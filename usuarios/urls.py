from django.urls import path
from . import views
from productos.views import home_tienda  # ← Importa la vista de productos


app_name = 'usuarios'

urlpatterns = [
    # URL de inicio de sesión
    path('login/', views.login_view, name='login'),

    # URL de registro
    path('registro/', views.registro_usuario, name='registro'),

    # URL para cerrar sesión
    path('logout/', views.logout_view, name='logout'),

    # URL de la página principal (home)
    path('', home_tienda, name='home'),
]
