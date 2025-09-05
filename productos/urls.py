from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Página principal de productos (separando físicos y digitales)
    path('', views.home_tienda, name='home'),
]
