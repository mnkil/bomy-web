"""
URL configuration for sofitas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name='home'),  # Assuming 'hello' is your home view
    path('eq/', views.eq_view, name='eq_view'),  # Lowercase 'eq'
    path('EQ/', views.eq_view, name='eq_view_upper'),  # Uppercase 'EQ'
    path('api/visits/', views.get_visits, name='get_visits'),
    path('visits/', views.visits_view, name='visits'),
    # other paths...
]
