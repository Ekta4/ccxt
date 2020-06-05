'use strict';

const Exchange = require ('./base/Exchange');
const { InvalidOrder } = require ('./base/errors');

module.exports = class coineal extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'coineal',
            'name': 'Coineal',
            'countries': ['UK'],
            'rateLimit': 25000,
            'timeout': 40000,
            'has': {
                'fetchMarkets': true,  // Trading Pairs and Precision
                'fetchOHLCV': true,     // Get Market Chart Information
                'fetchOrderBook': true,  // Get Market Depth
                'fetchTrades': true,   // Get Market Trading Record
                'createOrder': true,    // Create Orders
                'cancelOrder': true,       // Cancel Limit Orders
                'fetchMyTrades': true,     // Account Transcation Records
                'fetchOpenOrders': true,    // Get Current Orders
                'fetchBalance': true,    // Account Balances
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
                    'get': [
                        '/open/api/all_trade',    // Account Transaction Records
                        '/open/api/new_order',    // Fetch Open Ordes
                        '/open/api/user/account',  // Fetch My balances
                    ],
                    'post': [
                        '/open/api/create_order',  // Create Order
                        '/open/api/cancel_order',  // Cancel Limit Orders
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
        if (api === 'private') {
            let content = '';
            query['api_key'] = 'apiKEy';    // Replace Api key with original API Key
            const sortedParams = this.keysort (query);  // Sort key wise as required for sign params
            const keys = Object.keys (sortedParams);
            for (let i = 0; i < keys.length; i++) {
                const key = keys[i];
                content += key + sortedParams[key].toString ();
            }
            const signature = content + 'secretKey';  // Replace secret Key with Original Secret Key
            const hash = this.hash (this.encode (signature), 'md5');
            query['sign'] = hash;
            if (method === 'GET') {
                if (Object.keys (query).length) {
                    // Api Key need to be binded
                    url += '?' + this.urlencode (query);
                }
            }
            if (method === 'POST') {
                body = this.json (query);
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                };
            }
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    updateSymbol (symbol) {
        const words = symbol.split ('/');
        const newSymbol = words.join ('');
        return newSymbol;
    }

    async fetchMarkets (params = {}) {
        const response = await this.publicGetOpenApiCommonSymbols (this.extend (params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": [
        //         {
        //             "symbol": "btcusdt",
        //             "count_coin": "usdt",
        //             "amount_precision": 5,
        //             "base_coin": "btc",
        //             "price_precision": 2
        //         }
        //     ]
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
                    'cost': {
                        'min': undefined,
                        'max': undefined,
                    },
                },
            };
            result.push (entry);
        }
        return result;
    }

    parseOHLCV (ohlcv, market = undefined, timeframe = '5m', since = undefined, limit = undefined) {
        return [
            ohlcv[0] * 1000,
            parseFloat (ohlcv[1]),
            parseFloat (ohlcv[3]),
            parseFloat (ohlcv[4]),
            parseFloat (ohlcv[2]),
            parseFloat (ohlcv[5]),
        ];
    }

    async fetchOHLCV (symbol = 'btcusdt', timeframe = 1, params = {}, since = undefined, limit = undefined) {
        await this.loadMarkets ();
        const market = this.market (symbol);
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'period': timeframe,
        };
        const response = await this.publicGetOpenApiGetRecords (this.extend (request, params));
        // Exchange response
        // {
        //     'code': '0',
        //     'msg': 'suc',
        //     'data': [
        //                 [
        //                     1529387760,  //Time Stamp
        //                     7585.41,  //Opening Price
        //                     7585.41,  //Highest Price
        //                     7585.41,  //Lowest Price
        //                     7585.41,  //Closing Price
        //                     0.0       //Transaction Volume
        //                 ]
        //             ]
        // }
        return this.parseOHLCVs (response['data'], market, timeframe, since, limit);
    }

    async fetchOrderBook (symbol = 'btcusdt', type = 'type0', params = {}) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'type': type,
        };
        const response = await this.publicGetOpenApiMarketDept (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": {
        //         "tick": {
        //             "time": 1529408112000,  //Refresh time of depth
        //             "asks": //Ask orders
        //             [
        //                 [
        //                     "6753.31", //Price of Ask 1
        //                     0.00306    //Order Size of Ask 1
        //                 ],
        //                 [
        //                     "6754.78", //Price of Ask 2
        //                     0.61112   //Order Size of Ask 2
        //                 ]
        //                 ...
        //             ],
        //             "bids": //Bid orders
        //             [
        //                 [
        //                     "6732.02",  //Price of Bid 1
        //                     0.18444     //Order Size of Bid 1
        //                 ],
        //                 [
        //                     "6730.08", //Price of Bid 2
        //                     0.14662    //Order Size of Bid 2
        //                 ]
        //                 ...
        //             ]
        //         }
        return this.parseOrderBook (response['data']['tick'], response['data']['tick']['time']);
    }

    parseTrade (trade, market = undefined) {
        const timestamp = this.parse8601 (this.safeString (trade, 'trade_time'));
        const price = this.safeFloat (trade, 'price');
        const amount = this.safeFloat (trade, 'amount');
        const symbol = market['symbol'];
        let cost = undefined;
        if (price !== undefined) {
            if (amount !== undefined) {
                cost = parseFloat (this.costToPrecision (symbol, price * amount));
            }
        }
        const tradeId = this.safeString (trade, 'id');
        const side = this.safeString (trade, 'type');
        return {
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
    }

    async fetchTrades (symbol = 'btcusdt', params = {}, since = undefined, limit = undefined) {
        await this.loadMarkets ();
        const market = this.market (symbol);
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
        };
        const response = await this.publicGetOpenApiGetTrades (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": [
        //         {
        //             "amount": 0.99583,
        //             "trade_time": 1529408112000,
        //             "price": 6763.9,
        //             "id": 280101,
        //             "type": "sell"
        //         }
        //     ]
        // }
        return this.parseTrades (response['data'], market, since, limit);
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = undefined) {
        await this.loadMarkets ();
        let updatePrice = price;
        if (type === 2) {
            updatePrice = this.priceToPrecision (symbol, price);
        }
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'time': this.ymdhms (this.milliseconds ()),
            'symbol': updatedSymbol.toLowerCase (),
            'side': side,
            'type': type,
            'price': updatePrice,
            'volume': amount,
            // 'sign': ,
            // remaining Needs to be completed and API key should be binded Run time
        };
        const respose = await this.privatePostOpenApiCreateOrder (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": {
        //         "order_id": 34343
        //     }
        // }
        if (respose['msg'] !== 'suc') {
            throw new InvalidOrder (respose['msg'] + ' order was rejected by the exchange ' + this.json (respose));
        }
        return respose;
    }

    async cancelOrder (id, symbol = 'btcusdt', params = {}) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'order_id': id,
            'time': this.ymdhms (this.milliseconds ()),
            // 'sign': '',
            // Sign need to be filled and API KEY
        };
        const response = await this.privatePostOpenApiCancelOrder (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": {}
        // }
        return response;
    }

    async fetchMyTrades (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'time': this.ymdhms (this.milliseconds ()),
            'page': '',
            'pageSize': '',
            'sign': '',
            // Api key Need to be binded
        };
        const response = await this.privateGetOpenApiAllTrade (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": {
        //         "count": 22,
        //         "resultList": [
        //             {
        //                 "volume": "1.000",
        //                 "side": "BUY",
        //                 "price": "0.10000000",
        //                 "fee": "0.16431104",
        //                 "ctime": 1510996571195,
        //                 "deal_price": "0.10000000",
        //                 "id": 306,
        //                 "type": "买入"
        //             }
        //         ]
        //     }
        // }
        return response;
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        const updatedSymbol = this.updateSymbol (symbol);
        const request = {
            'symbol': updatedSymbol.toLowerCase (),
            'time': this.ymdhms (this.milliseconds ()),
            'page': '',
            'pageSize': '',
            'sign': '',
            // Api key Need to be binded
        };
        const response = await this.privateGetOpenApiNewOrder (this.extend (request, params));
        // Exchange response
        // {
        //     "code": "0",
        //     "msg": "suc",
        //     "data": {
        //         "count": 10,
        //         "resultList": [
        //             {
        //                 "side": "BUY",
        //                 "total_price": "0.10000000",
        //                 "created_at": 1510993841000,
        //                 "avg_price": "0.10000000",
        //                 "countCoin": "btc",
        //                 "source": 1,
        //                 "type": 1,
        //                 "side_msg": "买入",
        //                 "volume": "1.000",
        //                 "price": "0.10000000",
        //                 "source_msg": "WEB",
        //                 "status_msg": "部分成交",
        //                 "deal_volume": "0.50000000",
        //                 "id": 424,
        //                 "remain_volume": "0.00000000",
        //                 "baseCoin": "eth",
        //                 "tradeList": [
        //                     {
        //                         "volume": "0.500",
        //                         "price": "0.10000000",
        //                         "fee": "0.16431104",
        //                         "ctime": 1510996571195,
        //                         "deal_price": "0.10000000",
        //                         "id": 306,
        //                         "type": "买入"
        //                     }
        //                 ],
        //                 "status": 3
        //             },
        //             {
        //                 "side": "SELL",
        //                 "total_price": "0.10000000",
        //                 "created_at": 1510993841000,
        //                 "avg_price": "0.10000000",
        //                 "countCoin": "btc",
        //                 "source": 1,
        //                 "type": 1,
        //                 "side_msg": "买入",
        //                 "volume": "1.000",
        //                 "price": "0.10000000",
        //                 "source_msg": "WEB",
        //                 "status_msg": "未成交",
        //                 "deal_volume": "0.00000000",
        //                 "id": 425,
        //                 "remain_volume": "0.00000000",
        //                 "baseCoin": "eth",
        //                 "tradeList": [],
        //                 "status": 1
        //             }
        //         ]
        //     }
        // }
        return response;
    }
};
