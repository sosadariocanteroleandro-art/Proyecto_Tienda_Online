from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Producto


def registro_usuario(request):
    """
    Vista para registrar un nuevo usuario.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Redirige al usuario al login después de un registro exitoso
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
            return redirect('usuarios:home')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            form = AuthenticationForm(request.POST)  # ← Formulario con datos previos
    else:
        form = AuthenticationForm()  # ← Formulario vacío para GET

    return render(request, 'usuarios/login.html', {'form': form})  # ← ¡PASA EL FORMULARIO!


def home(request):
    """
    Vista de la página principal que muestra los productos.
    """
    # Obtenemos todos los productos de la base de datos
    productos = Producto.objects.all()

    # Pasamos los productos al contexto de la plantilla
    context = {
        'productos': productos
    }
    return render(request, 'usuarios/home.html', context)


def logout_view(request):
    """
    Vista para cerrar la sesión.
    """
    logout(request)
    return redirect('usuarios:login')  # ← Cambiado a 'usuarios:login'