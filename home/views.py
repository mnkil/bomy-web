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
    df = pd.read_pickle(df_url)
    df = df.tail(38)
    json_records = df.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)
    context = {
        'name': name,
        'size': size,
        'interests': interests,
        'image_url': image_url,
        'd' : data
    }

    return render(request, 'hello.html', context)
