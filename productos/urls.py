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

    # Detalle de producto (CON SISTEMA DE REFERENCIA SIMPLIFICADO)
    path('detalle/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # Afiliar/Desafiliar producto
    path('afiliar-producto/<int:producto_id>/', views.afiliar_producto, name='afiliar_producto'),
    path('desafiliar-producto/<int:producto_id>/', views.desafiliar_producto, name='desafiliar_producto'),

    # ========================================================================
    # 🆕 SISTEMA DE AFILIADOS SIMPLIFICADO
    # ========================================================================
    # Mis links de afiliado
    path('mis-links/', views.mis_links_afiliado, name='mis_links_afiliado'),

    # Editar perfil de vendedor/afiliado
    path('editar-perfil/', views.editar_perfil_vendedor, name='editar_perfil_vendedor'),

    # Estadísticas de afiliado
    path('estadisticas/', views.estadisticas_vendedor, name='estadisticas_vendedor'),

    # ========================================================================
    # 🛒 SISTEMA DE CARRITO CON STOCK
    # ========================================================================
    # Ver carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),

    # Agregar producto al carrito
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),

    # Actualizar cantidad en el carrito
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),

    # Eliminar del carrito
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),

    # Confirmar pedido
    path('carrito/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),

    # Ver mis pedidos
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),

    # Detalle de pedido confirmado
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
]