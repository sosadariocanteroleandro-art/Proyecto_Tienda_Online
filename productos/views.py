from django.shortcuts import render
from .models import Producto


def home_tienda(request):
    """
    Vista para la página principal de la tienda,
    separando productos físicos y digitales.
    """
    # Obtenemos los productos físicos y digitales
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO')
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL')

    # Pasamos los productos al contexto de la plantilla
    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'productos/home.html', context)
