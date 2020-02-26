# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange
import base64
import hashlib


class btcchina(Exchange):

    def describe(self):
        return self.deep_extend(super(btcchina, self).describe(), {
            'id': 'btcchina',
            'name': 'BTCChina',
            'countries': ['CN'],
            'rateLimit': 1500,
            'version': 'v1',
            'has': {
                'CORS': False,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766368-465b3286-5ed6-11e7-9a11-0f6467e1d82b.jpg',
                'api': {
                    'plus': 'https://plus-api.btcchina.com/market',
                    'public': 'https://data.btcchina.com/data',
                    'private': 'https://api.btcchina.com/api_trade_v1.php',
                },
                'www': 'https://www.btcchina.com',
                'doc': 'https://www.btcchina.com/apidocs',
            },
            'api': {
                'plus': {
                    'get': [
                        'orderbook',
                        'ticker',
                        'trade',
                    ],
                },
                'public': {
                    'get': [
                        'historydata',
                        'orderbook',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'BuyIcebergOrder',
                        'BuyOrder',
                        'BuyOrder2',
                        'BuyStopOrder',
                        'CancelIcebergOrder',
                        'CancelOrder',
                        'CancelStopOrder',
                        'GetAccountInfo',
                        'getArchivedOrder',
                        'getArchivedOrders',
                        'GetDeposits',
                        'GetIcebergOrder',
                        'GetIcebergOrders',
                        'GetMarketDepth',
                        'GetMarketDepth2',
                        'GetOrder',
                        'GetOrders',
                        'GetStopOrder',
                        'GetStopOrders',
                        'GetTransactions',
                        'GetWithdrawal',
                        'GetWithdrawals',
                        'RequestWithdrawal',
                        'SellIcebergOrder',
                        'SellOrder',
                        'SellOrder2',
                        'SellStopOrder',
                    ],
                },
            },
            'markets': {
                'BTC/CNY': {'id': 'btccny', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY', 'api': 'public', 'plus': False},
                'LTC/CNY': {'id': 'ltccny', 'symbol': 'LTC/CNY', 'base': 'LTC', 'quote': 'CNY', 'api': 'public', 'plus': False},
                'LTC/BTC': {'id': 'ltcbtc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'api': 'public', 'plus': False},
                'BCH/CNY': {'id': 'bcccny', 'symbol': 'BCH/CNY', 'base': 'BCH', 'quote': 'CNY', 'api': 'plus', 'plus': True},
                'ETH/CNY': {'id': 'ethcny', 'symbol': 'ETH/CNY', 'base': 'ETH', 'quote': 'CNY', 'api': 'plus', 'plus': True},
            },
        })

    def fetch_markets(self, params={}):
        request = {
            'market': 'all',
        }
        markets = self.publicGetTicker(self.extend(request, params))
        result = []
        keys = list(markets.keys())
        for i in range(0, len(keys)):
            key = keys[i]
            market = markets[key]
            parts = key.split('_')
            id = parts[1]
            baseId = id[0:3]
            quoteId = id[3:6]
            base = baseId.upper()
            quote = quoteId.upper()
            base = self.safe_currency_code(base)
            quote = self.safe_currency_code(quote)
            symbol = base + '/' + quote
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'info': market,
            })
        return result

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privatePostGetAccountInfo(params)
        balances = self.safe_value(response, 'result')
        result = {'info': balances}
        codes = list(self.currencies.keys())
        for i in range(0, len(codes)):
            code = codes[i]
            currency = self.currency(code)
            account = self.account()
            currencyId = currency['id']
            if currencyId in balances['balance']:
                account['total'] = float(balances['balance'][currencyId]['amount'])
            if currencyId in balances['frozen']:
                account['used'] = float(balances['frozen'][currencyId]['amount'])
            result[code] = account
        return self.parse_balance(result)

    def create_market_request(self, market):
        request = {}
        field = 'symbol' if (market['plus']) else 'market'
        request[field] = market['id']
        return request

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        method = market['api'] + 'GetOrderbook'
        request = self.create_market_request(market)
        response = getattr(self, method)(self.extend(request, params))
        timestamp = self.safe_timestamp(response, 'date')
        return self.parse_order_book(response, timestamp)

    def parse_ticker(self, ticker, market):
        timestamp = self.safe_timestamp(ticker, 'date')
        last = self.safe_float(ticker, 'last')
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'buy'),
            'ask': self.safe_float(ticker, 'sell'),
            'vwap': self.safe_float(ticker, 'vwap'),
            'open': self.safe_float(ticker, 'open'),
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': self.safe_float(ticker, 'vol'),
            'quoteVolume': None,
            'info': ticker,
        }

    def parse_ticker_plus(self, ticker, market):
        timestamp = self.safe_integer(ticker, 'Timestamp')
        symbol = None
        if market is not None:
            symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'High'),
            'low': self.safe_float(ticker, 'Low'),
            'bid': self.safe_float(ticker, 'BidPrice'),
            'ask': self.safe_float(ticker, 'AskPrice'),
            'vwap': None,
            'open': self.safe_float(ticker, 'Open'),
            'last': self.safe_float(ticker, 'Last'),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': self.safe_float(ticker, 'Volume24H'),
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        method = market['api'] + 'GetTicker'
        request = self.create_market_request(market)
        response = getattr(self, method)(self.extend(request, params))
        ticker = self.safe_value(response, 'ticker')
        if market['plus']:
            return self.parse_ticker_plus(ticker, market)
        return self.parse_ticker(ticker, market)

    def parse_trade(self, trade, market):
        timestamp = self.safe_timestamp(trade, 'date')
        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'amount')
        cost = None
        if amount is not None:
            if price is not None:
                cost = amount * price
        id = self.safe_string(trade, 'tid')
        return {
            'id': id,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': None,
            'price': price,
            'amount': amount,
            'cost': cost,
        }

    def parse_trade_plus(self, trade, market):
        timestamp = self.parse8601(self.safe_string(trade, 'timestamp'))
        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'size')
        cost = None
        if amount is not None:
            if price is not None:
                cost = amount * price
        side = self.safe_string_lower(trade, 'side')
        return {
            'id': None,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost,
        }

    def parse_trades_plus(self, trades, market=None):
        result = []
        for i in range(0, len(trades)):
            result.append(self.parse_trade_plus(trades[i], market))
        return result

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        method = market['api'] + 'GetTrade'
        request = self.create_market_request(market)
        if market['plus']:
            now = self.milliseconds()
            request['start_time'] = now - 86400000
            request['end_time'] = now
        else:
            method += 's'  # trades vs trade
        response = getattr(self, method)(self.extend(request, params))
        if market['plus']:
            return self.parse_trades_plus(response['trades'], market)
        return self.parse_trades(response, market, since, limit)

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        method = 'privatePost' + self.capitalize(side) + 'Order2'
        request = {}
        id = market['id'].upper()
        if type == 'market':
            request['params'] = [None, amount, id]
        else:
            request['params'] = [price, amount, id]
        response = getattr(self, method)(self.extend(request, params))
        orderId = self.safe_string(response, 'id')
        return {
            'info': response,
            'id': orderId,
        }

    def cancel_order(self, id, symbol=None, params={}):
        self.load_markets()
        market = params['market']  # TODO fixme
        request = {
            'params': [id, market],
        }
        return self.privatePostCancelOrder(self.extend(request, params))

    def nonce(self):
        return self.microseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'][api] + '/' + path
        if api == 'private':
            self.check_required_credentials()
            p = []
            if 'params' in params:
                p = params['params']
            nonce = self.nonce()
            request = {
                'method': path,
                'id': nonce,
                'params': p,
            }
            p = ','.join(p)
            body = self.json(request)
            query = '&'.join([
                'tonce=' + nonce,
                'accesskey=' + self.apiKey,
                'requestmethod=' + method.lower(),
                'id=' + nonce,
                'method=' + path,
                'params=' + p,
            ])
            signature = self.hmac(self.encode(query), self.encode(self.secret), hashlib.sha1)
            auth = self.encode(self.apiKey + ':' + signature)
            headers = {
                'Authorization': 'Basic ' + base64.b64encode(auth),
                'Json-Rpc-Tonce': nonce,
            }
        else:
            if params:
                url += '?' + self.urlencode(params)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
