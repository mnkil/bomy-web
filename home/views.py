from django.shortcuts import render, HttpResponse
from django.templatetags.static import static
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
    dfchart = df[(df['market'] == 'ETH-USD') | (df['market'] == 'BTC-USD')]
    dft = df.tail(38)
    dft['apy'] = dft['apy'].multiply(100)
    dft['apy'] = dft['apy'].apply(lambda x: round(x,0))
    dft['fundingrate'] = dft['fundingrate'].multiply(10000)
    dft['fundingrate'] = dft['fundingrate'].apply(lambda x: round(x,2))
    json_records = dft.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)
    json_records2 = dfchart.reset_index().to_json(orient='records')
    cdata = []
    cdata = json.loads(json_records2)
    context = {
        'name': name,
        'size': size,
        'interests': interests,
        'image_url': image_url,
        'd' : data,
	'c' : cdata
    }

    return render(request, 'hello.html', context)
