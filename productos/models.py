from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = (
        ('FISICO', 'Físico'),
        ('DIGITAL', 'Digital'),
    )

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    descripcion = models.TextField(verbose_name="Descripción")

    imagen = models.ImageField(
        upload_to='productos/',
        verbose_name="Imagen del Producto",
        null=True,
        blank=True,
        help_text="Sube una imagen del producto"
    )

    tipo_producto = models.CharField(
        max_length=7,
        choices=TIPO_PRODUCTO_CHOICES,
        default='FISICO',
        verbose_name="Tipo de Producto"
    )

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="productos_creados",
        null=True,
        blank=True
    )

    afiliados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='productos_afiliados',
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    activo = models.BooleanField(default=True, verbose_name="Producto Activo")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']


class PerfilVendedor(models.Model):
    """
    Perfil extendido para vendedores/afiliados.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_vendedor',
        verbose_name="Usuario"
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name="URL Personalizada",
        help_text="Ej: juan-perez → tutienda.com/vendedor/juan-perez"
    )

    nombre_tienda = models.CharField(
        max_length=100,
        default="Mi Tienda",
        verbose_name="Nombre de la Tienda"
    )

    descripcion = models.TextField(
        default="¡Bienvenido a mi tienda!",
        verbose_name="Descripción",
        help_text="Cuéntale a tus clientes sobre ti"
    )

    foto_perfil = models.ImageField(
        upload_to='vendedores/perfiles/',
        blank=True,
        null=True,
        verbose_name="Foto de Perfil"
    )

    banner = models.ImageField(
        upload_to='vendedores/banners/',
        blank=True,
        null=True,
        verbose_name="Banner de Portada"
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="WhatsApp",
        help_text="Ej: +5491123456789"
    )

    email_contacto = models.EmailField(
        blank=True,
        verbose_name="Email de Contacto"
    )

    facebook = models.URLField(
        blank=True,
        verbose_name="Facebook"
    )

    instagram = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Instagram",
        help_text="Solo el nombre de usuario (sin @)"
    )

    color_tema = models.CharField(
        max_length=7,
        default="#667eea",
        verbose_name="Color del Tema",
        help_text="Color principal de tu página"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Perfil Activo"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    def save(self, *args, **kwargs):
        """Genera automáticamente el slug si no existe"""
        if not self.slug:
            base_slug = slugify(self.usuario.username)
            slug = base_slug
            counter = 1

            while PerfilVendedor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_tienda} (@{self.usuario.username})"

    class Meta:
        verbose_name = "Perfil de Vendedor"
        verbose_name_plural = "Perfiles de Vendedores"
        ordering = ['-fecha_creacion']


class ProductoVendedor(models.Model):
    """
    Relación entre un vendedor y un producto que promociona.
    """
    vendedor = models.ForeignKey(
        PerfilVendedor,
        on_delete=models.CASCADE,
        related_name='productos_promocionados',
        verbose_name="Vendedor"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='vendedores_promocionando',
        verbose_name="Producto"
    )

    descripcion_personalizada = models.TextField(
        verbose_name="Tu Descripción del Producto",
        help_text="Escribe tu propia descripción de venta"
    )

    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Tu Precio de Venta",
        help_text="Puede incluir tu ganancia/comisión"
    )

    mensaje_especial = models.TextField(
        blank=True,
        verbose_name="Mensaje Especial",
        help_text="¿Por qué deberían comprarte a ti?"
    )

    beneficios_extra = models.TextField(
        blank=True,
        verbose_name="Beneficios Adicionales",
        help_text="Lista de beneficios que ofreces"
    )

    vistas = models.IntegerField(
        default=0,
        verbose_name="Número de Vistas"
    )

    clicks_whatsapp = models.IntegerField(
        default=0,
        verbose_name="Clicks en WhatsApp"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Publicación Activa"
    )

    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Publicación"
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    def get_url_completa(self):
        """Retorna la URL completa de la página del vendedor"""
        from django.urls import reverse
        return reverse('pagina_vendedor', kwargs={
            'slug': self.vendedor.slug,
            'producto_id': self.producto.id
        })

    def __str__(self):
        return f"{self.vendedor.nombre_tienda} → {self.producto.nombre}"

    class Meta:
        verbose_name = "Producto Promocionado"
        verbose_name_plural = "Productos Promocionados"
        unique_together = ('vendedor', 'producto')
        ordering = ['-fecha_publicacion']


# ============================================================================
# 🛒 MODELOS PARA SISTEMA DE PEDIDOS Y VENTAS
# ============================================================================

class Pedido(models.Model):
    """
    Modelo para registrar los pedidos/compras de los clientes
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente de Confirmación'),
        ('CONFIRMADO', 'Confirmado'),
        ('PROCESANDO', 'En Proceso'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )

    METODO_PAGO_CHOICES = (
        ('CONTRA_ENTREGA', 'Pago contra entrega'),
        ('TRANSFERENCIA', 'Transferencia bancaria'),
        ('TARJETA', 'Tarjeta de crédito/débito'),
    )

    # Información del pedido
    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    # Producto
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='pedidos')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Cliente
    nombre_cliente = models.CharField(max_length=200, verbose_name='Nombre completo')
    email_cliente = models.EmailField(verbose_name='Email')
    telefono_cliente = models.CharField(max_length=20, verbose_name='Teléfono')
    direccion_entrega = models.TextField(verbose_name='Dirección de entrega', blank=True)
    ciudad = models.CharField(max_length=100, blank=True)

    # Método de pago
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    comprobante_pago = models.ImageField(
        upload_to='comprobantes/',
        null=True,
        blank=True,
        verbose_name='Comprobante de pago'
    )

    # Sistema de afiliados/referencia
    codigo_referencia = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Código de referencia del afiliado'
    )
    vendedor_referido = models.ForeignKey(
        PerfilVendedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_referidas',
        verbose_name='Vendedor que refirió'
    )

    # Comisión
    comision_afiliado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Comisión del afiliado'
    )
    porcentaje_comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='% de comisión'
    )
    comision_pagada = models.BooleanField(default=False, verbose_name='Comisión pagada')

    # Notas
    notas_cliente = models.TextField(blank=True, verbose_name='Notas del cliente')
    notas_admin = models.TextField(blank=True, verbose_name='Notas administrativas')

    # Tracking
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Generar número de pedido único
            fecha = timezone.now()
            prefijo = fecha.strftime('%Y%m%d')
            ultimo_pedido = Pedido.objects.filter(
                numero_pedido__startswith=prefijo
            ).order_by('-numero_pedido').first()

            if ultimo_pedido:
                ultimo_numero = int(ultimo_pedido.numero_pedido[-4:])
                nuevo_numero = ultimo_numero + 1
            else:
                nuevo_numero = 1

            self.numero_pedido = f"{prefijo}{nuevo_numero:04d}"

        # Calcular total
        self.total = self.precio_unitario * self.cantidad

        # Calcular comisión si hay vendedor referido
        if self.vendedor_referido and not self.comision_afiliado:
            self.comision_afiliado = (self.total * self.porcentaje_comision) / 100

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_pedido} - {self.nombre_cliente} - {self.producto.nombre}"


class ConfiguracionPagos(models.Model):
    """
    Configuración de métodos de pago y comisiones
    """
    # Mercado Pago
    mercadopago_public_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Public Key de Mercado Pago'
    )
    mercadopago_access_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Access Token de Mercado Pago'
    )

    # Configuración de comisiones
    comision_afiliado_default = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='% Comisión por defecto para afiliados'
    )

    # Información bancaria
    banco_nombre = models.CharField(max_length=100, blank=True)
    banco_cuenta = models.CharField(max_length=50, blank=True)
    banco_titular = models.CharField(max_length=200, blank=True)
    banco_cedula = models.CharField(max_length=20, blank=True)

    # Configuración general
    requiere_direccion_digital = models.BooleanField(
        default=False,
        verbose_name='Requerir dirección para productos digitales'
    )

    class Meta:
        verbose_name = 'Configuración de Pagos'
        verbose_name_plural = 'Configuración de Pagos'

    def __str__(self):
        return 'Configuración de Pagos'