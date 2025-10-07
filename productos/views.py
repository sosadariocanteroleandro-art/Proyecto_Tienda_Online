from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Producto, Pedido, ItemPedido, ConfiguracionPagos
from .forms import ProductoForm


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

    context = {
        'productos_afiliados': productos_afiliados,
        'productos_creados': productos_creados,
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
    Vista de detalle de un producto con sistema de referencia simplificado
    """
    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    # Obtener el parámetro 'ref' de la URL (username o user_id del afiliado)
    ref_code = request.GET.get('ref', None)
    afiliado_referido = None

    # Si hay código de referencia, buscar el usuario afiliado
    if ref_code:
        try:
            # Intentar buscar por username
            from django.contrib.auth import get_user_model
            User = get_user_model()
            afiliado_referido = User.objects.get(username=ref_code)

            # Verificar que el usuario esté afiliado al producto
            if afiliado_referido not in producto.afiliados.all():
                afiliado_referido = None
        except User.DoesNotExist:
            # Intentar buscar por ID
            try:
                afiliado_referido = User.objects.get(id=ref_code)
                if afiliado_referido not in producto.afiliados.all():
                    afiliado_referido = None
            except (User.DoesNotExist, ValueError):
                afiliado_referido = None

    # Verificar si el usuario actual está afiliado
    afiliado = False
    if request.user.is_authenticated:
        afiliado = request.user in producto.afiliados.all()

    # Verificar disponibilidad de stock
    stock_disponible = producto.tiene_stock()

    context = {
        'producto': producto,
        'afiliado': afiliado,
        'afiliado_referido': afiliado_referido,
        'ref_code': ref_code,
        'stock_disponible': stock_disponible,
        'cantidad_stock': producto.stock if producto.tipo_producto == 'FISICO' else None
    }

    return render(request, "productos/detalle_producto.html", context)


@login_required
def mis_links_afiliado(request):
    """
    Vista para mostrar los links de afiliado del usuario
    """
    productos_afiliados = request.user.productos_afiliados.filter(activo=True)

    # Generar links para cada producto usando el username como ref
    productos_con_link = []
    for producto in productos_afiliados:
        link = request.build_absolute_uri(
            reverse('productos:detalle_producto', kwargs={'producto_id': producto.id})
        ) + f'?ref={request.user.username}'

        productos_con_link.append({
            'producto': producto,
            'link': link,
        })

    context = {
        'productos_con_link': productos_con_link,
    }

    return render(request, 'productos/mis_links_afiliado.html', context)


@login_required
def editar_perfil_vendedor(request):
    """
    Vista para editar el perfil de vendedor/afiliado
    """
    # Por ahora, esta es una vista básica
    # Puedes expandirla con un formulario para editar información del usuario

    if request.method == 'POST':
        # Aquí puedes agregar lógica para actualizar el perfil
        # Por ejemplo: actualizar nombre, foto, descripción, etc.
        messages.success(request, '¡Perfil actualizado correctamente!')
        return redirect('productos:mis_links_afiliado')

    context = {
        'user': request.user,
    }

    return render(request, 'productos/editar_perfil_vendedor.html', context)


@login_required
def estadisticas_vendedor(request):
    """
    Vista para ver estadísticas del afiliado
    """
    productos_afiliados = request.user.productos_afiliados.all()

    # Obtener ventas generadas por este afiliado
    ventas = Pedido.objects.filter(
        afiliado_referido=request.user
    ).exclude(estado='PENDIENTE')

    # Calcular totales
    total_ventas = ventas.count()
    comision_total = sum(v.comision_total for v in ventas)
    comision_pendiente = sum(v.comision_total for v in ventas.filter(comision_pagada=False))
    comision_pagada = sum(v.comision_total for v in ventas.filter(comision_pagada=True))

    context = {
        'total_productos': productos_afiliados.count(),
        'productos_activos': productos_afiliados.filter(activo=True).count(),
        'total_ventas': total_ventas,
        'comision_total': comision_total,
        'comision_pendiente': comision_pendiente,
        'comision_pagada': comision_pagada,
        'ventas_recientes': ventas.order_by('-fecha_creacion')[:10],
    }

    return render(request, 'productos/estadisticas_vendedor.html', context)


# ============================================================================
# 🛒 SISTEMA DE CARRITO CON STOCK
# ============================================================================

@login_required
@login_required
def agregar_al_carrito(request, producto_id):
    """Agregar producto al carrito con validación de stock"""
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id, activo=True)
        cantidad = int(request.POST.get('cantidad', 1))

        # Obtener el afiliado referido si existe
        ref_code = request.POST.get('ref_code', None)
        afiliado_referido = None

        if ref_code:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                afiliado_referido = User.objects.get(username=ref_code)
                if afiliado_referido not in producto.afiliados.all():
                    afiliado_referido = None
            except User.DoesNotExist:
                pass

        # Validar cantidad
        if cantidad < 1:
            messages.error(request, 'La cantidad debe ser al menos 1.')
            return redirect('productos:detalle_producto', producto_id=producto_id)

        # Validar stock disponible
        if not producto.tiene_stock(cantidad):
            messages.error(
                request,
                f'Stock insuficiente. Solo hay {producto.stock} unidades disponibles.'
            )
            return redirect('productos:detalle_producto', producto_id=producto_id)

        # Obtener o crear carrito (pedido pendiente)
        carrito, created = Pedido.objects.get_or_create(
            usuario=request.user,
            estado='PENDIENTE',
            defaults={'total': 0}
        )

        # Asignar afiliado al carrito si no tiene uno y viene con referencia
        if not carrito.afiliado_referido and afiliado_referido:
            carrito.afiliado_referido = afiliado_referido
            carrito.save()

        # Verificar si el producto ya está en el carrito
        item_existente = ItemPedido.objects.filter(
            pedido=carrito,
            producto=producto
        ).first()

        if item_existente:
            nueva_cantidad = item_existente.cantidad + cantidad

            # Validar stock para la nueva cantidad total
            if not producto.tiene_stock(nueva_cantidad):
                messages.error(
                    request,
                    f'No puedes agregar {cantidad} unidades más. Solo hay {producto.stock} disponibles y ya tienes {item_existente.cantidad} en el carrito.'
                )
                return redirect('productos:detalle_producto', producto_id=producto_id)

            item_existente.cantidad = nueva_cantidad
            item_existente.save()
            messages.success(request, f'Cantidad actualizada en el carrito.')
        else:
            # Crear nuevo item en el carrito
            ItemPedido.objects.create(
                pedido=carrito,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )
            messages.success(request, f'{producto.nombre} agregado al carrito.')

        # Redirigir al carrito después de agregar
        return redirect('productos:ver_carrito')

    return redirect('productos:detalle_producto', producto_id=producto_id)

@login_required
def ver_carrito(request):
    """Ver contenido del carrito"""
    try:
        carrito = Pedido.objects.get(usuario=request.user, estado='PENDIENTE')
        items = carrito.items.all()

        # Verificar stock de cada item
        items_con_stock = []
        for item in items:
            item.stock_suficiente = item.producto.tiene_stock(item.cantidad)
            items_con_stock.append(item)

        context = {
            'carrito': carrito,
            'items': items_con_stock,
        }
    except Pedido.DoesNotExist:
        context = {
            'carrito': None,
            'items': [],
        }

    return render(request, 'productos/carrito.html', context)


@login_required
def actualizar_cantidad_carrito(request, item_id):
    """Actualizar cantidad de un item en el carrito"""
    if request.method == 'POST':
        item = get_object_or_404(ItemPedido, id=item_id, pedido__usuario=request.user)
        nueva_cantidad = int(request.POST.get('cantidad', 1))

        if nueva_cantidad < 1:
            messages.error(request, 'La cantidad debe ser al menos 1.')
            return redirect('productos:ver_carrito')

        # Validar stock
        if not item.producto.tiene_stock(nueva_cantidad):
            messages.error(
                request,
                f'Stock insuficiente. Solo hay {item.producto.stock} unidades disponibles.'
            )
            return redirect('productos:ver_carrito')

        item.cantidad = nueva_cantidad
        item.save()
        messages.success(request, 'Cantidad actualizada.')

    return redirect('productos:ver_carrito')


@login_required
def eliminar_del_carrito(request, item_id):
    """Eliminar un item del carrito"""
    item = get_object_or_404(ItemPedido, id=item_id, pedido__usuario=request.user)
    producto_nombre = item.producto.nombre
    item.delete()
    messages.success(request, f'{producto_nombre} eliminado del carrito.')
    return redirect('productos:ver_carrito')


@login_required
@transaction.atomic
@login_required
@login_required
def confirmar_pedido(request):
    """Vista para confirmar el pedido con selección de método de pago"""
    try:
        carrito = Pedido.objects.get(usuario=request.user, estado='PENDIENTE')
        items = carrito.items.all()

        if not items:
            messages.error(request, 'Tu carrito está vacío.')
            return redirect('productos:ver_carrito')

        # Validar stock
        for item in items:
            if not item.producto.tiene_stock(item.cantidad):
                messages.error(
                    request,
                    f'Stock insuficiente para {item.producto.nombre}.'
                )
                return redirect('productos:ver_carrito')

        # Verificar si solo hay productos digitales
        solo_digitales = all(item.producto.tipo_producto == 'DIGITAL' for item in items)

        # Obtener configuración de pagos
        try:
            config_pagos = ConfiguracionPagos.objects.first()
        except ConfiguracionPagos.DoesNotExist:
            config_pagos = None

        if request.method == 'POST':
            # Obtener datos del formulario
            metodo_pago = request.POST.get('metodo_pago')
            nombre_completo = request.POST.get('nombre_completo')
            email = request.POST.get('email')
            telefono = request.POST.get('telefono')
            direccion_envio = request.POST.get('direccion_envio', '')
            ciudad = request.POST.get('ciudad', '')
            notas = request.POST.get('notas', '')
            comprobante = request.FILES.get('comprobante_pago')

            # Validaciones básicas
            if not metodo_pago or not nombre_completo or not email or not telefono:
                messages.error(request, 'Por favor completa todos los campos obligatorios.')
                return redirect('productos:confirmar_pedido')

            # Si hay productos físicos O es pago en puerta, validar dirección
            if not solo_digitales or metodo_pago == 'CONTRA_ENTREGA':
                if not direccion_envio or not ciudad:
                    messages.error(request, 'La dirección y ciudad son obligatorias.')
                    return redirect('productos:confirmar_pedido')

            # Si es transferencia, validar comprobante
            if metodo_pago == 'TRANSFERENCIA' and not comprobante:
                messages.error(request, 'Por favor sube el comprobante de pago.')
                return redirect('productos:confirmar_pedido')

            # Validar stock y confirmar pedido
            with transaction.atomic():
                for item in items:
                    if not item.producto.tiene_stock(item.cantidad):
                        messages.error(
                            request,
                            f'Stock insuficiente para {item.producto.nombre}.'
                        )
                        return redirect('productos:ver_carrito')

                # Actualizar pedido
                carrito.nombre_completo = nombre_completo
                carrito.email = email
                carrito.telefono = telefono
                carrito.direccion_envio = direccion_envio
                carrito.ciudad = ciudad
                carrito.notas = notas
                carrito.metodo_pago = metodo_pago

                if comprobante:
                    carrito.comprobante_pago = comprobante

                carrito.estado = 'CONFIRMADO'
                carrito.fecha_confirmacion = timezone.now()
                carrito.save()

                # Reducir stock
                for item in items:
                    item.producto.reducir_stock(item.cantidad)

            # Enviar email (opcional)
            try:
                enviar_email_confirmacion(carrito)
            except Exception as e:
                print(f"Error enviando email: {e}")

            messages.success(
                request,
                f'¡Pedido #{carrito.numero_pedido} confirmado exitosamente!'
            )
            return redirect('productos:detalle_pedido', pedido_id=carrito.id)

        # GET - mostrar formulario
        context = {
            'carrito': carrito,
            'items': items,
            'solo_digitales': solo_digitales,
            'config_pagos': config_pagos,
        }

        return render(request, 'productos/confirmar_pedido.html', context)

    except Pedido.DoesNotExist:
        messages.error(request, 'No tienes un carrito activo.')
        return redirect('productos:home')


def enviar_email_confirmacion(pedido):
    """
    Función auxiliar para enviar email de confirmación
    """
    from django.core.mail import send_mail
    from django.conf import settings

    asunto = f'Pedido #{pedido.numero_pedido} - Confirmación'
    mensaje = f"""
Hola {pedido.nombre_completo},

¡Gracias por tu compra!

Tu pedido #{pedido.numero_pedido} ha sido recibido y está siendo procesado.

Detalles del pedido:
- Total: ₲{pedido.total:,.0f}
- Estado: {pedido.get_estado_display()}

Te contactaremos pronto para coordinar la entrega.

Saludos,
Tu Tienda
    """

    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        [pedido.email],
        fail_silently=True,
    )


@login_required
def mis_pedidos(request):
    """Ver historial de pedidos del usuario"""
    pedidos = Pedido.objects.filter(
        usuario=request.user
    ).exclude(estado='PENDIENTE').order_by('-fecha_creacion')

    return render(request, 'productos/mis_pedidos.html', {'pedidos': pedidos})


@login_required
def detalle_pedido(request, pedido_id):
    """Ver detalles de un pedido confirmado"""
    pedido = get_object_or_404(
        Pedido,
        id=pedido_id,
        usuario=request.user
    )

    if pedido.estado == 'PENDIENTE':
        messages.warning(request, 'Este pedido aún no ha sido confirmado.')
        return redirect('productos:ver_carrito')

    return render(request, 'productos/detalle_pedido.html', {'pedido': pedido})