from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # URL de inicio de sesión - nombre CORREGIDO a 'login'
    path('login/', views.login_view, name='login'),

    # URL de registro
    path('registro/', views.registro_usuario, name='registro_usuario'),

    # URL para cerrar sesión
    path('logout/', views.logout_view, name='logout_view'),

    # URL de la página principal (home)
    path('', views.home, name='home'),
]