from django.shortcuts import render
from .models import Producto


def home_tienda(request):
    """
    Esta vista renderiza la página principal de la Tienda,
    separando los productos físicos de los digitales.
    """
    # Filtramos los productos para obtener solo los físicos.
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO')
    # Filtramos los productos para obtener solo los digitales.
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL')

    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'usuarios/home.html', context)
