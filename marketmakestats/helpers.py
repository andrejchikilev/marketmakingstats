#!/usr/bin/python

import argparse
import urllib.request
import json
import datetime
from functools import reduce


URL_LISTINGS = 'https://api.coinmarketcap.com/v2/listings/'
URL_CONVERT = 'https://api.coinmarketcap.com/v2/ticker/?convert={symbol}'
URL_GRAPH = 'https://graphs2.coinmarketcap.com/currencies/{slug}/{start_time}/{now_time}'
PERIOD_WITH_HOURLY_CHUNK = 89


def createParser():
    parser = argparse.ArgumentParser(description='Example: marketmakingstats.py BTC/ETH 2 5 20')
    parser.add_argument('market', help='e.c. BTC/ETH')
    parser.add_argument('delta_time', help='in hours')
    parser.add_argument('ratio', help='in percents')
    parser.add_argument('period', help='in days')
    return parser


def getRate(fcur, tcur):
    with urllib.request.urlopen(URL_CONVERT.format(symbol=tcur.get('symbol'))) as request:
        return json.loads(request.read().decode('UTF-8')).get('data').get(str(fcur['id'])).get('quotes')[tcur['symbol']]['price']


def getCurrencies(fsym, tsym):
    with urllib.request.urlopen(URL_LISTINGS) as request:
        curr_list = json.loads(request.read().decode('UTF-8')).get('data')
    curr_dict = {currency['symbol']: {'symbol':currency['symbol'], 'id':currency['id'], 'website_slug': currency['website_slug']} for currency in curr_list}
    fcur = curr_dict.get(fsym)
    tcur = curr_dict.get(tsym)
    return fcur, tcur


def getData(fcur, tcur, delta_time, start_day, current_time=None):
    if not current_time:
        current_time = datetime.datetime.now()
    current_timestamp = current_time.timestamp()
    if current_time - start_day <= datetime.timedelta(days=PERIOD_WITH_HOURLY_CHUNK):
        with urllib.request.urlopen(URL_GRAPH.format(slug=fcur['website_slug'], start_time=round(start_day.timestamp())*1000, now_time=round(current_timestamp)*1000)) as request:
            fprice_btc = json.loads(request.read().decode('UTF-8')).get('price_btc')
        with urllib.request.urlopen(URL_GRAPH.format(slug=tcur['website_slug'], start_time=round(start_day.timestamp())*1000, now_time=round(current_timestamp)*1000)) as request:
            tprice_btc = json.loads(request.read().decode('UTF-8')).get('price_btc')
        data = list(map(lambda x,y: x[1]/y[1], fprice_btc, tprice_btc))
        entry_delta = datetime.datetime.fromtimestamp(fprice_btc[1][0]/1000) - datetime.datetime.fromtimestamp(fprice_btc[0][0]/1000)
        return [data[i] for i in range(0, len(data)-1 , (datetime.timedelta(hours=delta_time)//entry_delta))]
    else:
        chunk_dates = [start_day]
        for i in range((current_time - start_day)//datetime.timedelta(days=PERIOD_WITH_HOURLY_CHUNK)):
            chunk_dates.append(chunk_dates[i] + datetime.timedelta(days=PERIOD_WITH_HOURLY_CHUNK))
        if chunk_dates[len(chunk_dates)-1] != current_time:
            chunk_dates.append(current_time)
        data = []
        for i in range(len(chunk_dates)-1):
            data.extend(getData(fcur, tcur, delta_time, chunk_dates[i], chunk_dates[i+1]))
        return data


def makeMarketStats(market, interval, percent, period):
    ratio = percent / 100
    start_day = datetime.datetime.now() - datetime.timedelta(days=period)

    fsym, tsym = market.split('/')
    fcur, tcur = getCurrencies(fsym, tsym)
    current_rate = getRate(fcur, tcur)

    data = getData(fcur, tcur, interval, start_day)

    rates = [current_rate]
    while rates[len(rates)-1] + current_rate * ratio < max(data):
        rates.append(rates[len(rates)-1] + current_rate * ratio)
    rates.append(max(data))

    while rates[0] - current_rate * ratio > min(data):
        rates.insert(0, rates[0] - current_rate * ratio)
    if min(data) < current_rate:
        rates.insert(0, min(data))

    returned_trades = []
    for i in range(len(rates)-1):
        counter = 0
        k = 0
        t = 0
        while k < len(data):
            if rates[i] <= data[k] <= rates[i+1]:
                t += 1
                k += 1
                continue
            if t:
                counter += 1
                t = 0
            else:
                k += 1
        else:
            if t:
                counter += 1
        returned_trades.append(counter)
    return reduce(lambda x,y: x + y, returned_trades)

if __name__ == '__main__':
    parser = createParser()
    args = parser.parse_args()
    market = args.market
    interval = int(args.delta_time)
    percent = int(args.ratio)
    period = int(args.period)

    returned_trades = makeMarketStats(market, interval, percent, period)

    print(returned_trades)
