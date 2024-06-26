import config 
from binance.client import Client
from binance.enums import *
import time
import vlc
import threading
import math
import csv
import itertools
import datetime
from scipy import stats
import numpy as np

client = Client(config.API_KEY, config.API_SECRET, tld='com')
symbolTicker = 'ETHBTC'
symbolPrice = 0
ma50 = 0
auxPrice = 0.0

def orderStatus(orderToCkeck):
    try:
        status = client.get_order(
            symbol = symbolTicker,
            orderId = orderToCkeck.get('orderId')
        )
        return status.get('status')
    except Exception as e:
        print(e)
        return 7

def _tendencia_ma50_4hs_15minCandles_():
    x = []
    y = []
    sum = 0
    ma50_i = 0

    time.sleep(1)

    resp = False

    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "18 hour ago UTC")

    if (len(klines) != 72):
        return False
    for i in range(56,72):
        for j in range(i-50,i):
            sum = sum + float(klines[j][4])
        ma50_i = round(sum / 50,6)
        sum = 0
        x.append(i)
        y.append(float(ma50_i))

    modelo = np.polyfit(x, y, 1)

    if (modelo[0]>0):
        resp = True

    return resp


def _ma50_():
    ma50_local = 0
    sum = 0

    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "24 hour ago UTC")

    if (len(klines) == 96):

        for i in range(10,96):
            sum = sum + float(klines[i][4])

        ma50_local = sum / 50

    return ma50_local

while 1:

    time.sleep(3)
    sum = 0

    try:
        list_of_tickers = client.get_all_tickers()
    except Exception as e:
        with open("ETHBTC_scalper.txt", "a") as myfile:
            myfile.write(str(datetime.datetime.now()) +" - ha ocurrido una excepción - {}".format(e)+ " Error 401 Opss ! \n")
        client = Client(config.API_KEY, config.API_SECRET, tld='com')
        continue

    for tick_2 in list_of_tickers:
        if tick_2['symbol'] == symbolTicker:
            symbolPrice = float(tick_2['price'])

    ma50 = _ma50_()
    if (ma50 == 0): continue

    print("########## " + symbolTicker + " ##########")
    print(" Media Actual: "  + str(round(ma50,6)))
    print(" Precio Actual: " + str(round(symbolPrice,6)))
    print(" Precio a Comprar: "  + str(round(ma50*0.99,6)))
    print("--------------------------")

    try:
        orders = client.get_open_orders(symbol=symbolTicker)
    except Exception as e:
        print(e)
        client = Client(config.API_KEY, config.API_SECRET, tld='com')
        continue

    if (len(orders) != 0):
        print("Hay ordenes abiertas")
        time.sleep(20)
        continue
    if (not _tendencia_ma50_4hs_15minCandles_()):
        print("Tendencia Bajista")
        time.sleep(20)
        continue
    else:
        print("Tendencia Alcista")

    if ( symbolPrice < ma50*0.99 ):
        print("COMPRA_DINÁMICA")

        try:

            buyOrder = client.create_order(
                        symbol=symbolTicker,
                        side='BUY',
                        type='STOP_LOSS_LIMIT',
                        quantity=0.12,
                        price=round(symbolPrice*1.0055,6),
                        stopPrice=round(symbolPrice*1.005,6),
                        timeInForce='GTC')

            auxPrice = symbolPrice
            time.sleep(3)
            while orderStatus(buyOrder)=='NEW':

                try:
                    list_of_tickers = client.get_all_tickers()
                except Exception as e:
                    with open("ETHBTC_scalper.txt", "a") as myfile:
                        myfile.write(str(datetime.datetime.now()) +" - ha ocurrido una excepción - {}".format(e)+ " Error 402 Opss ! \n")
                    client = Client(config.API_KEY, config.API_SECRET, tld='com')
                    continue

                for tick_2 in list_of_tickers:
                    if tick_2['symbol'] == symbolTicker:
                        symbolPrice = float(tick_2['price'])

                if (symbolPrice < auxPrice):

                    try:
                        result = client.cancel_order(
                            symbol=symbolTicker,
                            orderId=buyOrder.get('orderId'))

                        time.sleep(3)
                    except Exception as e:
                        with open("ETHBTC_scalper.txt", "a") as myfile:
                            myfile.write(str(datetime.datetime.now()) +" - ha ocurrido una excepción - {}".format(e)+ " Error 403 Opss ! \n")
                        break

                    buyOrder = client.create_order(
                                symbol=symbolTicker,
                                side='BUY',
                                type='STOP_LOSS_LIMIT',
                                quantity=0.12,
                                price=round(symbolPrice*1.0055,6),
                                stopPrice=round(symbolPrice*1.005,6),
                                timeInForce='GTC')
                    auxPrice = symbolPrice
                    time.sleep(1)

            time.sleep(10)

            orderOCO = client.order_oco_sell(
                        symbol = symbolTicker,
                        quantity = 0.12,
                        price = round(float(symbolPrice)*1.02,6),
                        stopPrice = round(float(symbolPrice)*0.992,6),
                        stopLimitPrice = round(float(symbolPrice)*0.99,6),
                        stopLimitTimeInForce = 'GTC'
                    )

            time.sleep(20)

        except Exception as e:
            with open("ETHBTC_scalper.txt", "a") as myfile:
                myfile.write(str(datetime.datetime.now()) +" - ha ocurrido una excepción - {}".format(e)+ " Error 404 Opss ! \n")
            client = Client(config.API_KEY, config.API_SECRET, tld='com')
            print(format(e))
            orders = client.get_open_orders(symbol=symbolTicker)
            if (len(orders)>0):
                result = client.cancel_order(
                    symbol=symbolTicker,
                    orderId=orders[0].get('orderId'))
            continue
