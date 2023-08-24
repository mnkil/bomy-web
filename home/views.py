from django.shortcuts import render, HttpResponse
from django.templatetags.static import static


# Create your views here.
def hello(request):
    name = "mad mike"
    size = 40
    interests = ['mochi', 'degen crypto', 'beer']

    image_path = 'tramdepot.jpeg'  # Path to the image within the static directory
    image_url = static(image_path)  # Get the URL for the image

    context = {
        'name': name,
        'size': size,
        'interests': interests,
        'image_url': image_url,
    }

    return render(request, 'hello.html', context)
