from django.urls import path
from . import views

# Define el nombre de la aplicación para namespacing
app_name = 'afiliados'

urlpatterns = [
    # Aquí puedes agregar las rutas específicas de tu aplicación afiliados
    # Ejemplo básico:
    # path('', views.lista_afiliados, name='lista_afiliados'),
    # path('<int:afiliado_id>/', views.detalle_afiliado, name='detalle_afiliado'),
    # path('registro/', views.registro_afiliado, name='registro_afiliado'),
]