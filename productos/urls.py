from django.urls import path
from . import views

# Define el nombre de la aplicación para namespacing
app_name = 'productos'

urlpatterns = [
    # Aquí puedes agregar las rutas específicas de tu aplicación productos
    # Ejemplo básico:
    # path('', views.lista_productos, name='lista_productos'),
    # path('<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    # path('crear/', views.crear_producto, name='crear_producto'),
]