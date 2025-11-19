# urls.py principal (Tienda/urls.py)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importar la vista de landing page
from usuarios.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # ======= LANDING PAGE COMO PÁGINA PRINCIPAL =======
    path('', landing_page, name='landing_page'),

    # ======= AUTENTICACIÓN OAUTH =======
    path('accounts/', include('allauth.urls')),  # URLs de allauth para Google OAuth

    # ======= APPS PRINCIPALES =======
    path('usuarios/', include('usuarios.urls')),  # Dashboard y gestión de usuarios
    path('productos/', include('productos.urls')),  # Productos y afiliación
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)