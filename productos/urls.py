from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Página principal de productos (separando físicos y digitales)
    path('', views.home_tienda, name='home'),

    # Página de afiliación
    path('afiliarme/', views.afiliarme, name='afiliarme'),

    # Mis productos (afiliados y creados)
    path('mis-productos/', views.mis_productos, name='mis_productos'),

    # Crear producto (volverse vendedor)
    path('crear/', views.crear_producto, name='crear_producto'),

    # Detalle de producto
    path('detalle/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # Afiliar/Desafiliar producto
    path('afiliar-producto/<int:producto_id>/', views.afiliar_producto, name='afiliar_producto'),
    path('desafiliar-producto/<int:producto_id>/', views.desafiliar_producto, name='desafiliar_producto'),
]