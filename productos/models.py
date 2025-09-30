from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = (
        ('FISICO', 'Físico'),
        ('DIGITAL', 'Digital'),
    )

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    descripcion = models.TextField(verbose_name="Descripción")

    # 🔹 Cambio: ImageField en lugar de URLField para subir imágenes directamente
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

    # 🔹 Quién creó el producto
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="productos_creados",
        null=True,
        blank=True
    )

    # 🔹 Usuarios afiliados al producto
    afiliados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='productos_afiliados',
        blank=True
    )

    # 🔹 Campos adicionales útiles
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    activo = models.BooleanField(default=True, verbose_name="Producto Activo")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']  # Ordenar por más recientes primero


# ============================================================================
# 🆕 NUEVOS MODELOS PARA SISTEMA DE VENDEDORES/AFILIADOS
# ============================================================================

class PerfilVendedor(models.Model):
    """
    Perfil extendido para vendedores/afiliados.
    Cada usuario puede tener su página personalizada para promocionar productos.
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📝 INFORMACIÓN DE LA TIENDA (Editable por el vendedor)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📞 INFORMACIÓN DE CONTACTO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎨 PERSONALIZACIÓN VISUAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    color_tema = models.CharField(
        max_length=7,
        default="#667eea",
        verbose_name="Color del Tema",
        help_text="Color principal de tu página"
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📊 ESTADÍSTICAS Y CONTROL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

            # Asegurar que el slug sea único
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
    El vendedor puede personalizar la descripción, precio y mensaje.
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ✏️ CONTENIDO PERSONALIZABLE POR EL VENDEDOR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        help_text="¿Por qué deberían comprarte a ti? Ej: Envío gratis, garantía extendida, etc."
    )

    beneficios_extra = models.TextField(
        blank=True,
        verbose_name="Beneficios Adicionales",
        help_text="Lista de beneficios que ofreces (separados por líneas)"
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📊 ESTADÍSTICAS Y CONTROL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    vistas = models.IntegerField(
        default=0,
        verbose_name="Número de Vistas",
        help_text="Cuántas personas visitaron esta página"
    )

    clicks_whatsapp = models.IntegerField(
        default=0,
        verbose_name="Clicks en WhatsApp",
        help_text="Cuántas veces clickearon tu WhatsApp"
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
        """Retorna la URL completa de la página del vendedor con este producto"""
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
        unique_together = ('vendedor', 'producto')  # Un vendedor no puede promocionar el mismo producto dos veces
        ordering = ['-fecha_publicacion']