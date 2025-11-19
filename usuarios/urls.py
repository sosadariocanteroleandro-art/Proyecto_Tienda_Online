from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # ======= DASHBOARD Y GESTIÓN DE USUARIOS =======
    path('', views.home, name='home'),  # Dashboard principal para usuarios autenticados
    path('perfil/', views.perfil_usuario, name='perfil'),

    # ======= AUTENTICACIÓN =======
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_usuario, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # ======= NAVEGACIÓN DESDE LANDING =======
    path('ir-a-compras/', views.ir_a_compras, name='ir_a_compras'),
    path('ir-a-negocio/', views.ir_a_negocio, name='ir_a_negocio'),

    # ======= DASHBOARDS ESPECÍFICOS =======
    path('comprador/', views.comprador_dashboard, name='comprador_dashboard'),

    # ======= SISTEMA DE ROLES =======
    path('upgrade-vendedor/', views.upgrade_a_vendedor, name='upgrade_vendedor'),

    # ======= REGISTRO VÍA ENLACES DE AFILIADOS =======
    path('registro-afiliado/', views.registro_via_afiliado, name='registro_afiliado'),
    path('registro-afiliado/<int:producto_id>/', views.registro_via_afiliado, name='registro_afiliado_producto'),
    path('registro-afiliado/<int:producto_id>/<str:ref_code>/', views.registro_via_afiliado,
         name='registro_afiliado_completo'),
]