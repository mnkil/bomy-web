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
import yfinance as yf
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import Visit

# Create your views here.
def hello(request):
    image_path = 'tramdepot.jpeg'
    image_url = static(image_path)

    # Construct the relative path to the SQLite database using BASE_DIR
    # df_path = os.path.join(settings.BASE_DIR, 'static', 'dydx-funding.db')
    dfh_path = os.path.join(settings.BASE_DIR, 'static', 'hl-funding.db')

    # Check if the database file exists
    # if not os.path.exists(df_path):
    #    return HttpResponse("dydx database file does not exist.")
    if not os.path.exists(dfh_path):
        return HttpResponse("hl database file does not exist.")

    # connection = sqlite3.connect(df_path)
    connection = sqlite3.connect(dfh_path)

    try:
        # df = pd.read_sql_query("SELECT * FROM [dydx-funding]", connection)
        df = pd.read_sql_query("SELECT * FROM [hyperliquid-funding]", connection)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
    finally:
        connection.close()

    df.rename(columns={'Timestamp': 'timestamp'}, inplace=True)
    dft = df.tail(180)
    dft['apy'] = dft['apy'].multiply(100)
    dft['apy'] = dft['apy'].apply(lambda x: round(x,0))
    dft['fundingrate'] = dft['fundingrate'].multiply(10000)
    dft['fundingrate'] = dft['fundingrate'].apply(lambda x: round(x, 3))
    dfchart = df[(df['market'] == 'ETH') | (df['market'] == 'BTC') | (df['market'] == 'SOL')]
    dfchart['apy'] = dfchart['apy'].multiply(100)
    dfchart['apy'] = dfchart['apy'].apply(lambda x: round(x,0))
    dfchart['fundingrate'] = dfchart['fundingrate'].multiply(10000)
    dfchart['fundingrate'] = dfchart['fundingrate'].apply(lambda x: round(x,3))
    json_records = dft.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)

    #dfh.rename(columns={'Timestamp': 'timestamp'}, inplace=True)
    #dfth = dfh.tail(151)
    #dfth['apy'] = dfth['apy'].multiply(100)
    #dfth['apy'] = dfth['apy'].apply(lambda x: round(x,0))
    #dfth['fundingrate'] = dfth['fundingrate'].multiply(10000)
    #dfth['fundingrate'] = dfth['fundingrate'].apply(lambda x: round(x, 3))
    # dfchart = df[(df['market'] == 'ETH-USD') | (df['market'] == 'BTC-USD') | (df['market'] == 'SOL-USD')]
    # dfchart['apy'] = dfchart['apy'].multiply(100)
    # dfchart['apy'] = dfchart['apy'].apply(lambda x: round(x,0))
    # dfchart['fundingrate'] = dfchart['fundingrate'].multiply(10000)
    # dfchart['fundingrate'] = dfchart['fundingrate'].apply(lambda x: round(x,3))
    #json_recordsh = dfth.reset_index().to_json(orient='records')
    #datah = []
    #datah = json.loads(json_recordsh)

    # Filter data for BTC-USD and ETH-USD

    df_btc = dfchart[dfchart['market'] == 'BTC']
    df_eth = dfchart[dfchart['market'] == 'ETH']
    df_sol = dfchart[dfchart['market'] == 'SOL']
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
    # df_btc_sp_path = 'home/ubuntu/bomy-web/static/btc-hist.pickle'
    # df_url_btc_sp = df_btc_sp_path
    # try:
    #     df_xbt = pd.read_pickle(df_url_btc_sp)
    # except FileNotFoundError:
    #    df_btc_sp_path = '~/sofitas/static/btc-hist.pickle'
    #    df_url_btc_sp = df_btc_sp_path
    #    df_xbt = pd.read_pickle(df_url_btc_sp)
    # df_xbt = df_xbt.iloc[-1::-60].iloc[::-1]
    # btc spot data from SQLite database instead of the pickle file
    btc_db_path = os.path.join(settings.BASE_DIR, 'static', 'btc-hist.db')

    # Check if the database file exists
    if not os.path.exists(btc_db_path):
        return HttpResponse("BTC history database file does not exist.")

    # Connect to the SQLite3 database
    connection = sqlite3.connect(btc_db_path)
    try:
        # Read the data from the database (assuming the relevant columns are 'Open Time' and 'Close')
        df_xbt = pd.read_sql_query('SELECT "Open Time" AS timestamp, "Open", "High", "Low", "Close" AS btc_spot FROM btc_history', connection)
        df_xbt.rename(columns={'Open Time': 'timestamp', 'Close': 'btc_spot', 'Open': 'Open', 'High' : 'High', 'Low': 'Low'}, inplace=True)
        df_xbt['logreturn'] = np.log(df_xbt['btc_spot'] / df_xbt['btc_spot'].shift(1))
        df_xbt['logreturn'] = df_xbt['logreturn'] * 100
        df_xbt['logreturn'] = df_xbt['logreturn'].fillna(0)
        window_size = 7
        df_xbt['btc-1w-realized'] = df_xbt['logreturn'].rolling(window=window_size).std().fillna(0)
        df_xbt['btc-1w-realized'] = df_xbt['btc-1w-realized'] * 365.25**0.5
        df_xbt['timestamp'] = pd.to_datetime(df_xbt['timestamp'])
        df_xbt['timestamp'] = df_xbt['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # df_xbt = df_xbt.iloc[10:]
        # print(df_xbt)


        df_xbt['close_open'] = np.log(df_xbt['btc_spot'] / df_xbt['Open'])
        df_xbt['open_close_prev'] = np.log(df_xbt['Open'] / df_xbt['btc_spot'].shift(1))
        df_xbt['high_low'] = np.log(df_xbt['High'] / df_xbt['Low'])


        # 1) Compute daily "Yang-Zhang variance"
        df_xbt['yz_daily_var'] = (
            0.34 * df_xbt['close_open']**2 +
            0.34 * df_xbt['open_close_prev']**2 +
            0.16 * df_xbt['high_low']**2
        )

        # 2) Take a 7-day rolling average of that daily variance
        #    and THEN take the square root to get a standard deviation.
        df_xbt['btc-1w-realized-yang_zhang'] = (
            df_xbt['yz_daily_var']
            .rolling(window=7)
            .mean()
            .fillna(0)
            .pipe(np.sqrt)              # <-- Take the sqrt to convert variance -> stdev
            * np.sqrt(365.25) * 100     # <-- Annualize and turn into a percentage
        )
        
        df_xbt = df_xbt.iloc[7:]
        df_xbt['timestamp'] = pd.to_datetime(df_xbt['timestamp'])
        df_xbt['timestamp'] = df_xbt['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        xbt = df_xbt[['timestamp', 'btc_spot', 'logreturn', 'btc-1w-realized', 'btc-1w-realized-yang_zhang']].to_dict(orient='list')


        # xbt = df_xbt[['timestamp', 'btc_spot', 'logreturn', 'btc-1w-realized', ]].to_dict(orient='list')
        xbt_json = json.dumps(xbt)


        # print('now xbt')
    # print(xbt)
    finally:
        connection.close()
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
        'image_url': image_url,
        'd': data,
        'e': data,
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

def eq_view(request):
    # Fetch data for ^SPX
    now = datetime.now()
    tomorrow = now + pd.Timedelta(days=1)
    end = tomorrow.strftime("%Y-%m-%d")
    print(f'end: {end}')
    def yfd(ticker, start='2024-06-01', end=end):
        ticker_symbol = ticker
        yf_data = yf.Ticker(ticker_symbol)
        if not start:
            start = "2023-01-01"
        if not end:
            now = datetime.now()
            tomorrow = now + pd.Timedelta(days=1)
            end = tomorrow.strftime("%Y-%m-%d")
        hist_data = yf_data.history(start=start, end=end, auto_adjust=False)
        return hist_data

    spx_data = yfd('^SPX')
    
    # Calculate daily returns and absolute returns
    spx_data['pct_change'] = spx_data['Close'].pct_change() * 100
    spx_data['abs_change'] = spx_data['pct_change'].abs()  # Add absolute returns
    spx_data['abs_change_ma'] = spx_data['abs_change'].rolling(window=20).mean()  # 20-day moving average
    
    # Calculate overnight and session log returns
    spx_data['overnight_return'] = np.log(spx_data['Open'] / spx_data['Close'].shift(1)) * 100
    spx_data['session_return'] = np.log(spx_data['Close'] / spx_data['Open']) * 100
    
    # Calculate cumulative returns
    spx_data['cum_total_return'] = np.log(spx_data['Close'] / spx_data['Close'].iloc[0]) * 100
    spx_data['cum_overnight'] = spx_data['overnight_return'].cumsum()
    spx_data['cum_session'] = spx_data['session_return'].cumsum()
    
    # Include all necessary data in JSON
    spx_data_json = spx_data[['Close', 'pct_change', 'abs_change', 'abs_change_ma', 
                             'cum_total_return', 'cum_overnight', 'cum_session']].reset_index().to_json(orient='records', date_format='iso')

    image_path = 'tramdepot.jpeg'
    image_url = static(image_path)

    # Debug print to see what we're sending
    print("JSON data sample:", spx_data_json[:200])
    
    context = {
        'image_url': image_url,
        'spx_data': spx_data_json
    }

    return render(request, 'eq.html', context)

def get_visits(request):
    """API endpoint to get visit logs"""
    try:
        # Get parameters
        days = int(request.GET.get('days', 7))  # Default to 7 days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query the database
        visits = Visit.objects.filter(
            timestamp__gte=cutoff_date
        ).values('timestamp', 'path', 'ip')
        
        return JsonResponse({
            'status': 'success',
            'data': list(visits),
            'count': visits.count()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def visits_view(request):
    return render(request, 'visits.html')
