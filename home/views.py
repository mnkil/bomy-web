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
import requests
import logging
from logging.handlers import RotatingFileHandler

# Setup logger for views
logger = logging.getLogger(__name__)

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

    # Check what columns we actually have and rename if needed
    print(f"Available columns: {list(df.columns)}")
    
    # Handle different possible timestamp column names
    if 'Timestamp' in df.columns:
        df.rename(columns={'Timestamp': 'timestamp'}, inplace=True)
    elif 'timestamp' not in df.columns:
        # If neither exists, try to find a similar column
        time_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if time_columns:
            df.rename(columns={time_columns[0]: 'timestamp'}, inplace=True)
            print(f"Renamed column '{time_columns[0]}' to 'timestamp'")
        else:
            return HttpResponse("No timestamp column found in database")
    
    # Convert timestamp to datetime for proper time filtering
    # Handle both Unix timestamps (milliseconds) and string timestamps
    if df['timestamp'].dtype == 'object':
        # If it's object type, try to parse as Unix timestamp first
        try:
            # Check if first value looks like Unix timestamp (13+ digits)
            first_ts = str(df['timestamp'].iloc[0])
            if len(first_ts) >= 13 and first_ts.isdigit():
                # Convert from milliseconds to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
                print("Converted Unix timestamps (milliseconds) to datetime")
            else:
                # Try regular datetime parsing
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print("Converted string timestamps to datetime")
        except:
            # Fallback to regular datetime parsing
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            print("Fallback: converted timestamps to datetime")
    else:
        # If it's numeric, assume Unix timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        print("Converted numeric Unix timestamps to datetime")
    
    # Find the most recent timestamp
    latest_timestamp = df['timestamp'].max()
    
    # Configure the time window for filtering recent prints
    # Adjust this value if you need a different time window (e.g., 2 minutes, 10 minutes)
    time_window_minutes = 2  # instead of 5
    
    # Filter for prints within the specified time window of the latest timestamp
    # This ensures we get the most recent batch of prints without mixing old data
    time_threshold = latest_timestamp - pd.Timedelta(minutes=time_window_minutes)
    dft = df[df['timestamp'] >= time_threshold].copy()
    
    # If we have very few recent prints, fall back to a reasonable number
    if len(dft) < 50:
        # Get the last 100 rows as fallback, but this should rarely happen
        dft = df.tail(100).copy()
    
    # Debug info - you can remove this later
    print(f"Total records in database: {len(df)}")
    print(f"Latest timestamp: {latest_timestamp}")
    print(f"Time threshold ({time_window_minutes} min): {time_threshold}")
    print(f"Records within {time_window_minutes} minutes: {len(dft)}")
    print(f"Time range: {dft['timestamp'].min()} to {dft['timestamp'].max()}")
    
    # Use time-filtered data for the main table display
    dft['apy'] = dft['apy'].multiply(100)
    dft['apy'] = dft['apy'].apply(lambda x: round(x,0))
    dft['fundingrate'] = dft['fundingrate'].multiply(10000)
    dft['fundingrate'] = dft['fundingrate'].apply(lambda x: round(x, 3))
    
    # Use the ORIGINAL full dataset for charts (keep what was working)
    dfchart = df[(df['market'] == 'ETH') | (df['market'] == 'BTC') | (df['market'] == 'SOL')]
    dfchart['apy'] = dfchart['apy'].multiply(100)
    dfchart['apy'] = dfchart['apy'].apply(lambda x: round(x,0))
    dfchart['fundingrate'] = dfchart['fundingrate'].multiply(10000)
    dfchart['fundingrate'] = dfchart['fundingrate'].apply(lambda x: round(x,3))
    
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
    
    # Convert timestamps to strings for JSON serialization (keep charts working)
    btc_data['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in btc_data['timestamp']]
    eth_data['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in eth_data['timestamp']]
    sol_data['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in sol_data['timestamp']]
    btc_data_ma['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in btc_data_ma['timestamp']]
    eth_data_ma['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in eth_data_ma['timestamp']]
    sol_data_ma['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(ts) else '' for ts in sol_data_ma['timestamp']]
    
    # Convert the main funding table data (dft) to JSON with formatted timestamps
    # Create a copy for display to avoid affecting the original data
    dft_display = dft.copy()
    dft_display['timestamp'] = dft_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    json_records = dft_display.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)

    # print(btc_data_ma)

    # Convert data to JSON for passing to the template
    btc_json = json.dumps(btc_data)
    eth_json = json.dumps(eth_data)
    sol_json = json.dumps(sol_data)
    btc_json_ma = json.dumps(btc_data_ma)
    eth_json_ma = json.dumps(eth_data_ma)
    sol_json_ma = json.dumps(sol_data_ma)

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
    btc_atm_db_path = 'home/ubuntu/bomy-web/static/btcatm_latest.db'
    try:
        conn = sqlite3.connect(btc_atm_db_path)
        df_btc_atm = pd.read_sql_query("SELECT * FROM btcatm", conn)
        conn.close()
    except:
        btc_atm_db_path = '/Users/michaelkilchenmann/bomy-web/static/btcatm_latest.db'
        conn = sqlite3.connect(btc_atm_db_path)
        df_btc_atm = pd.read_sql_query("SELECT * FROM btcatm", conn)
        conn.close()
    
    # Convert timestamp columns to datetime
    df_btc_atm['expiration_timestamp'] = pd.to_datetime(df_btc_atm['expiration_timestamp'])
    df_btc_atm['timestamp'] = pd.to_datetime(df_btc_atm['timestamp'])
    
    df_btc_atm['mid_iv'] = (df_btc_atm['bid_iv'] + df_btc_atm['ask_iv']) / 2
    # Assuming 'df' is your DataFrame

    # For BTC
    df_btc_atm = df_btc_atm.sort_values('expiration_timestamp')

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

    # For ETH
    df_eth_atm = df_eth_atm.sort_values('expiration_timestamp')

    df_eth_atm = df_eth_atm.sort_values('expiration_timestamp')

    eth_expiration_data = {
        'expiration_timestamp': df_eth_atm['expiration_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'mid_iv': df_eth_atm['mid_iv'].tolist(),
        'timestamp': df_eth_atm['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    }
    eth_expiration_data_json = json.dumps(eth_expiration_data, cls=DjangoJSONEncoder)

    # --- IBIT ETF DATA FROM POLYGON ---
    api_key = getattr(settings, 'POLYGON_API_KEY', None)
    ibit_data_json = '[]'
    try:
        if api_key:
            now = datetime.now()
            tomorrow = now + pd.Timedelta(days=1)
            end = tomorrow.strftime("%Y-%m-%d")
            start_date = "2024-06-01"
            end_date = end
            url = f"https://api.polygon.io/v2/aggs/ticker/IBIT/range/1/day/{start_date}/{end_date}"
            params = {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000,
                "apiKey": api_key
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data_ibit = response.json()
                ibit_records = []
                results = data_ibit.get("results", [])
                for bar in results:
                    date = pd.to_datetime(bar["t"], unit='ms')
                    ibit_records.append({
                        "Date": date,
                        "Open": bar["o"],
                        "Close": bar["c"]
                    })
                if ibit_records:
                    df_ibit = pd.DataFrame(ibit_records)
                    df_ibit.set_index('Date', inplace=True)
                    df_ibit['cum_return'] = np.log(df_ibit['Close'] / df_ibit['Close'].iloc[0]) * 100
                    df_ibit['overnight_return'] = np.log(df_ibit['Open'] / df_ibit['Close'].shift(1)) * 100
                    df_ibit['session_return'] = np.log(df_ibit['Close'] / df_ibit['Open']) * 100
                    df_ibit['cum_overnight'] = df_ibit['overnight_return'].cumsum()
                    df_ibit['cum_session'] = df_ibit['session_return'].cumsum()
                    df_ibit_json = df_ibit.reset_index()
                    df_ibit_json['Date'] = df_ibit_json['Date'].dt.strftime('%Y-%m-%d')
                    ibit_data_json = df_ibit_json.to_json(orient='records')
    except Exception as e:
        # Log the error but do not break the rest of the view
        logger.error(f'Error fetching IBIT data: {e}')
    # --- END IBIT ETF DATA ---

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
        'eth_expiration_data':  eth_expiration_data_json,
        'ibit_data': ibit_data_json
    }

    return render(request, 'hello.html', context)

def eq_view(request):
    now = datetime.now()
    tomorrow = now + pd.Timedelta(days=1)
    end = tomorrow.strftime("%Y-%m-%d")

    # Debug logging
    env_api_key = os.getenv('KEY_POLYGON')
    settings_api_key = getattr(settings, 'POLYGON_API_KEY', None)
    logger.error(f"Environment KEY_POLYGON: {env_api_key}")
    logger.error(f"Settings POLYGON_API_KEY: {settings_api_key}")
    
    api_key = getattr(settings, 'POLYGON_API_KEY', None)
    if not api_key:
        logger.error("Polygon API key not found in settings")
        return HttpResponse("API key not configured", status=500)
        
    logger.info(f"Using Polygon API key: {api_key[:4]}..." if api_key else "No API key found")
    
    # Fetch SPX data
    ticker = "I:SPX"
    start_date = "2024-06-01"
    end_date = end

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        logger.info(f"Successfully retrieved {len(results)} records from Polygon API")
        
        records = []
        for bar in results:
            date = pd.to_datetime(bar["t"], unit='ms')
            records.append({
                "Date": date,
                "Open": bar["o"],
                "High": bar["h"],
                "Low": bar["l"],
                "Close": bar["c"]
            })
        
        # Convert to DataFrame and set Date as index
        df = pd.DataFrame(records)
        df.set_index('Date', inplace=True)
        
        # Calculate metrics
        df['pct_change'] = df['Close'].pct_change() * 100
        df['abs_change'] = df['pct_change'].abs()
        df['abs_change_ma'] = df['abs_change'].rolling(window=20).mean()
        
        df['overnight_return'] = np.log(df['Open'] / df['Close'].shift(1)) * 100
        df['session_return'] = np.log(df['Close'] / df['Open']) * 100
        
        df['cum_total_return'] = np.log(df['Close'] / df['Close'].iloc[0]) * 100
        df['cum_overnight'] = df['overnight_return'].cumsum()
        df['cum_session'] = df['session_return'].cumsum()
        
        # Reset index and format dates
        df_json = df.reset_index()
        df_json['Date'] = df_json['Date'].dt.strftime('%Y-%m-%d')
        
        # Convert to JSON with proper date formatting
        spx_data_json = df_json.to_dict(orient='records')
        
    else:
        logger.error(f"Polygon API request failed with status code: {response.status_code}")
        logger.error(f"Response text: {response.text}")
        spx_data_json = []

    # Fetch SPY and FEZ data
    etfs = ["SPY", "FEZ", "IWM", "QQQ", "IBIT"]
    etf_data = {}
    
    for etf in etfs:
        url = f"https://api.polygon.io/v2/aggs/ticker/{etf}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            records = []
            for bar in results:
                date = pd.to_datetime(bar["t"], unit='ms')
                records.append({
                    "Date": date,
                    "Close": bar["c"]
                })
            
            # Convert to DataFrame and calculate cumulative returns
            df_etf = pd.DataFrame(records)
            df_etf.set_index('Date', inplace=True)
            df_etf['cum_return'] = np.log(df_etf['Close'] / df_etf['Close'].iloc[0]) * 100
            
            # Reset index and format dates
            df_etf_json = df_etf.reset_index()
            df_etf_json['Date'] = df_etf_json['Date'].dt.strftime('%Y-%m-%d')
            
            etf_data[etf] = df_etf_json.to_dict(orient='records')
        else:
            logger.error(f"Polygon API request failed for {etf} with status code: {response.status_code}")
            etf_data[etf] = []

    # Calculate the difference between SPY and FEZ returns
    if etf_data['SPY'] and etf_data['FEZ']:
        spy_df = pd.DataFrame(etf_data['SPY'])
        fez_df = pd.DataFrame(etf_data['FEZ'])
        
        # Merge the dataframes on Date
        merged_df = pd.merge(spy_df, fez_df, on='Date', suffixes=('_spy', '_fez'))
        merged_df['return_diff'] = merged_df['cum_return_spy'] - merged_df['cum_return_fez']
        
        etf_data['DIFF'] = merged_df[['Date', 'return_diff']].to_dict(orient='records')
    else:
        etf_data['DIFF'] = []

    # Calculate the difference between SPY and FEZ returns
    if etf_data['SPY'] and etf_data['IWM']:
        spy_df = pd.DataFrame(etf_data['SPY'])
        iwm_df = pd.DataFrame(etf_data['IWM'])
        
        # Merge the dataframes on Date
        merged_df = pd.merge(spy_df, iwm_df, on='Date', suffixes=('_spy', '_iwm'))
        merged_df['return_diff_spy_iwm'] = merged_df['cum_return_spy'] - merged_df['cum_return_iwm']
        
        etf_data['SPYIWMDIFF'] = merged_df[['Date', 'return_diff_spy_iwm']].to_dict(orient='records')
    else:
        etf_data['SPYIWMDIFF'] = []

    image_path = 'tramdepot.jpeg'
    image_url = static(image_path)
    
    context = {
        'image_url': image_url,
        'spx_data': json.dumps(spx_data_json),
        'spy_data': json.dumps(etf_data['SPY']),
        'fez_data': json.dumps(etf_data['FEZ']),
        'iwm_data': json.dumps(etf_data['IWM']),
        'qqq_data': json.dumps(etf_data['QQQ']),
        'ibit_data': json.dumps(etf_data['IBIT']),
        'diff_data': json.dumps(etf_data['DIFF']),
        'diffspyiwm_data': json.dumps(etf_data['SPYIWMDIFF'])
    }

    return render(request, 'eq.html', context)

def get_visits(request):
    """API endpoint to get visit logs"""
    try:
        days = int(request.GET.get('days', 7))
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Update path to new log location
        log_path = '/var/log/bomy-web/visits.log'
        
        visits = []
        # Read from main log file and all rotated files
        log_files = [log_path]
        for i in range(1, 4):  # Check .1, .2, .3 backup files
            backup = f"{log_path}.{i}"
            if os.path.exists(backup):
                log_files.append(backup)
                
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            visit = json.loads(line.strip())
                            visit_date = datetime.fromisoformat(visit['timestamp'])
                            if visit_date >= cutoff_date:
                                visits.append(visit)
                        except:
                            continue
        
        return JsonResponse({
            'status': 'success',
            'data': visits,
            'count': len(visits)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def visits_view(request):
    return render(request, 'visits.html')

def jetty_view(request):
    """View for displaying open trades from OMS database"""
    image_path = 'tramdepot.jpeg'
    image_url = static(image_path)
    
    # Initialize variables
    tables_info = []
    
    try:
        # Construct the path to the OMS database
        oms_db_path = os.path.join(settings.BASE_DIR, 'static', 'oms.db')
        
        # Check if the database file exists
        if not os.path.exists(oms_db_path):
            return HttpResponse("OMS database file does not exist.")
        
        # Connect to the OMS database
        conn = sqlite3.connect(oms_db_path)
        
        try:
            # Get table names
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            
            # Process each table
            for table_name in tables['name']:
                # Get schema
                schema = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
                
                # Check if 'open_trade' column exists
                if 'open_trade' in schema['name'].values:
                    # Get open trades only
                    data = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE open_trade = 1", conn)
                else:
                    # Fallback: get all data if no open_trade column
                    data = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                
                if not data.empty:
                    # Convert DataFrame to a format that works with Django templates
                    columns = list(data.columns)
                    rows = []
                    for _, row in data.iterrows():
                        row_data = []
                        for col in columns:
                            value = row[col]
                            if pd.isna(value):
                                row_data.append('-')
                            else:
                                row_data.append(str(value))
                        rows.append(row_data)
                    
                    # Store table info for display
                    tables_info.append({
                        'name': table_name,
                        'count': len(rows),
                        'columns': columns,
                        'rows': rows  # Use rows instead of data
                    })
        
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error reading OMS database: {str(e)}")
        return HttpResponse(f"An error occurred while reading OMS database: {str(e)}")
    
    context = {
        'image_url': image_url,
        'tables_info': tables_info,
        'total_tables': len(tables_info)
    }
    
    return render(request, 'jetty.html', context)
