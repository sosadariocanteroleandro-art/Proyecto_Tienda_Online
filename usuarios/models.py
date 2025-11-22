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

    # ======= CAMPOS PARA AFILIACIÓN =======
    # Datos personales para afiliación
    tipo_persona = models.CharField(
        max_length=20,
        choices=[('fisica', 'Persona Física'), ('juridica', 'Persona Jurídica')],
        blank=True,
        verbose_name='Tipo de Persona'
    )

    documento_identidad = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Documento de Identidad'
    )

    pais_residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='País de Residencia'
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )

    # Datos opcionales para mejorar el perfil de afiliado
    experiencia_marketing = models.TextField(
        blank=True,
        verbose_name='Experiencia en Marketing',
        help_text='Describe tu experiencia previa en marketing digital o ventas (opcional)'
    )

    biografia_afiliado = models.TextField(
        blank=True,
        verbose_name='Biografía/Presentación',
        help_text='Cuéntanos sobre ti y por qué quieres ser afiliado (opcional)'
    )

    canales_promocion = models.TextField(
        blank=True,
        verbose_name='Canales de Promoción',
        help_text='¿Dónde planeas promocionar? (redes sociales, blog, email, etc.) - opcional'
    )

    areas_interes = models.TextField(
        blank=True,
        verbose_name='Áreas de Interés',
        help_text='¿Qué tipo de productos te interesa promocionar? (opcional)'
    )

    # Control de acceso a herramientas de afiliación
    datos_afiliacion_completos = models.BooleanField(
        default=False,
        verbose_name='Datos de Afiliación Completos',
        help_text='Indica si completó los datos mínimos para poder afiliarse a productos'
    )

    fecha_completado_perfil = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Completado Perfil Afiliación'
    )
    # =====================================

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

    # ======= NUEVOS MÉTODOS PARA AFILIACIÓN =======
    def puede_afiliarse_a_productos(self):
        """
        Verifica si puede afiliarse a productos.
        Requiere: ser vendedor + tener datos completos
        """
        return self.es_vendedor() and self.datos_afiliacion_completos

    def completar_datos_afiliacion(self):
        """
        Marca los datos de afiliación como completos si cumple requisitos mínimos
        """
        # Campos obligatorios para afiliación
        campos_obligatorios = [
            self.tipo_persona,
            self.documento_identidad,
            self.pais_residencia,
        ]

        if all(campo for campo in campos_obligatorios):
            self.datos_afiliacion_completos = True
            if not self.fecha_completado_perfil:
                self.fecha_completado_perfil = timezone.now()
            return True
        else:
            self.datos_afiliacion_completos = False
            return False

    def get_campos_faltantes_afiliacion(self):
        """
        Retorna lista de campos obligatorios faltantes para afiliación
        """
        campos_faltantes = []

        if not self.tipo_persona:
            campos_faltantes.append('Tipo de Persona')
        if not self.documento_identidad:
            campos_faltantes.append('Documento de Identidad')
        if not self.pais_residencia:
            campos_faltantes.append('País de Residencia')

        return campos_faltantes

    def get_porcentaje_completitud_perfil(self):
        """
        Retorna porcentaje de completitud del perfil de afiliación (0-100)
        """
        campos_totales = [
            self.tipo_persona,
            self.documento_identidad,
            self.pais_residencia,
            self.telefono,
            self.biografia_afiliado,
            self.canales_promocion,
        ]

        campos_completos = sum(1 for campo in campos_totales if campo)
        return int((campos_completos / len(campos_totales)) * 100)

    # ====================================================

    def puede_afiliarse(self):
        """Solo vendedores pueden afiliarse a productos (método legacy)"""
        return self.puede_afiliarse_a_productos()

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

    # usuarios/models.py - AGREGAR ESTOS CAMPOS AL FINAL DE LA CLASE CustomUser

    # ================ CAMPOS PARA GESTIÓN DE SALDO Y RETIROS ================
    # Saldo y comisiones
    saldo_disponible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Disponible para Retiro"
    )

    saldo_retirado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Retirado"
    )

    retiro_minimo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=50000,
        verbose_name="Retiro Mínimo (Gs)"
    )

    # Datos bancarios para retiros
    tipo_retiro = models.CharField(
        max_length=20,
        choices=[
            ('banco', 'Transferencia Bancaria'),
            ('tigo_money', 'Tigo Money'),
            ('personal_pay', 'Personal Pay'),
            ('weepay', 'WeePayy'),
        ],
        blank=True,
        verbose_name="Método de Retiro Preferido"
    )

    # Para transferencias bancarias
    banco_nombre = models.CharField(max_length=100, blank=True, verbose_name="Nombre del Banco")
    numero_cuenta = models.CharField(max_length=50, blank=True, verbose_name="Número de Cuenta")
    tipo_cuenta = models.CharField(
        max_length=20,
        choices=[
            ('corriente', 'Corriente'),
            ('ahorro', 'Ahorro'),
        ],
        blank=True,
        verbose_name="Tipo de Cuenta"
    )
    titular_cuenta = models.CharField(max_length=100, blank=True, verbose_name="Titular de la Cuenta")

    # Para billeteras digitales
    numero_celular_retiro = models.CharField(max_length=20, blank=True, verbose_name="Celular para Retiro")
    nombre_titular_billetera = models.CharField(max_length=100, blank=True, verbose_name="Nombre del Titular")

    # Control de retiros
    datos_retiro_completos = models.BooleanField(default=False, verbose_name="Datos de Retiro Completos")
    retiros_pendientes = models.BooleanField(default=False, verbose_name="Tiene Retiros Pendientes")
    fecha_ultimo_retiro = models.DateTimeField(blank=True, null=True, verbose_name="Último Retiro")

    # MÉTODOS ADICIONALES PARA AGREGAR AL FINAL DE LA CLASE
    def puede_solicitar_retiro(self):
        """Verifica si el usuario puede solicitar un retiro"""
        return (
                self.es_vendedor() and
                self.datos_retiro_completos and
                self.saldo_disponible >= self.retiro_minimo and
                not self.retiros_pendientes
        )

    def saldo_total_comisiones(self):
        """Calcula el saldo total incluyendo disponible y retirado"""
        return self.saldo_disponible + self.saldo_retirado

    def get_tipo_retiro_display_custom(self):
        """Display personalizado para tipo de retiro"""
        tipos = {
            'banco': '🏦 Transferencia Bancaria',
            'tigo_money': '📱 Tigo Money',
            'personal_pay': '📱 Personal Pay',
            'weepay': '📱 WeePayy',
        }
        return tipos.get(self.tipo_retiro, 'No configurado')

# NOTA: Pedido e ItemPedido están en productos.models, no aquí