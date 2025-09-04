from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Incluye las URLs de la aplicación 'usuarios' en la raíz del proyecto.
    path('', include('usuarios.urls')),

    # Ahora también incluimos las URLs de la aplicación de productos
    path('productos/', include('productos.urls')),

    # Y las URLs de la aplicación de afiliados
    path('afiliados/', include('afiliados.urls')),

    # Ruta para el panel de administración de Django
    path('admin/', admin.site.urls),
]
