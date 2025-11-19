from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .forms import CustomUserCreationForm
from productos.models import Pedido, Producto  # ← CORREGIDO: Ambos vienen de productos
from django.shortcuts import render
from django.conf import settings
from productos.models import Producto


def registro_usuario(request):
    """
    Vista para registrar nuevos VENDEDORES que se registran directamente.
    Estos usuarios vienen a la plataforma para vender, no para comprar.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tipo_usuario = 'VENDEDOR'  # Se registran directo como vendedores
            user.origen_registro = 'DIRECTO'
            user.fecha_upgrade_vendedor = timezone.now()  # Ya son vendedores desde el inicio
            user.save()
            messages.success(request,
                             '¡Bienvenido! Tu cuenta de vendedor ha sido creada. Ahora puedes afiliarte a productos y empezar a ganar.')
            login(request, user)  # Login automático
            return redirect('productos:afiliarme')  # Directo a afiliarse
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def registro_via_afiliado(request, producto_id=None, ref_code=None):
    """
    Registro de CLIENTES que llegan vía link de afiliado.
    Estos usuarios vienen a comprar pero también ver la oportunidad de vender.
    """
    # Detectar el afiliado que refiere
    afiliado_referido = None
    if ref_code:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            afiliado_referido = User.objects.get(username=ref_code)
            if not afiliado_referido.es_vendedor():
                afiliado_referido = None
        except User.DoesNotExist:
            pass

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
            user.tipo_usuario = 'COMPRADOR'  # Clientes que llegan a comprar

            # ===== CONFIGURAR ORIGEN Y REFERENCIA =====
            if afiliado_referido:
                user.origen_registro = 'AFILIADO'
                user.referido_por = afiliado_referido
                user.fecha_referido = timezone.now()
                success_message = f'¡Bienvenido! Fuiste invitado por {afiliado_referido.nombre}. Completa tu compra y descubre cómo TÚ también puedes ganar dinero vendiendo.'
            else:
                user.origen_registro = 'DIRECTO'
                success_message = '¡Registro exitoso! Completa tu compra y descubre nuestra oportunidad de negocio.'

            user.save()

            # Login automático
            login(request, user)
            messages.success(request, success_message)

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
        'afiliado_referido': afiliado_referido,
        'from_affiliate': afiliado_referido is not None,
        'is_customer_registration': True  # Indica que es registro de cliente
    }

    return render(request, 'usuarios/registro_afiliado.html', context)


def login_view(request):
    """
    Vista para iniciar sesión con soporte para redirección automática.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # MEJORA: Manejar redirección del parámetro 'next'
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # Redirigir según tipo de usuario si no hay 'next'
            if user.es_vendedor():
                return redirect('productos:mis_productos')
            else:
                # Cliente/comprador va al home para ver oportunidad de vender
                return redirect('usuarios:home')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            form = AuthenticationForm(request.POST)
    else:
        form = AuthenticationForm()

    # Pasar 'next' al template para mantenerlo en el formulario
    context = {
        'form': form,
        'next': request.GET.get('next', '')
    }

    return render(request, 'usuarios/login.html', context)


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

        # Pedidos del usuario (tanto vendedores como compradores pueden tener pedidos)
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

            # Comisiones totales ganadas como afiliado
            ventas_como_afiliado = Pedido.objects.filter(
                afiliado_referido=request.user
            ).exclude(estado='PENDIENTE')
            context['comisiones_totales'] = sum(v.comision_total for v in ventas_como_afiliado)
            context['ventas_generadas'] = ventas_como_afiliado.count()

            if request.user.is_superuser:
                context['productos_creados_count'] = request.user.productos_creados.count()

        # Para compradores vía afiliado, mostrar potencial de ganancias
        else:
            context['productos_disponibles_count'] = Producto.objects.filter(activo=True).count()
            # Simular potencial de ganancias
            context['potencial_comision_mensual'] = 150000  # Ejemplo

    return render(request, 'usuarios/home.html', context)


@login_required
def upgrade_a_vendedor(request):
    """
    Vista para convertir un COMPRADOR (cliente) en VENDEDOR.
    Solo los compradores pueden hacer upgrade, los vendedores ya son vendedores.
    """
    if request.user.es_vendedor():
        messages.info(request, 'Ya eres vendedor/afiliado.')
        return redirect('productos:mis_productos')

    if request.method == 'POST':
        # Confirmar upgrade
        confirmacion = request.POST.get('confirmar_upgrade')
        acepta_terminos = request.POST.get('acepto_terminos')

        if confirmacion == 'si' and acepta_terminos:
            if request.user.upgrade_a_vendedor():
                messages.success(
                    request,
                    '¡Felicitaciones! Ahora eres vendedor/afiliado. Ya puedes afiliarte a productos y ganar comisiones por cada venta.'
                )
                return redirect('productos:afiliarme')  # Directo a afiliarse
            else:
                messages.error(request, 'Hubo un error al procesar tu upgrade.')
        else:
            messages.warning(request, 'Debes aceptar los términos para continuar.')

    # GET - Mostrar página de confirmación
    context = {
        'pedidos_realizados': Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').count(),
        'es_referido': request.user.referido_por is not None,
        'referido_por': request.user.referido_por
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


# ======== MANEJADOR PARA GOOGLE OAUTH ========
def custom_google_signup_handler(request, socialaccount):
    """
    Manejador personalizado para registro via Google OAuth.
    Determina si viene de link de afiliado o registro directo.
    """
    user = socialaccount.user

    # Detectar si viene de enlace de afiliado (guardado en sesión)
    referido_por_username = request.session.get('ref_username')

    if referido_por_username:
        try:
            from .models import CustomUser
            referido_por = CustomUser.objects.get(username=referido_por_username)
            if referido_por.es_vendedor():
                # Cliente vía afiliado
                user.tipo_usuario = 'COMPRADOR'
                user.origen_registro = 'AFILIADO'
                user.referido_por = referido_por
                user.fecha_referido = timezone.now()

                # Limpiar la sesión
                del request.session['ref_username']

                # Mensaje para mostrar después del login
                request.session['google_signup_info'] = {
                    'referido_por': referido_por.nombre,
                    'es_afiliado': True
                }
            else:
                # Registro directo como vendedor
                user.tipo_usuario = 'VENDEDOR'
                user.origen_registro = 'GOOGLE'
                user.fecha_upgrade_vendedor = timezone.now()
        except Exception:
            # Registro directo como vendedor
            user.tipo_usuario = 'VENDEDOR'
            user.origen_registro = 'GOOGLE'
            user.fecha_upgrade_vendedor = timezone.now()
    else:
        # Registro directo como vendedor (sin referencia)
        user.tipo_usuario = 'VENDEDOR'
        user.origen_registro = 'GOOGLE'
        user.fecha_upgrade_vendedor = timezone.now()

    user.save()


# ======== LANDING PAGE PRINCIPAL ========
def landing_page(request):
    """
    Vista de la landing page principal que se muestra a TODOS los usuarios.
    Ya no redirige automáticamente a usuarios logueados.
    """
    # Estadísticas básicas para mostrar en la landing (datos reales)
    context = {
        'total_productos': Producto.objects.filter(activo=True).count(),
        'productos_fisicos': Producto.objects.filter(activo=True, tipo_producto='FISICO').count(),
        'productos_digitales': Producto.objects.filter(activo=True, tipo_producto='DIGITAL').count(),

        # Configuración de la plataforma desde settings
        'platform_name': getattr(settings, 'PLATFORM_NAME', 'AfiliaMax'),
        'platform_tagline': getattr(settings, 'PLATFORM_TAGLINE', 'Tu plataforma de afiliación'),
        'platform_description': getattr(settings, 'PLATFORM_DESCRIPTION', 'Genera ingresos por comisiones'),
        'default_commission': getattr(settings, 'DEFAULT_COMMISSION_RATE', 15),
        'min_commission': getattr(settings, 'MIN_COMMISSION_RATE', 10),
        'max_commission': getattr(settings, 'MAX_COMMISSION_RATE', 25),
    }

    return render(request, 'landing/landing_page.html', context)


@login_required
def comprador_dashboard(request):
    """
    Dashboard para compradores - interface simple enfocada en compras
    """
    context = {
        'user': request.user,
        'pedidos_count': Pedido.objects.filter(usuario=request.user).exclude(estado='PENDIENTE').count(),
        'pedidos_cancelados': Pedido.objects.filter(usuario=request.user, estado='CANCELADO').count(),
        'pedidos_reembolsos': Pedido.objects.filter(usuario=request.user, estado='REEMBOLSO').count(),

        # Últimos pedidos para mostrar en "Mis compras"
        'ultimos_pedidos': Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').order_by('-fecha_creacion')[:5],

        # Items en carrito actual
        'items_carrito': 0,
    }

    # Calcular items en carrito
    try:
        carrito = Pedido.objects.get(usuario=request.user, estado='PENDIENTE')
        context['items_carrito'] = carrito.items.count()
    except Pedido.DoesNotExist:
        pass

    return render(request, 'usuarios/comprador_dashboard.html', context)


@login_required
def ir_a_compras(request):
    """
    Redirige al dashboard de compras. Requiere login.
    """
    return redirect('usuarios:comprador_dashboard')


@login_required
def ir_a_negocio(request):
    """
    Redirige al dashboard de negocio (home.html). Requiere login.
    """
    return redirect('usuarios:home')