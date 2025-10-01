from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import Producto, PerfilVendedor, Pedido, ConfiguracionPagos
from .forms import ProductoForm
import random
import string


def home_tienda(request):
    """
    Vista para la página principal de la tienda,
    separando productos físicos y digitales.
    """
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO', activo=True)
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL', activo=True)

    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'productos/home.html', context)


def afiliarme(request):
    """
    Vista de la página de afiliación
    """
    productos_fisicos = Producto.objects.filter(tipo_producto='FISICO', activo=True)
    productos_digitales = Producto.objects.filter(tipo_producto='DIGITAL', activo=True)

    context = {
        'productos_fisicos': productos_fisicos,
        'productos_digitales': productos_digitales
    }

    return render(request, 'productos/afiliarme.html', context)


@login_required
def mis_productos(request):
    """
    Vista para mostrar los productos afiliados del usuario
    y también los productos que creó como vendedor
    """
    productos_afiliados = request.user.productos_afiliados.all()
    productos_creados = request.user.productos_creados.all()

    # Verificar si el usuario tiene perfil de vendedor
    tiene_perfil = hasattr(request.user, 'perfil_vendedor')

    context = {
        'productos_afiliados': productos_afiliados,
        'productos_creados': productos_creados,
        'tiene_perfil': tiene_perfil,
    }

    return render(request, 'productos/mis_productos.html', context)


@login_required
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


@login_required
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


@login_required
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
    Vista de detalle de un producto con sistema de referencia de afiliados
    """
    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    # Obtener el parámetro 'ref' de la URL
    ref_code = request.GET.get('ref', None)
    vendedor_perfil = None

    # Si hay código de referencia, buscar el vendedor
    if ref_code:
        try:
            vendedor_perfil = PerfilVendedor.objects.get(slug=ref_code, activo=True)

            # Verificar que el vendedor esté afiliado al producto
            if request.user.is_authenticated:
                if vendedor_perfil.usuario not in producto.afiliados.all():
                    vendedor_perfil = None

            # Registrar la visita (incrementar vistas del vendedor)
            if vendedor_perfil:
                # Aquí podrías crear un modelo Visit para tracking más detallado
                pass

        except PerfilVendedor.DoesNotExist:
            vendedor_perfil = None

    # Verificar si el usuario actual está afiliado
    afiliado = False
    if request.user.is_authenticated:
        afiliado = producto.afiliados.filter(id=request.user.id).exists()

    context = {
        'producto': producto,
        'afiliado': afiliado,
        'vendedor_perfil': vendedor_perfil,  # Info del vendedor que refirió
        'ref_code': ref_code,
    }

    return render(request, "productos/detalle_producto.html", context)


# ============================================================================
# 🆕 VISTAS PARA SISTEMA DE AFILIADOS
# ============================================================================

@login_required
def crear_perfil_vendedor(request):
    """
    Vista para crear el perfil de vendedor por primera vez
    """
    # Verificar si ya tiene perfil
    if hasattr(request.user, 'perfil_vendedor'):
        messages.info(request, 'Ya tienes un perfil de vendedor. Puedes editarlo.')
        return redirect('productos:editar_perfil_vendedor')

    if request.method == 'POST':
        nombre_tienda = request.POST.get('nombre_tienda', f'Tienda de {request.user.username}')
        descripcion = request.POST.get('descripcion', '¡Bienvenido a mi tienda!')
        color_tema = request.POST.get('color_tema', '#667eea')

        # Crear el perfil
        perfil = PerfilVendedor.objects.create(
            usuario=request.user,
            nombre_tienda=nombre_tienda,
            descripcion=descripcion,
            color_tema=color_tema
        )

        messages.success(request, f'¡Perfil de vendedor creado! Tu código de referencia es: {perfil.slug}')
        return redirect('productos:mis_links_afiliado')

    return render(request, 'productos/crear_perfil_vendedor.html')


@login_required
def editar_perfil_vendedor(request):
    """
    Vista para editar el perfil de vendedor
    """
    perfil = get_object_or_404(PerfilVendedor, usuario=request.user)

    if request.method == 'POST':
        perfil.nombre_tienda = request.POST.get('nombre_tienda', perfil.nombre_tienda)
        perfil.descripcion = request.POST.get('descripcion', perfil.descripcion)
        perfil.color_tema = request.POST.get('color_tema', '#667eea')

        # Manejar imágenes
        if request.FILES.get('foto_perfil'):
            perfil.foto_perfil = request.FILES['foto_perfil']
        if request.FILES.get('banner'):
            perfil.banner = request.FILES['banner']

        perfil.save()
        messages.success(request, '¡Perfil actualizado correctamente!')
        return redirect('productos:mis_links_afiliado')

    context = {
        'perfil': perfil
    }
    return render(request, 'productos/editar_perfil_vendedor.html', context)


@login_required
def mis_links_afiliado(request):
    """
    Vista para gestionar los links de afiliado del usuario
    """
    # Verificar si tiene perfil de vendedor
    if not hasattr(request.user, 'perfil_vendedor'):
        messages.warning(request, 'Primero debes crear tu perfil de vendedor.')
        return redirect('productos:crear_perfil_vendedor')

    perfil = request.user.perfil_vendedor
    productos_afiliados = request.user.productos_afiliados.filter(activo=True)

    # Generar links para cada producto
    productos_con_link = []
    for producto in productos_afiliados:
        link = request.build_absolute_uri(
            reverse('productos:detalle_producto', kwargs={'producto_id': producto.id})
        ) + f'?ref={perfil.slug}'

        productos_con_link.append({
            'producto': producto,
            'link': link,
        })

    context = {
        'perfil': perfil,
        'productos_con_link': productos_con_link,
    }

    return render(request, 'productos/mis_links_afiliado.html', context)


@login_required
def estadisticas_vendedor(request):
    """
    Vista para ver estadísticas del vendedor
    """
    if not hasattr(request.user, 'perfil_vendedor'):
        messages.warning(request, 'Primero debes crear tu perfil de vendedor.')
        return redirect('productos:crear_perfil_vendedor')

    perfil = request.user.perfil_vendedor
    productos_afiliados = request.user.productos_afiliados.all()

    # Aquí podrías calcular estadísticas más avanzadas
    # Por ahora mostramos información básica

    context = {
        'perfil': perfil,
        'total_productos': productos_afiliados.count(),
        'productos_activos': productos_afiliados.filter(activo=True).count(),
    }

    return render(request, 'productos/estadisticas_vendedor.html', context)


# ============================================================================
# 🛒 VISTAS PARA SISTEMA DE PEDIDOS
# ============================================================================

def crear_pedido(request, producto_id):
    """
    Vista para crear un nuevo pedido
    """
    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    # Obtener código de referencia si existe
    ref_code = request.GET.get('ref', None)
    vendedor_perfil = None

    if ref_code:
        try:
            vendedor_perfil = PerfilVendedor.objects.get(slug=ref_code, activo=True)
        except PerfilVendedor.DoesNotExist:
            vendedor_perfil = None

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.POST.get('nombre_cliente')
        email = request.POST.get('email_cliente')
        telefono = request.POST.get('telefono_cliente')
        direccion = request.POST.get('direccion_entrega', '')
        ciudad = request.POST.get('ciudad', '')
        cantidad = int(request.POST.get('cantidad', 1))
        metodo_pago = request.POST.get('metodo_pago')
        notas = request.POST.get('notas_cliente', '')

        # Crear el pedido
        pedido = Pedido.objects.create(
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            nombre_cliente=nombre,
            email_cliente=email,
            telefono_cliente=telefono,
            direccion_entrega=direccion,
            ciudad=ciudad,
            metodo_pago=metodo_pago,
            notas_cliente=notas,
            codigo_referencia=ref_code if ref_code else None,
            vendedor_referido=vendedor_perfil if vendedor_perfil else None,
        )

        # Si es transferencia, manejar el comprobante
        if metodo_pago == 'TRANSFERENCIA' and request.FILES.get('comprobante_pago'):
            pedido.comprobante_pago = request.FILES['comprobante_pago']
            pedido.save()

        # Enviar email de confirmación (opcional)
        try:
            asunto = f'Pedido #{pedido.numero_pedido} - {producto.nombre}'
            mensaje = f"""
            ¡Gracias por tu pedido!

            Número de pedido: {pedido.numero_pedido}
            Producto: {producto.nombre}
            Cantidad: {cantidad}
            Total: ₲{pedido.total:,.0f}
            Método de pago: {pedido.get_metodo_pago_display()}

            Te contactaremos pronto para confirmar tu pedido.

            Saludos,
            Tu Tienda
            """

            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except:
            pass

        # Redirigir a página de confirmación
        return redirect('productos:confirmacion_pedido', pedido_id=pedido.id)

    # Si es GET, mostrar el formulario
    context = {
        'producto': producto,
        'vendedor_perfil': vendedor_perfil,
        'ref_code': ref_code,
    }

    return render(request, 'productos/crear_pedido.html', context)


def confirmacion_pedido(request, pedido_id):
    """
    Vista de confirmación del pedido
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    context = {
        'pedido': pedido,
    }

    return render(request, 'productos/confirmacion_pedido.html', context)