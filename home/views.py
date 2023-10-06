from django.shortcuts import render, HttpResponse
from django.templatetags.static import static
import sys
print(sys.version)
print('no fucking way')
import pandas as pd
import json

# Create your views here.
def hello(request):
    name = "mad mike"
    size = 40
    interests = ['mochi', 'degen crypto', 'beer']

    image_path = 'tramdepot.jpeg'  # Path to the image within the static directory
    image_url = static(image_path)  # Get the URL for the image
    # df_path = os.path.join(settings.BASE_DIR, 'bomy-web/static/dydx-funding.pickle') 
    df_path = 'home/ubuntu/bomy-web/static/dydx-funding.pickle'
    df_url = df_path
    try:
        df = pd.read_pickle(df_url)
    except FileNotFoundError:
        df_path = '~/sofitas/static/dydx-funding.pickle'
        df_url = df_path
        df = pd.read_pickle(df_url)

    df.rename(columns={'Timestamp': 'timestamp'}, inplace=True)
    dft = df.tail(38)
    dft['apy'] = dft['apy'].multiply(100)
    dft['apy'] = dft['apy'].apply(lambda x: round(x,0))
    dft['fundingrate'] = dft['fundingrate'].multiply(10000)
    dft['fundingrate'] = dft['fundingrate'].apply(lambda x: round(x, 3))
    dfchart = df[(df['market'] == 'ETH-USD') | (df['market'] == 'BTC-USD')]
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
    df_btc_ma = df_btc.copy()
    df_eth_ma = df_eth.copy()
    df_btc_ma['apy'] = df_btc_ma['apy'].rolling(window=24).mean().fillna(0) 
    df_eth_ma['apy'] = df_eth_ma['apy'].rolling(window=24).mean().fillna(0)
 
    # Prepare data for BTC-USD and ETH-USD as lists
    btc_data = df_btc[['timestamp', 'apy']].to_dict(orient='list')
    eth_data = df_eth[['timestamp', 'apy']].to_dict(orient='list') 
    btc_data_ma = df_btc_ma[['timestamp', 'apy']].to_dict(orient='list')
    eth_data_ma = df_eth_ma[['timestamp', 'apy']].to_dict(orient='list') 
 
    # Convert data to JSON for passing to the template
    btc_json = json.dumps(btc_data)
    eth_json = json.dumps(eth_data)    
    btc_json_ma = json.dumps(btc_data_ma)
    eth_json_ma = json.dumps(eth_data_ma)     

    context = {
        'name': name,
        'size': size,
        'interests': interests,
        'image_url': image_url,
        'd': data,
        'btc_data': btc_json,
        'eth_data': eth_json,
        'btc_data_ma': btc_json_ma,
        'eth_data_ma': eth_json_ma
    }

    return render(request, 'hello.html', context)
