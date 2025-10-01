from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Página principal de productos
    path('', views.home_tienda, name='home'),

    # Página de afiliación
    path('afiliarme/', views.afiliarme, name='afiliarme'),

    # Mis productos (afiliados y creados)
    path('mis-productos/', views.mis_productos, name='mis_productos'),

    # Crear producto (volverse vendedor)
    path('crear/', views.crear_producto, name='crear_producto'),

    # Detalle de producto (CON SISTEMA DE REFERENCIA)
    path('detalle/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # Afiliar/Desafiliar producto
    path('afiliar-producto/<int:producto_id>/', views.afiliar_producto, name='afiliar_producto'),
    path('desafiliar-producto/<int:producto_id>/', views.desafiliar_producto, name='desafiliar_producto'),

    # ========================================================================
    # 🆕 SISTEMA DE AFILIADOS CON LINKS DE REFERENCIA
    # ========================================================================

    # Crear y editar perfil de vendedor
    path('afiliado/crear-perfil/', views.crear_perfil_vendedor, name='crear_perfil_vendedor'),
    path('afiliado/editar-perfil/', views.editar_perfil_vendedor, name='editar_perfil_vendedor'),

    # Gestionar links de afiliado
    path('afiliado/mis-links/', views.mis_links_afiliado, name='mis_links_afiliado'),

    # Estadísticas
    path('afiliado/estadisticas/', views.estadisticas_vendedor, name='estadisticas_vendedor'),

    # ========================================================================
    # 🛒 SISTEMA DE PEDIDOS
    # ========================================================================
    path('pedido/crear/<int:producto_id>/', views.crear_pedido, name='crear_pedido'),
    path('pedido/confirmacion/<int:pedido_id>/', views.confirmacion_pedido, name='confirmacion_pedido'),
]