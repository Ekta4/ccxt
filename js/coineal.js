'use strict';

const Exchange = require ('./base/Exchange');

module.exports = class coineal extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'coineal',
            'name': 'Coineal',
            'countries': [],
            'rateLimit': 25000,
            'timeout': 40000,
            'has': {
                // Trading Pairs and Precision
                'fetchMarkets': true,
                // Get Market Chart Information
                'fetchOHLCV': true,
                // Get Market Depth
                'fetchOrderBook': true,
                // Get Market Trading Record
                'fetchTrades': true,
                // Create Orders
                'createOrder': true,
            },
            'urls': {
                'api': {
                    'public': 'https://exchange-open-api.coineal.com',
                    'private': 'https://exchange-open-api.coineal.com',
                },
                'www': 'https://exchange-open-api.coineal.com',
            },
            'api': {
                'public': {
                    'get': [
                        // 'open/api/get_ticker',
                        'open/api/common/symbols',
                        'open/api/get_records',
                        'open/api/market_dept',
                        '/open/api/get_trades',
                    ],
                },
                'private': {
                    'post': [
                        '/open/api/create_order',
                    ],
                },
            },
        });
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let url = this.urls['api'][api];
        url += '/' + path;
        const query = this.omit (params, this.extractParams (path));
        if (api === 'public') {
            // Case When Public method and has QueryParams
            if (Object.keys (query).length) {
                url += '?' + this.urlencode (query);
            }
        }
        // if (api === 'private') {
        //     if (method === 'post') {
        //         // dfghjk
        //     }
        // }
        // eslint-disable-next-line no-console
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    updateSymbol (symbol) {
        const words = symbol.split ('/');
        const newSymbol = words.join ('');
        return newSymbol;
    }

    async fetchMarkets (params = {}) {
        const response = await this.publicGetOpenApiCommonSymbols (params);
        // Response Format
        // {
        //     "code":"0",
        //     "msg":"suc",
        //     "data":[{"symbol":"btcusdt","count_coin":"usdt","amount_precision":5,"base_coin":"btc","price_precision":2},
        //              {"symbol":"ethbtc","count_coin":"btc","amount_precision":4,"base_coin":"eth","price_precision":5},
        //              {"symbol":"eoseth","count_coin":"eth","amount_precision":2,"base_coin":"eos","price_precision":6},
        //              {"symbol":"ethusdt","count_coin":"usdt","amount_precision":4,"base_coin":"eth","price_precision":2}]
        // }
        const result = [];
        const markets = this.safeValue (response, 'data');
        for (let i = 0; i < markets.length; i++) {
            const market = markets[i];
            const id = this.safeString (market, 'symbol');
            const baseId = market['base_coin'];
            const quoteId = market['count_coin'];
            const base = this.safeCurrencyCode (baseId);
            const quote = this.safeCurrencyCode (quoteId);
            const symbol = base + '/' + quote;
            const precision = {
                'base': market['amount_precision'],
                'quote': market['price_precision'],
                'amount': market['amount_precision'],
                'price': market['price_precision'],
            };
            const active = 'true'; // Assuemed If true than only query will return result
            const entry = {
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'info': market,
                'active': active,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': Math.pow (10, -precision['amount']),
                        'max': undefined,
                    },
                    'price': {
                        'min': undefined,
                        'max': undefined,
                    },
                },
            };
            result.push (entry);
        }
        return result;
    }

    async fetchOHLCV (symbol = 'btcusdt', timeframe = 1, params = {}, since = undefined, limit = undefined) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'period': timeframe,
        };
        const method = 'publicGetOpenApiGetRecords';
        const response = await this[method] (this.extend (request, params));
        // const ohlcvs = Object.values (response['data'] || []);              //Need to check Real Code Uses Object Values method
        const ohlcvs = this.safeValue (response, 'data');
        const result = [];
        for (let i = 0; i < ohlcvs.length; i++) {
            if (limit && (result.length >= limit)) {
                break;
            }
            const ohlcv = this.parseOHLCV (ohlcvs[i], undefined, timeframe, since, limit);
            if (since && (ohlcv[0] < since)) {
                continue;
            }
            result.push (ohlcv);
        }
        return this.sortBy (result, 0);
    }

    async fetchOrderBook (symbol = 'btcusdt', type = 'type0', params = {}) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'type': type,
        };
        const method = 'publicGetOpenApiMarketDept';
        const response = await this[method] (this.extend (request, params));
        const result = {
            'bids': [],
            'asks': [],
            'timestamp': '',
            'nonce': undefined,
            'datetime': '',
        };
        const data = this.safeValue (response, 'data');
        const asks = this.safeValue (data['tick'], 'asks');
        const bids = this.safeValue (data['tick'], 'bids');
        const timestamp = this.safeValue (data['tick'], 'time');
        result['bids'] = this.sortBy (bids, 0, true);
        result['asks'] = this.sortBy (asks, 0);
        result['timestamp'] = timestamp;
        result['datetime'] = this.iso8601 (timestamp);
        return result;
    }

    async fetchTrades (symbol = 'btcusdt', params = {}, since = undefined, limit = undefined) {
        await this.loadMarkets ();
        const market = this.market (symbol);
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
        };
        const method = 'publicGetOpenApiGetTrades';
        const response = await this[method] (this.extend (request, params));
        let result = [];
        const traders = this.safeValue (response, 'data');
        for (let i = 0; i < traders.length; i++) {
            const trade = traders[i];
            const price = this.safeFloat (trade, 'price');
            const amount = this.safeFloat (trade, 'amount');
            // const symboll = symbol;
            const timestamp = this.safeString (trade, 'trade_time');
            const side = this.safeString (trade, 'type');
            const tradeId = this.safeString (trade, 'id');
            let cost = undefined;
            // Cost Logic Below Which is Not working as of CosttoPrecision function now finds symbol
            if (price !== undefined) {
                if (amount !== undefined) {
                    cost = parseFloat (this.costToPrecision (symbol, price * amount));
                }
            }
            const entry = {
                'info': trade,
                'timestamp': timestamp,
                'datetime': this.iso8601 (timestamp),
                'symbol': symbol,
                'id': tradeId,
                'order': undefined,
                'type': undefined,
                'side': side,
                'takerOrMaker': undefined,
                'price': price,
                'amount': amount,
                'cost': cost,
                'fee': undefined,
            };
            result.push (entry);
        }
        result = this.sortBy (result, 'timestamp');
        // Need to update Once Market is updated
        const symbo = (market !== undefined) ? market['symbol'] : undefined;
        return this.filterBySymbolSinceLimit (result, symbo, since, limit);
    }
};
