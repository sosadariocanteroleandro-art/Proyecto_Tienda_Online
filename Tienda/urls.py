from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # URLs de la app usuarios
    path('', include('usuarios.urls')),  # La página principal y login/registro se manejan aquí

    # URLs de la app productos
    path('productos/', include('productos.urls')),  # Aquí se manejarán los productos físicos y digitales
]
