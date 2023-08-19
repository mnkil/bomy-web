from django.shortcuts import render, HttpResponse


# Create your views here.
def hello(request):
    name="mad mike"
    size=40
    Interests=['mochi', 'degen crypto', 'beer']
    return render(request, 'hello.html',{'name':name, 'size':size, 'Interests':Interests})

