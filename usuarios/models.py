from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado con sistema de roles dinámicos.
    """
    # Tipos de usuario
    TIPO_USUARIO_CHOICES = (
        ('COMPRADOR', 'Comprador'),
        ('VENDEDOR', 'Vendedor/Afiliado'),
    )

    nombre = models.CharField(max_length=100)
    email = models.EmailField(
        _('correo electrónico'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        }
    )

    # Campo para tipo de usuario (NUEVO)
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default='COMPRADOR',
        verbose_name='Tipo de Usuario'
    )

    # Fecha de upgrade a vendedor (NUEVO)
    fecha_upgrade_vendedor = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Upgrade a Vendedor'
    )

    # Campo para tracking de comisiones (NUEVO)
    comisiones_ganadas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Comisiones Totales Ganadas'
    )

    # Campo para indicar si puede crear productos (NUEVO)
    puede_crear_productos = models.BooleanField(
        default=False,
        verbose_name='Puede Crear Productos'
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
        return f"{self.username} ({self.get_tipo_usuario_display()})"

    # MÉTODOS PARA GESTIÓN DE ROLES

    def es_comprador(self):
        """Verifica si el usuario es solo comprador"""
        return self.tipo_usuario == 'COMPRADOR'

    def es_vendedor(self):
        """Verifica si el usuario es vendedor/afiliado"""
        return self.tipo_usuario == 'VENDEDOR' or self.is_superuser

    def puede_comprar(self):
        """Cualquier usuario autenticado puede comprar"""
        return self.is_authenticated

    def puede_afiliarse(self):
        """Solo vendedores pueden afiliarse a productos"""
        return self.es_vendedor()

    def upgrade_a_vendedor(self):
        """Convierte un comprador a vendedor"""
        if self.tipo_usuario == 'COMPRADOR':
            self.tipo_usuario = 'VENDEDOR'
            self.fecha_upgrade_vendedor = timezone.now()
            self.save()
            return True
        return False

    def obtener_productos_afiliados(self):
        """Obtiene productos a los que está afiliado (solo vendedores)"""
        if self.es_vendedor():
            return self.productos_afiliados.all()
        return []

    def obtener_productos_creados(self):
        """Obtiene productos creados (solo superusuarios)"""
        if self.is_superuser:
            return self.productos_creados.all()
        return []

    def puede_ver_panel_vendedor(self):
        """Determina si puede ver funcionalidades de vendedor"""
        return self.es_vendedor()

    def generar_codigo_referencia(self):
        """Genera código de referencia para afiliados"""
        if self.es_vendedor():
            return f"{self.username}_{self.id}"
        return None


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