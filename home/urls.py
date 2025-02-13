from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name='home'),  # Assuming 'hello' is your home view
    path('eq/', views.eq_view, name='eq_view'),  # Lowercase 'eq'
    path('EQ/', views.eq_view, name='eq_view_upper'),  # Uppercase 'EQ'
    # other paths...
] 