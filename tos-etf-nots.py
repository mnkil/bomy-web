#!/usr/bin/env python3

import schwabdev
import logging
import dotenv
import os
from px_snapshot_tt import px_flow
from datetime import datetime
import pandas as pd
import yaml
from discordwebhook import Discord


class tickers:
    def __init__(self):
        self.dxtickers = ['MSTR', 'MSTU', 'TSLA', 'TSLT']
        self.pairs = [
            {
            "StockA": {"ticker": "MSTR", "beta": 1, "position": "long"},
            "StockB": {"ticker": "MSTU", "beta": 2, "position": "short"}
            },
            {
            "StockA": {"ticker": "TSLA", "beta": 1, "position": "long"},
            "StockB": {"ticker": "TSLT", "beta": 2, "position": "short"}
            },
        ]

def discord_tos(content):
    discord = Discord(url='https://discord.com/api/webhooks/1331124250324635678/XrtDF9AnKqquAno2zeMBypLcnhk4Dx90pE6PdWnuhnMiTEUDu8rR0gaBh_-FgmKjpmjk')
    discord.post(content=content)
	
def tos_init():
    # set logging level
    logging.basicConfig(level=logging.INFO)

    #load environment variables and make client
    dotenv.load_dotenv()
    client = schwabdev.Client('mo9cGsX0VrGn50IxPunymehxyUArVfIK', 'Z0d6G4VKi0qDzgEW', 'https://127.0.0.1')
    return client

def tos_auth(client):
    # get account number and hashes for linked accounts
    linked_accounts = client.account_linked().json()
    print(linked_accounts)
    # select the first account to use for orders
    account_hash = linked_accounts[0].get('hashValue')
    return account_hash

def tos_positions_process(account_hash, client):
    # get positions for selected account
    posx = client.account_details(account_hash, fields="positions").json()
    print(posx)
    current_nav = posx['aggregatedBalance']['currentLiquidationValue']
    print(f'Current NAV: {current_nav}')
    closeonly = posx['securitiesAccount']['isClosingOnlyRestricted']
    print(f'Close Only: {closeonly}')
    posx['securitiesAccount']['currentBalances']
    dfbalancescurrent = pd.DataFrame([posx['securitiesAccount']['currentBalances']])
    dfbalancesproj = dfbalancescurrent = pd.DataFrame([posx['securitiesAccount']['projectedBalances']])
    dfp = pd.DataFrame(posx['securitiesAccount']['positions'])
    # Parse the instrument data
    dfp['assetType'] = dfp['instrument'].apply(lambda x: x.get('assetType'))
    dfp['cusip'] = dfp['instrument'].apply(lambda x: x.get('cusip'))
    dfp['symbol'] = dfp['instrument'].apply(lambda x: x.get('symbol'))
    dfp['description'] = dfp['instrument'].apply(lambda x: x.get('description', ''))
    dfp['netChange'] = dfp['instrument'].apply(lambda x: x.get('netChange', ''))
    dfp['type'] = dfp['instrument'].apply(lambda x: x.get('type', ''))
    dfp['putCall'] = dfp['instrument'].apply(lambda x: x.get('putCall', ''))
    dfp['underlyingSymbol'] = dfp['instrument'].apply(lambda x: x.get('underlyingSymbol', ''))
    dfp.drop(columns=['instrument'], inplace=True)
    dfp.to_clipboard()
    return dfp

def tob_snapshot():
    sy = tickers()
    symbols = sy.dxtickers
    print(symbols)
    # symbols = ['IBIT', 'BITX', 'COIN', 'CONL', 'MSTR', 'MSTX', 'XLV', 'LABU']
    # symbols = ['SVIX', 'BITX', 'CONL', 'LABU', 'EWZ', 'MSTR', 'MSTU', 'TQQQ', 'QQQ', 'SPY']

    pxi = px_flow(symbols)
    ts = datetime.now()
    prices = pxi.process_market_data()
    prices.insert(0, 'timestamp', ts)
    prices = prices[['timestamp', 'streamer-symbol', 'eventType', 'eventType2', 'bidPrice', 'askPrice', 'midPrice', 'bidSize', 'askSize']]
    prices.insert(7, 'bidoffer', prices['askPrice'] - prices['bidPrice'])
    prices.insert(8, 'bidoffer_pct', (prices['askPrice'] - prices['bidPrice'])/prices['midPrice']*100)
    prices.insert(9, 'bidoffer_bp', (prices['askPrice'] - prices['bidPrice'])/prices['midPrice']*10000)
    prices['bidoffer_pct'] = prices['bidoffer_pct'].round(2)
    prices['bidoffer_bp'] = prices['bidoffer_bp'].round(1)
    # Add the corresponding threshold from the tickers.yaml data
    prices = prices.sort_values(by='streamer-symbol')
    return prices

def merge_tos_px(dfp, px):
    df_merged = pd.merge(px, dfp, left_on='streamer-symbol', right_on='symbol')
    df_merged['Quantity'] = df_merged['longQuantity'] - df_merged['shortQuantity']
    return df_merged

def full_process():
# try:
    # kill_port()
    # discord_ibkr_log('ibkr rv rebalance...')
    client = tos_init()
    account_hash = tos_auth(client)
    dfp = tos_positions_process(account_hash, client)
    px = tob_snapshot()
    df_merged = merge_tos_px(dfp, px)
    df_merged
    df_merged['usd_exposure'] = df_merged['midPrice'] * df_merged['Quantity']
    df_merged['beta'] = df_merged['streamer-symbol'].map({ticker['ticker']: ticker['beta'] for pair in tickers().pairs for ticker in pair.values()})
    df_merged['usd_exposure_beta_weighted'] = df_merged['usd_exposure'] * df_merged['beta']

    pairs = tickers().pairs
    for pair in pairs:
        stock_a = pair['StockA']['ticker']
        stock_b = pair['StockB']['ticker']
        exposure_a = df_merged[df_merged['symbol'] == stock_a]['usd_exposure_beta_weighted'].sum()
        exposure_b = df_merged[df_merged['symbol'] == stock_b]['usd_exposure_beta_weighted'].sum()
        total_exposure = exposure_a + exposure_b
        print('==============================')
        print(f"Total USD Exposure Beta Weighted for pair {stock_a} and {stock_b}: {round(total_exposure,2)}")
        if abs(total_exposure) > 100:
            print(f"Rebalance needed for pair {stock_a} and {stock_b}")
            discord_tos(f"Rebalance needed for pair {stock_a} and {stock_b}: Total USD Exposure Beta Weighted: {round(total_exposure,2)}")
            discord_tos(f'{stock_a} beta weighted exposure: {round(exposure_a,2)}, {stock_b} beta weighted exposure: {round(exposure_b,2)}')
    
    # for rvp in tickers().pairs:
    #     print(rvp)
    #     rvo = ibkr_rv_calcs(df_merged, rvp)
    #     trade_execution(rvo)
# except Exception as e:
    # print('error')
    # discord_ibkr_alert(f'Error in ibkr rv rebalance process: {str(e)}')
    return df_merged

if __name__ == "__main__":
    df = full_process()
    pd.options.display.float_format = '{:,.2f}'.format
    # print(df.to_string(index=False))
    # discord_tos('test')
    # tta = df.to_string(index=False)
    # discord_tos(tta)
