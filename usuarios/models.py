from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado.
    """
    nombre = models.CharField(max_length=100)
    email = models.EmailField(
        _('correo electrónico'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        }
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        verbose_name='user permissions',
    )

    REQUIRED_FIELDS = ['email', 'nombre']

    def __str__(self):
        return self.username


class Pedido(models.Model):
    """
    Modelo para pedidos
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='pedidos_usuario'
    )
    afiliado_referido = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_referidas'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    comision_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Pedido {self.id} - {self.usuario.username}"


class ItemPedido(models.Model):
    """
    Modelo para los items dentro de un pedido
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'
    )
    # Referencia al modelo Producto de la app productos
    producto = models.ForeignKey(
        'productos.Producto',  # ← Referencia al Producto de la app productos
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"