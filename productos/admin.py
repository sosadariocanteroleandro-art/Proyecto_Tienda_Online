from django.contrib import admin
from .models import Producto

class ProductoAdmin(admin.ModelAdmin):
    #campos que se mostraran en la lista del admin
    list_display = ('nombre', 'precio', 'tipo producto', 'stock')

    #filtros en la barra lateral
    list_filter = ('tipo_producto',)

    #campo por el que se puede buscar
    search_fields = ('nombre', 'descripcion')

    #orden por defecto de la lista
    ordering = ('-nombre',)

    #campos editables en el formulario
    fields = ('nombre', 'descripcion', 'precio', 'stock', 'imagen', 'tipo_producto')

