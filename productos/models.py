from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from Tienda.settings import AUTH_USER_MODEL


class Producto(models.Model):
    # La tupla CHOICES define las opciones para el campo.
    TIPO_PRODUCTO_CHOICES = (
        ('FISICO', 'Físico'),
        ('DIGITAL', 'Digital'),
    )

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    descripcion = models.TextField(verbose_name="Descripción")
    imagen = models.URLField(max_length=500, verbose_name="URL de Imagen", null=True, blank=True)
    afiliados = models.ManyToManyField(AUTH_USER_MODEL, related_name='productos_afiliados', blank=True)
    # Nuevo campo para clasificar el producto
    tipo_producto = models.CharField(
        max_length=7,
        choices=TIPO_PRODUCTO_CHOICES,
        default='FISICO',
        verbose_name="Tipo de Producto"
    )

    def __str__(self):
        # Esta función define la representación en string del objeto,
        # útil para el panel de administración de Django.
        return self.nombre
