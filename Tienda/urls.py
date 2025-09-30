from django.contrib import admin
from django.urls import path, include
# AGREGAR ESTAS IMPORTACIONES:
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # URLs de allauth (¡ESENCIALES!)
    path('accounts/', include('allauth.urls')),  # ← ¡AGREGA ESTA LÍNEA!

    # URLs de la app productos
    path('productos/', include('productos.urls')),

    # URLs de la app usuarios (debe ir al final para no interferir)
    path('', include('usuarios.urls')),  # La página principal y login/registro se manejan aquí
]

# ✅ CONFIGURACIÓN PARA ARCHIVOS MEDIA (IMÁGENES)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)