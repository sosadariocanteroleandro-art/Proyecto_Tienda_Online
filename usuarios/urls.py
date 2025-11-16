from django.urls import path
from . import views
from productos.views import home_tienda  # ← Importa la vista de productos

app_name = 'usuarios'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),

    # Autenticación básica
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_usuario, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # NUEVAS URLs para sistema de roles
    path('upgrade-vendedor/', views.upgrade_a_vendedor, name='upgrade_vendedor'),
    path('perfil/', views.perfil_usuario, name='perfil'),

    # Registro especial vía enlaces de afiliados
    path('registro-afiliado/', views.registro_via_afiliado, name='registro_afiliado'),
    path('registro-afiliado/<int:producto_id>/', views.registro_via_afiliado, name='registro_afiliado_producto'),
    path('registro-afiliado/<int:producto_id>/<str:ref_code>/', views.registro_via_afiliado,
         name='registro_afiliado_completo'),
]