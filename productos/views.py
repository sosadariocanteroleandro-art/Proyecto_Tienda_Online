from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm


def home_tienda(request):
    """
    Vista para la página principal de la tienda,
    separando productos físicos y digitales.
    """
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO')
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL')

    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'productos/home.html', context)


def afiliarme(request):
    """
    Vista de la página de afiliación
    """
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO')
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL')

    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'productos/afiliarme.html', context)


@login_required(login_url='/usuarios/login/')
def mis_productos(request):
    """
    Vista para mostrar los productos afiliados del usuario
    y también los productos que creó como vendedor
    """
    productos_afiliados = request.user.productos_afiliados.all()
    productos_creados = request.user.productos_creados.all()

    context = {
        'productos_afiliados': productos_afiliados,
        'productos_creados': productos_creados
    }

    return render(request, 'productos/mis_productos.html', context)


@login_required(login_url='/usuarios/login/')
def afiliar_producto(request, producto_id):
    """
    Vista para afiliar al usuario logueado a un producto
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        # Verificar si ya está afiliado
        if request.user in producto.afiliados.all():
            messages.warning(request, f'Ya estás afiliado a {producto.nombre}.')
        else:
            producto.afiliados.add(request.user)
            messages.success(request, f'¡Te has afiliado correctamente a {producto.nombre}!')

        return redirect('productos:mis_productos')

    return redirect('productos:home')


@login_required(login_url='/usuarios/login/')
def desafiliar_producto(request, producto_id):
    """
    Vista para desafiliar al usuario logueado de un producto
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        if request.user in producto.afiliados.all():
            producto.afiliados.remove(request.user)
            messages.success(request, f'Te has desafiliado exitosamente de {producto.nombre}.')
        else:
            messages.error(request, f'No estabas afiliado a {producto.nombre}.')
    else:
        messages.error(request, 'Método no permitido.')

    return redirect('productos:mis_productos')


@login_required(login_url='/usuarios/login/')
def crear_producto(request):
    """
    Vista para crear un nuevo producto (volverse vendedor)
    """
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.vendedor = request.user
            producto.save()
            messages.success(request, f'¡Producto "{producto.nombre}" creado correctamente! Ahora eres vendedor.')
            return redirect("productos:mis_productos")
    else:
        form = ProductoForm()

    return render(request, "productos/crear_producto.html", {"form": form})


def detalle_producto(request, producto_id):
    """
    Vista de detalle de un producto
    """
    producto = get_object_or_404(Producto, id=producto_id)
    afiliado = False

    if request.user.is_authenticated:
        afiliado = producto.afiliados.filter(id=request.user.id).exists()

    context = {
        'producto': producto,
        'afiliado': afiliado
    }

    return render(request, "productos/detalle_producto.html", context)