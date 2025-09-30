from django.contrib import admin
from .models import Producto


class ProductoAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista del admin
    list_display = ('nombre', 'precio', 'tipo_producto', 'vendedor')

    # Filtros en la barra lateral
    list_filter = ('tipo_producto',)

    # Campo por el que se puede buscar
    search_fields = ('nombre', 'descripcion')

    # Orden por defecto de la lista
    ordering = ('-id',)

    # Campos editables en el formulario
    fields = ('nombre', 'descripcion', 'precio', 'imagen', 'tipo_producto', 'vendedor')

    # Campos de solo lectura (opcional)
    readonly_fields = ('vendedor',)


# Registrar el modelo con la configuración personalizada
admin.site.register(Producto, ProductoAdmin)