from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
    """Vista de la pagina principal """
    return render(request, 'productos/home.html', context)

def afiliarme(request):
    #Obtenemos los productos fisicos y digitales
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO')
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL')

    #Pasamos al contexto
    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    """Vista de la pagina de afiliacion"""
    return render(request, 'productos/afiliarme.html', context)

@login_required(login_url='/login/')  # ← Especifica la URL de login
def mis_productos(request):
    productos_afiliados = request.user.productos_afiliados.all()
    return render(request, 'productos/mis_productos.html', {'productos':productos_afiliados})

@login_required(login_url='/login/')  # ← Especifica la URL de login
def afiliar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.afiliados.add(request.user)
    messages.success(request, f'Te has afiliado correctamente a {producto.nombre}.')
    return redirect('productos:mis_productos')  # Redirige a la página de afiliación

@login_required(login_url='/login/')  # ← Especifica la URL de login
def desafiliar_producto(request, producto_id):
    """
    Vista para desafiliar a un usuario de un producto
    """
    # Verificar que sea una petición POST para seguridad
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        # Verificar que el usuario esté afiliado a este producto
        if request.user in producto.afiliados.all():
            producto.afiliados.remove(request.user)
            messages.success(request, f'Te has desafiliado exitosamente de {producto.nombre}.')
        else:
            messages.error(request, f'No estabas afiliado a {producto.nombre}.')

        return redirect('productos:mis_productos')
    else:
        # Si no es POST, redirigir a mis productos
        messages.error(request, 'Método no permitido.')
        return redirect('productos:mis_productos')