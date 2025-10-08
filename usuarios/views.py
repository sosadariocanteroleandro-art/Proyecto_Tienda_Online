from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Pedido  # ← Solo Pedido, Producto viene de productos
from productos.models import Producto  # ← Importar desde productos

def registro_usuario(request):
    """
    Vista para registrar un nuevo usuario.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
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
            return redirect('usuarios:home')  # Esto puede cambiar después según la app de productos
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
    Vista del Dashboard principal
    """
    context = {}

    if request.user.is_authenticated:
        # Estadísticas del usuario
        context['productos_afiliados_count'] = request.user.productos_afiliados.count()
        context['pedidos_count'] = Pedido.objects.filter(
            usuario=request.user
        ).exclude(estado='PENDIENTE').count()

        # Comisiones totales
        ventas_como_afiliado = Pedido.objects.filter(
            afiliado_referido=request.user
        ).exclude(estado='PENDIENTE')
        context['comisiones_totales'] = sum(v.comision_total for v in ventas_como_afiliado)

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

    return render(request, 'usuarios/home.html', context)