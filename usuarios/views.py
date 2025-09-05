from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm


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
