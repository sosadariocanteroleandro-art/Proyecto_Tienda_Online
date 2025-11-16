from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Pedido  # ← Solo Pedido, Producto viene de productos
from productos.models import Producto  # ← Importar desde productos


def registro_usuario(request):
    """
    Vista para registrar un nuevo usuario.
    Los usuarios se registran automáticamente como COMPRADORES.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tipo_usuario = 'COMPRADOR'  # Todos empiezan como compradores
            user.save()
            messages.success(request, '¡Cuenta creada exitosamente! Puedes empezar a comprar inmediatamente.')
            return redirect('usuarios:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    """
    Vista para iniciar sesión.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Redirigir según tipo de usuario
            if user.es_vendedor():
                return redirect('productos:mis_productos')
            else:
                return redirect('usuarios:home')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            form = AuthenticationForm(request.POST)
    else:
        form = AuthenticationForm()

    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    """
    Vista para cerrar la sesión.
    """
    logout(request)
    return redirect('usuarios:login')


def home(request):
    """
    Vista del Dashboard principal - se adapta según el tipo de usuario
    """
    context = {}

    if request.user.is_authenticated:
        # Estadísticas básicas para todos los usuarios
        context['user'] = request.user
        context['tipo_usuario'] = request.user.get_tipo_usuario_display()

        # Pedidos del usuario
        context['pedidos_count'] = Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').count()

        # Items en carrito
        try:
            carrito = Pedido.objects.get(usuario=request.user, estado='PENDIENTE')
            context['items_carrito'] = carrito.items.count()
        except Pedido.DoesNotExist:
            context['items_carrito'] = 0

        # Últimos 5 pedidos
        context['ultimos_pedidos'] = Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').order_by('-fecha_creacion')[:5]

        # Estadísticas específicas para VENDEDORES
        if request.user.es_vendedor():
            context['productos_afiliados_count'] = request.user.productos_afiliados.count()

            # Comisiones totales
            ventas_como_afiliado = Pedido.objects.filter(
                afiliado_referido=request.user
            ).exclude(estado='PENDIENTE')
            context['comisiones_totales'] = sum(v.comision_total for v in ventas_como_afiliado)

            if request.user.is_superuser:
                context['productos_creados_count'] = request.user.productos_creados.count()

    return render(request, 'usuarios/home.html', context)


@login_required
def upgrade_a_vendedor(request):
    """
    Vista para convertir un comprador en vendedor/afiliado
    """
    if request.user.es_vendedor():
        messages.info(request, 'Ya eres vendedor/afiliado.')
        return redirect('productos:mis_productos')

    if request.method == 'POST':
        # Confirmar upgrade
        confirmacion = request.POST.get('confirmar_upgrade')
        if confirmacion == 'si':
            if request.user.upgrade_a_vendedor():
                messages.success(
                    request,
                    '¡Felicitaciones! Ahora eres vendedor/afiliado. Ya puedes afiliarte a productos y ganar comisiones.'
                )
                return redirect('productos:afiliarme')
            else:
                messages.error(request, 'Hubo un error al procesar tu upgrade.')
        else:
            messages.info(request, 'Upgrade cancelado.')
            return redirect('usuarios:home')

    # GET - Mostrar página de confirmación
    context = {
        'pedidos_realizados': Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').count()
    }

    return render(request, 'usuarios/upgrade_vendedor.html', context)


@login_required
def perfil_usuario(request):
    """
    Vista del perfil del usuario con información sobre su cuenta
    """
    context = {
        'user': request.user,
        'pedidos_count': Pedido.objects.filter(usuario=request.user).exclude(estado='PENDIENTE').count(),
    }

    # Estadísticas adicionales para vendedores
    if request.user.es_vendedor():
        ventas_como_afiliado = Pedido.objects.filter(
            afiliado_referido=request.user
        ).exclude(estado='PENDIENTE')

        context.update({
            'productos_afiliados_count': request.user.productos_afiliados.count(),
            'ventas_referidas_count': ventas_como_afiliado.count(),
            'comisiones_totales': sum(v.comision_total for v in ventas_como_afiliado),
        })

    return render(request, 'usuarios/perfil.html', context)


def registro_via_afiliado(request, producto_id=None, ref_code=None):
    """
    Registro especial cuando viene de un link de afiliado.
    El usuario se registra automáticamente como COMPRADOR
    y es dirigido directamente al producto.
    """
    # Si ya está autenticado, redirigir al producto
    if request.user.is_authenticated:
        if producto_id:
            redirect_url = f"/productos/detalle/{producto_id}/"
            if ref_code:
                redirect_url += f"?ref={ref_code}"
            return redirect(redirect_url)
        return redirect('productos:home')

    producto = None
    if producto_id:
        try:
            producto = Producto.objects.get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            messages.error(request, 'Producto no encontrado.')
            return redirect('productos:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tipo_usuario = 'COMPRADOR'  # Registro automático como comprador
            user.save()

            # Login automático
            login(request, user)

            messages.success(
                request,
                '¡Bienvenido! Tu cuenta ha sido creada. Ahora puedes realizar tu compra.'
            )

            # Redirigir al producto específico
            if producto:
                redirect_url = f"/productos/detalle/{producto_id}/"
                if ref_code:
                    redirect_url += f"?ref={ref_code}"
                return redirect(redirect_url)

            return redirect('productos:home')
    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
        'producto': producto,
        'ref_code': ref_code,
        'from_affiliate': True
    }

    return render(request, 'usuarios/registro_afiliado.html', context)