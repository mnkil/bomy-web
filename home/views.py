from django.shortcuts import render, HttpResponse
from django.templatetags.static import static
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
import sys
print(sys.version)
import pandas as pd
import json
import numpy as np
import sqlite3
import os

# Create your views here.
def hello(request):
    name = "mad mike"
    size = 40
    interests = ['mochi', 'degen crypto', 'beer']

    image_path = 'tramdepot.jpeg'
    image_url = static(image_path)

    # Construct the relative path to the SQLite database using BASE_DIR
    df_path = os.path.join(settings.BASE_DIR, 'static', 'dydx-funding.db')

    # Check if the database file exists
    if not os.path.exists(df_path):
        return HttpResponse("Database file does not exist.")

    connection = sqlite3.connect(df_path)

    try:
        df = pd.read_sql_query("SELECT * FROM [dydx-funding]", connection)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
    finally:
        connection.close()

    df.rename(columns={'Timestamp': 'timestamp'}, inplace=True)
    dft = df.tail(38)
    dft['apy'] = dft['apy'].multiply(100)
    dft['apy'] = dft['apy'].apply(lambda x: round(x,0))
    dft['fundingrate'] = dft['fundingrate'].multiply(10000)
    dft['fundingrate'] = dft['fundingrate'].apply(lambda x: round(x, 3))
    dfchart = df[(df['market'] == 'ETH-USD') | (df['market'] == 'BTC-USD') | (df['market'] == 'SOL-USD')]
    dfchart['apy'] = dfchart['apy'].multiply(100)
    dfchart['apy'] = dfchart['apy'].apply(lambda x: round(x,0))
    dfchart['fundingrate'] = dfchart['fundingrate'].multiply(10000)
    dfchart['fundingrate'] = dfchart['fundingrate'].apply(lambda x: round(x,3))
    json_records = dft.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)

    # Filter data for BTC-USD and ETH-USD

    df_btc = dfchart[dfchart['market'] == 'BTC-USD']
    df_eth = dfchart[dfchart['market'] == 'ETH-USD']
    df_sol = dfchart[dfchart['market'] == 'SOL-USD']
    df_btc_ma = df_btc.copy()
    df_eth_ma = df_eth.copy()
    df_sol_ma = df_sol.copy()
    df_btc_ma['apy'] = df_btc_ma['apy'].rolling(window=24).mean().fillna(0)
    df_eth_ma['apy'] = df_eth_ma['apy'].rolling(window=24).mean().fillna(0)
    df_sol_ma['apy'] = df_sol_ma['apy'].rolling(window=24).mean().fillna(0)

    # Prepare data for BTC-USD,ETH-USD and SOL-USD as lists
    btc_data = df_btc[['timestamp', 'apy']].to_dict(orient='list')
    eth_data = df_eth[['timestamp', 'apy']].to_dict(orient='list')
    sol_data = df_sol[['timestamp', 'apy']].to_dict(orient='list')
    btc_data_ma = df_btc_ma[['timestamp', 'apy']].to_dict(orient='list')
    eth_data_ma = df_eth_ma[['timestamp', 'apy']].to_dict(orient='list')
    sol_data_ma = df_sol_ma[['timestamp', 'apy']].to_dict(orient='list')

    # Convert data to JSON for passing to the template
    btc_json = json.dumps(btc_data)
    eth_json = json.dumps(eth_data)
    sol_json = json.dumps(sol_data)
    btc_json_ma = json.dumps(btc_data_ma)
    eth_json_ma = json.dumps(eth_data_ma)
    sol_json_ma = json.dumps(sol_data_ma)
    # print(btc_data_ma)

    # btc spot data
    df_btc_sp_path = 'home/ubuntu/bomy-web/static/btc-hist.pickle'
    df_url_btc_sp = df_btc_sp_path
    try:
        df_xbt = pd.read_pickle(df_url_btc_sp)
    except FileNotFoundError:
        df_btc_sp_path = '~/sofitas/static/btc-hist.pickle'
        df_url_btc_sp = df_btc_sp_path
        df_xbt = pd.read_pickle(df_url_btc_sp)
    # df_xbt = df_xbt.iloc[-1::-60].iloc[::-1]
    df_xbt.rename(columns={'Open Time': 'timestamp', 'Close': 'btc_spot'}, inplace=True)
    df_xbt['logreturn'] = np.log(df_xbt['btc_spot'] / df_xbt['btc_spot'].shift(1))
    df_xbt['logreturn'] = df_xbt['logreturn'] * 100
    df_xbt['logreturn'] = df_xbt['logreturn'].fillna(0)
    window_size = 7
    df_xbt['btc-1w-realized'] = df_xbt['logreturn'].rolling(window=window_size).std().fillna(0)
    df_xbt['btc-1w-realized'] = df_xbt['btc-1w-realized'] * 365.25**0.5
    df_xbt['timestamp'] = df_xbt['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # df_xbt = df_xbt.iloc[10:]
    # print(df_xbt)
    xbt = df_xbt[['timestamp', 'btc_spot', 'logreturn', 'btc-1w-realized']].to_dict(orient='list')
    xbt_json = json.dumps(xbt)
    # print('now xbt')
    # print(xbt)

    # btc atm data
    df_btc_atm_path = 'home/ubuntu/bomy-web/static/btcatm_latest.pickle'
    try:
        df_btc_atm = pd.read_pickle(df_btc_atm_path)
    except FileNotFoundError:
        df_btc_atm_path = '~/bomy-web/static/btcatm_latest.pickle'
        df_btc_atm = pd.read_pickle(df_btc_atm_path)
    df_btc_atm['mid_iv'] = (df_btc_atm['bid_iv'] + df_btc_atm['ask_iv']) / 2
    # Assuming 'df' is your DataFrame

    expiration_data = {
        'expiration_timestamp': df_btc_atm['expiration_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'mid_iv': df_btc_atm['mid_iv'].tolist(),
        'timestamp': df_btc_atm['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    }
    expiration_data_json = json.dumps(expiration_data, cls=DjangoJSONEncoder)

    # eth atm data
    df_eth_atm_path = 'home/ubuntu/bomy-web/static/ethatm_latest.pickle'
    try:
        df_eth_atm = pd.read_pickle(df_eth_atm_path)
    except FileNotFoundError:
        df_eth_atm_path = '~/bomy-web/static/ethatm_latest.pickle'
        df_eth_atm = pd.read_pickle(df_eth_atm_path)
    df_eth_atm['mid_iv'] = (df_eth_atm['bid_iv'] + df_eth_atm['ask_iv']) / 2
    # Assuming 'df' is your DataFrame

    eth_expiration_data = {
        'expiration_timestamp': df_eth_atm['expiration_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'mid_iv': df_eth_atm['mid_iv'].tolist(),
        'timestamp': df_eth_atm['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    }
    eth_expiration_data_json = json.dumps(eth_expiration_data, cls=DjangoJSONEncoder)

    context = {
        'name': name,
        'size': size,
        'interests': interests,
        'image_url': image_url,
        'd': data,
        'btc_data': btc_json,
        'eth_data': eth_json,
        'sol_data': sol_json,
        'btc_data_ma': btc_json_ma,
        'eth_data_ma': eth_json_ma,
        'sol_data_ma': sol_json_ma,
        'xbt_json': xbt_json,
        'expiration_data': expiration_data_json,
        'eth_expiration_data':  eth_expiration_data_json
    }

    return render(request, 'hello.html', context)
