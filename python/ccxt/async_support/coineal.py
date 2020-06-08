# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange
import math
from ccxt.base.errors import InvalidOrder


class coineal(Exchange):

    def describe(self):
        return self.deep_extend(super(coineal, self).describe(), {
            'id': 'coineal',
            'name': 'Coineal',
            'countries': ['UK'],
            'rateLimit': 25000,
            'timeout': 40000,
            'has': {
                'fetchMarkets': True,  # Trading Pairs and Precision
                'fetchOHLCV': True,     # Get Market Chart Information
                'fetchOrderBook': True,  # Get Market Depth
                'fetchTrades': True,   # Get Market Trading Record
                'createOrder': True,    # Create Orders
                'cancelOrder': True,       # Cancel Limit Orders
                'fetchMyTrades': True,     # Account Transcation Records
                'fetchOpenOrders': True,    # Get Current Orders
                'fetchBalance': True,    # Account Balances
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
                        # 'open/api/get_ticker',
                        'open/api/common/symbols',
                        'open/api/get_records',
                        'open/api/market_dept',
                        '/open/api/get_trades',
                    ],
                },
                'private': {
                    'get': [
                        '/open/api/all_trade',    # Account Transaction Records
                        '/open/api/new_order',    # Fetch Open Ordes
                        '/open/api/user/account',  # Fetch My balances
                    ],
                    'post': [
                        '/open/api/create_order',  # Create Order
                        '/open/api/cancel_order',  # Cancel Limit Orders
                    ],
                },
            },
        })

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'][api]
        url += '/' + path
        query = self.omit(params, self.extract_params(path))
        if api == 'public':
            # Case When Public method and has QueryParams
            if query:
                url += '?' + self.urlencode(query)
        if api == 'private':
            content = ''
            query['api_key'] = 'apiKEy'    # Replace Api key with original API Key
            sortedParams = self.keysort(query)  # Sort key wise as required for sign params
            keys = list(sortedParams.keys())
            for i in range(0, len(keys)):
                key = keys[i]
                content += key + str(sortedParams[key])
            signature = content + 'secretKey'  # Replace secret Key with Original Secret Key
            hash = self.hash(self.encode(signature), 'md5')
            query['sign'] = hash
            if method == 'GET':
                if query:
                    # Api Key need to be binded
                    url += '?' + self.urlencode(query)
            if method == 'POST':
                body = self.json(query)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def update_symbol(self, symbol):
        words = symbol.split('/')
        newSymbol = ''.join(words)
        return newSymbol

    async def fetch_markets(self, params={}):
        response = await self.publicGetOpenApiCommonSymbols(self.extend(params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": [
        #         {
        #             "symbol": "btcusdt",
        #             "count_coin": "usdt",
        #             "amount_precision": 5,
        #             "base_coin": "btc",
        #             "price_precision": 2
        #         }
        #     ]
        # }
        result = []
        markets = self.safe_value(response, 'data')
        for i in range(0, len(markets)):
            market = markets[i]
            id = self.safe_string(market, 'symbol')
            baseId = market['base_coin']
            quoteId = market['count_coin']
            base = self.safe_currency_code(baseId)
            quote = self.safe_currency_code(quoteId)
            symbol = base + '/' + quote
            precision = {
                'base': market['amount_precision'],
                'quote': market['price_precision'],
                'amount': market['amount_precision'],
                'price': market['price_precision'],
            }
            active = 'true'  # Assuemed If True than only query will return result
            entry = {
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
                        'min': math.pow(10, -precision['amount']),
                        'max': None,
                    },
                    'price': {
                        'min': None,
                        'max': None,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
            }
            result.append(entry)
        return result

    def parse_ohlcv(self, ohlcv, market=None, timeframe='5m', since=None, limit=None):
        return [
            ohlcv[0] * 1000,
            float(ohlcv[1]),
            float(ohlcv[3]),
            float(ohlcv[4]),
            float(ohlcv[2]),
            float(ohlcv[5]),
        ]

    async def fetch_ohlcv(self, symbol='btcusdt', timeframe=1, params={}, since=None, limit=None):
        await self.load_markets()
        market = self.market(symbol)
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
            'period': timeframe,
        }
        response = await self.publicGetOpenApiGetRecords(self.extend(request, params))
        # Exchange response
        # {
        #     'code': '0',
        #     'msg': 'suc',
        #     'data': [
        #                 [
        #                     1529387760,  #Time Stamp
        #                     7585.41,  #Opening Price
        #                     7585.41,  #Highest Price
        #                     7585.41,  #Lowest Price
        #                     7585.41,  #Closing Price
        #                     0.0       #Transaction Volume
        #                 ]
        #             ]
        # }
        return self.parse_ohlcvs(response['data'], market, timeframe, since, limit)

    async def fetch_order_book(self, symbol='btcusdt', type='type0', params={}):
        await self.load_markets()
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
            'type': type,
        }
        response = await self.publicGetOpenApiMarketDept(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": {
        #         "tick": {
        #             "time": 1529408112000,  #Refresh time of depth
        #             "asks":  #Ask orders
        #             [
        #                 [
        #                     "6753.31",  #Price of Ask 1
        #                     0.00306    #Order Size of Ask 1
        #                 ],
        #                 [
        #                     "6754.78",  #Price of Ask 2
        #                     0.61112   #Order Size of Ask 2
        #                 ]
        #                 ...
        #             ],
        #             "bids":  #Bid orders
        #             [
        #                 [
        #                     "6732.02",  #Price of Bid 1
        #                     0.18444     #Order Size of Bid 1
        #                 ],
        #                 [
        #                     "6730.08",  #Price of Bid 2
        #                     0.14662    #Order Size of Bid 2
        #                 ]
        #                 ...
        #             ]
        #         }
        return self.parse_order_book(response['data']['tick'], response['data']['tick']['time'])

    def parse_trade(self, trade, market=None):
        timestamp = self.parse8601(self.safe_string(trade, 'trade_time'))
        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'amount')
        symbol = market['symbol']
        cost = None
        if price is not None:
            if amount is not None:
                cost = float(self.cost_to_precision(symbol, price * amount))
        tradeId = self.safe_string(trade, 'id')
        side = self.safe_string(trade, 'type')
        return {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': tradeId,
            'order': None,
            'type': None,
            'side': side,
            'takerOrMaker': None,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
        }

    async def fetch_trades(self, symbol='btcusdt', params={}, since=None, limit=None):
        await self.load_markets()
        market = self.market(symbol)
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
        }
        response = await self.publicGetOpenApiGetTrades(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": [
        #         {
        #             "amount": 0.99583,
        #             "trade_time": 1529408112000,
        #             "price": 6763.9,
        #             "id": 280101,
        #             "type": "sell"
        #         }
        #     ]
        # }
        return self.parse_trades(response['data'], market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params=None):
        await self.load_markets()
        updatePrice = price
        if type == 2:
            updatePrice = self.price_to_precision(symbol, price)
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'time': self.ymdhms(self.milliseconds()),
            'symbol': updatedSymbol.lower(),
            'side': side,
            'type': type,
            'price': updatePrice,
            'volume': amount,
            # 'sign': ,
            # remaining Needs to be completed and API key should be binded Run time
        }
        respose = await self.privatePostOpenApiCreateOrder(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": {
        #         "order_id": 34343
        #     }
        # }
        if respose['msg'] != 'suc':
            raise InvalidOrder(respose['msg'] + ' order was rejected by the exchange ' + self.json(respose))
        return respose

    async def cancel_order(self, id, symbol='btcusdt', params={}):
        await self.load_markets()
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
            'order_id': id,
            'time': self.ymdhms(self.milliseconds()),
            # 'sign': '',
            # Sign need to be filled and API KEY
        }
        response = await self.privatePostOpenApiCancelOrder(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": {}
        # }
        return response

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
            'time': self.ymdhms(self.milliseconds()),
            'page': '',
            'pageSize': '',
            'sign': '',
            # Api key Need to be binded
        }
        response = await self.privateGetOpenApiAllTrade(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": {
        #         "count": 22,
        #         "resultList": [
        #             {
        #                 "volume": "1.000",
        #                 "side": "BUY",
        #                 "price": "0.10000000",
        #                 "fee": "0.16431104",
        #                 "ctime": 1510996571195,
        #                 "deal_price": "0.10000000",
        #                 "id": 306,
        #                 "type": "买入"
        #             }
        #         ]
        #     }
        # }
        return response

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        updatedSymbol = self.update_symbol(symbol)
        request = {
            'symbol': updatedSymbol.lower(),
            'time': self.ymdhms(self.milliseconds()),
            'page': '',
            'pageSize': '',
            'sign': '',
            # Api key Need to be binded
        }
        response = await self.privateGetOpenApiNewOrder(self.extend(request, params))
        # Exchange response
        # {
        #     "code": "0",
        #     "msg": "suc",
        #     "data": {
        #         "count": 10,
        #         "resultList": [
        #             {
        #                 "side": "BUY",
        #                 "total_price": "0.10000000",
        #                 "created_at": 1510993841000,
        #                 "avg_price": "0.10000000",
        #                 "countCoin": "btc",
        #                 "source": 1,
        #                 "type": 1,
        #                 "side_msg": "买入",
        #                 "volume": "1.000",
        #                 "price": "0.10000000",
        #                 "source_msg": "WEB",
        #                 "status_msg": "部分成交",
        #                 "deal_volume": "0.50000000",
        #                 "id": 424,
        #                 "remain_volume": "0.00000000",
        #                 "baseCoin": "eth",
        #                 "tradeList": [
        #                     {
        #                         "volume": "0.500",
        #                         "price": "0.10000000",
        #                         "fee": "0.16431104",
        #                         "ctime": 1510996571195,
        #                         "deal_price": "0.10000000",
        #                         "id": 306,
        #                         "type": "买入"
        #                     }
        #                 ],
        #                 "status": 3
        #             },
        #             {
        #                 "side": "SELL",
        #                 "total_price": "0.10000000",
        #                 "created_at": 1510993841000,
        #                 "avg_price": "0.10000000",
        #                 "countCoin": "btc",
        #                 "source": 1,
        #                 "type": 1,
        #                 "side_msg": "买入",
        #                 "volume": "1.000",
        #                 "price": "0.10000000",
        #                 "source_msg": "WEB",
        #                 "status_msg": "未成交",
        #                 "deal_volume": "0.00000000",
        #                 "id": 425,
        #                 "remain_volume": "0.00000000",
        #                 "baseCoin": "eth",
        #                 "tradeList": [],
        #                 "status": 1
        #             }
        #         ]
        #     }
        # }
        return response
