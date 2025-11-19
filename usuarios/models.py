from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado con sistema de roles y referencia de afiliados.
    """
    # Tipos de usuario
    TIPO_USUARIO_CHOICES = (
        ('COMPRADOR', 'Comprador'),
        ('VENDEDOR', 'Vendedor/Afiliado'),
    )

    # Origen de registro (NUEVO)
    ORIGEN_REGISTRO_CHOICES = (
        ('DIRECTO', 'Registro directo'),
        ('AFILIADO', 'Vía link de afiliado'),
        ('GOOGLE', 'Google OAuth'),
        ('ADMIN', 'Creado por admin'),
    )

    nombre = models.CharField(max_length=100)
    email = models.EmailField(
        _('correo electrónico'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        }
    )

    # Campo para tipo de usuario
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default='COMPRADOR',
        verbose_name='Tipo de Usuario'
    )

    # ======= CAMPOS PARA ORIGEN Y REFERENCIA =======
    # Origen de registro
    origen_registro = models.CharField(
        max_length=10,
        choices=ORIGEN_REGISTRO_CHOICES,
        default='DIRECTO',
        verbose_name='Origen de Registro'
    )

    # Afiliado que lo refirió
    referido_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_referidos',
        verbose_name='Referido por'
    )

    # Fecha de referencia
    fecha_referido = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Referido',
        help_text='Fecha cuando se registró vía link de afiliado'
    )
    # ===============================================

    # Fecha de upgrade a vendedor
    fecha_upgrade_vendedor = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Upgrade a Vendedor'
    )

    # Campo para tracking de comisiones
    comisiones_ganadas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Comisiones Totales Ganadas'
    )

    # Campo para indicar si puede crear productos
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

    # MÉTODOS PARA GESTIÓN DE ROLES Y ORIGEN

    def es_comprador(self):
        """Verifica si el usuario es solo comprador"""
        return self.tipo_usuario == 'COMPRADOR'

    def es_vendedor(self):
        """Verifica si el usuario es vendedor/afiliado"""
        return self.tipo_usuario == 'VENDEDOR' or self.is_superuser

    def puede_comprar(self):
        """Cualquier usuario autenticado puede comprar"""
        return self.is_authenticated

    # ======= NUEVOS MÉTODOS PARA ORIGEN Y REFERENCIA =======
    def es_comprador_normal(self):
        """Comprador registrado directamente o por Google (sin afiliado)"""
        return (self.tipo_usuario == 'COMPRADOR' and
                self.origen_registro in ['DIRECTO', 'GOOGLE'])

    def es_comprador_via_afiliado(self):
        """Comprador que llegó vía link de afiliado"""
        return (self.tipo_usuario == 'COMPRADOR' and
                self.origen_registro == 'AFILIADO')

    def debe_mostrar_promos_vendedor(self):
        """Determina si debe ver promociones para ser vendedor"""
        return self.es_comprador_via_afiliado()

    def puede_ver_panel_afiliacion(self):
        """Determina si puede ver el panel completo de afiliación"""
        return self.es_vendedor()

    # ====================================================

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

# NOTA: Pedido e ItemPedido están en productos.models, no aquí