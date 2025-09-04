from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Producto  # ← Agrega Producto aquí
from django.utils.translation import gettext_lazy as _


# Registra tu modelo CustomUser en el admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Campos a mostrar en la lista
    list_display = ('username', 'email', 'nombre', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'nombre', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Campos para el formulario de edición
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información personal'), {'fields': ('nombre', 'first_name', 'last_name', 'email')}),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    # Para el formulario de CREACIÓN
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nombre', 'password1', 'password2'),
        }),
    )

    # Configuración adicional
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('date_joined', 'last_login')


# 🚨 AÑADE ESTO PARA REGISTRAR EL MODELO PRODUCTO
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'stock')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_creacion',)
    list_editable = ('precio', 'stock')  # Puedes editar directamente en la lista

    # Campos para el formulario
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion')
        }),
        ('Precio e Inventario', {
            'fields': ('precio', 'stock', 'imagen')
        }),
    )