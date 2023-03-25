#!/usr/bin/env python3

import requests
import json
import time
import numpy as np
from sklearn.linear_model import LinearRegression
import csv
import os
#import mbtapi

def get_ticker_price():
    price = requests.get('https://www.mercadobitcoin.net/api/BTC/ticker/')
    price = json.loads(price.text)
    return float(price['ticker']['last'])

def extract(trades, a_key):
    extract = []
    for trade in trades:
        extract.append(trade[a_key])
    return extract

def get_trades(seconds):
    time_now = int(time.time())
    time_then = time_now - seconds
    trades = requests.get('https://www.mercadobitcoin.net/api/BTC/trades/{0}/{1}'.format(time_then, time_now))
    return trades.json()
'''
def generate_order(order):
    params = order.generate_params()
    tapi_mac = order.generate_mac(params)
    headers = order.generate_headers(tapi_mac)
    order.generate_post(params, headers)
'''
# Initializing wallet
if os.path.isfile('run-test-stoploss-2.csv'):
    # Read from csv
    with open('run-test-stoploss-2.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            last_row = row
        walletbtc = float(last_row[4])
        walletbrl = float(last_row[5])

    with open('buylist-stoploss-2.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        buy_list = [float(row[0]) for row in csvreader]
else:
    walletbtc = 0
    walletbrl = 1000
    buy_list = []

quantity = 0.0001
margin = 1.025
stop_loss = 0.95

while True:
    # Get the historical data
    trades = get_trades(600)
    timestamps = extract(trades, 'date')
    prices = extract(trades, 'price')

    # Perform linear regression on the prices
    x = np.array(timestamps).reshape(-1, 1)
    y = np.array(prices).reshape(-1, 1)
    reg = LinearRegression().fit(x, y)

    # Initializing regression
    reg_value = float("%.6f" % float(reg.predict(np.array([[timestamps[-1]]]))[0][0]))

    # Get the current price
    current_price = float("%.6f" % get_ticker_price())

    # Saving current wallet
    tmp_brl = walletbrl
    tmp_btc = round(walletbtc, 4)

    # Buy/Sell/Hold condition
    # First Sell condition
    if len(buy_list) > 0 and current_price < max(buy_list) * stop_loss:
        trade_type = 'sell'

        # Doing accounting
        walletbrl += (quantity * current_price)
        walletbtc -= round(quantity, 4)

        # Reversing order if there are no BTC in wallet
        if walletbtc < 0:
            walletbtc = round(tmp_btc, 4)
            walletbrl = tmp_brl
            trade_type = 'hold'

        # Sending order
        else:
            buy_list.remove(max(buy_list))
            # Generate order
            #order = mbtapi.Tapi('place_sell_order', quantity, current_price)
            #generate_order(order)

    # Buy condition
    elif current_price < reg_value:
        trade_type = 'buy'

        # Doing accounting
        walletbrl -= (quantity * current_price)
        walletbtc += round(quantity, 4)

        # Reversing order
        if walletbrl < 0:
            walletbtc = round(tmp_btc, 4)
            walletbrl = tmp_brl
            trade_type = 'hold'

        # Sending order
        else:
            buy_list.append(current_price)

            # Generate order
            #order = mbtapi.Tapi('place_buy_order', quantity, current_price)
            #generate_order(order)

    # Second sell condition
    # Check if the current price is above the minimum sell price
    elif len(buy_list) > 0 and current_price > min(buy_list) * margin:
        trade_type = 'sell'

        # Doing accounting
        walletbrl += (quantity * current_price)
        walletbtc -= quantity

        # Reversing order if there are no BTC in wallet
        if walletbtc < 0:
            walletbtc = tmp_btc
            walletbrl = tmp_brl
            trade_type = 'hold'

        # Sending order
        else:
            buy_list.remove(min(buy_list))
            # Generate order
            #order = mbtapi.Tapi('place_sell_order', quantity, current_price)
            #generate_order(order)

    # Hold condition if neither the stop loss nor minimum sell price is met
    else:
        trade_type = 'hold'


    # Write output to a csv file
    with open('run-test-stoploss-2.csv', 'a', newline='') as cfile:
        writer = csv.writer(cfile)

        # Collect the data
        data = [int(time.time()), trade_type, current_price, reg_value, round(walletbtc, 4), walletbrl]
        writer.writerow(data)

    print(data)

    with open('buylist-stoploss-2.csv', 'w', newline='') as sfile:
        writer = csv.writer(sfile)
        buy_list.sort()
        writer.writerow(buy_list)

    # Setting sleep based on trade
    if trade_type == 'sell':
        time.sleep(29)
    else:
        time.sleep(59)
