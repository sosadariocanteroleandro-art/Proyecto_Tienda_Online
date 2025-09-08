from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Página principal de productos (separando físicos y digitales)
    path('', views.home_tienda, name='home'),
    path('afiliarme/', views.afiliarme, name='afiliarme'),
    path('mis-productos/', views.mis_productos, name='mis_productos'),
    path('afiliar-producto/<int:producto_id>/', views.afiliar_producto, name='afiliar_producto'),
]
