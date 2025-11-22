from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal


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

    stock = models.IntegerField(
        default=0,
        verbose_name="Stock Disponible",
        help_text="Cantidad disponible en inventario. Los productos digitales tienen stock ilimitado"
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
        blank=True,
        verbose_name="Afiliados"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    activo = models.BooleanField(default=True, verbose_name="Producto Activo")

    def __str__(self):
        return self.nombre

    def tiene_stock(self, cantidad=1):
        """Verifica si hay stock suficiente"""
        if self.tipo_producto == 'DIGITAL':
            return True
        return self.stock >= cantidad

    def reducir_stock(self, cantidad):
        """Reduce el stock después de una venta"""
        if self.tipo_producto == 'FISICO' and self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        return False

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']


# ============================================================================
# 🛒 MODELOS PARA SISTEMA DE CARRITO Y PEDIDOS CON STOCK
# ============================================================================

class Pedido(models.Model):
    """
    Modelo para pedidos que puede contener múltiples productos (carrito)
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),  # Carrito activo
        ('CONFIRMADO', 'Confirmado'),
        ('PROCESANDO', 'En Proceso'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )

    # Información básica
    numero_pedido = models.CharField(max_length=20, unique=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name='Usuario'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name='Estado'
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total'
    )

    # Información de entrega (se llena al confirmar)
    nombre_completo = models.CharField(max_length=200, blank=True, verbose_name='Nombre completo')
    email = models.EmailField(blank=True, verbose_name='Email')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    direccion_envio = models.TextField(blank=True, verbose_name='Dirección de entrega')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')

    METODO_PAGO_CHOICES = (
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CONTRA_ENTREGA', 'Pago en Puerta'),
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        blank=True,
        null=True,
        verbose_name='Método de Pago'
    )

    comprobante_pago = models.ImageField(
        upload_to='comprobantes/',
        null=True,
        blank=True,
        verbose_name='Comprobante de Pago',
        help_text='Imagen del comprobante de transferencia'
    )

    # Sistema de referidos - SIMPLIFICADO
    afiliado_referido = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_como_afiliado',
        verbose_name='Afiliado que refirió'
    )

    # ✅ CAMBIO CRÍTICO: comision_total como campo normal (no property)
    comision_total_field = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Comisión total'
    )

    porcentaje_comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='% de comisión'
    )

    comision_pagada = models.BooleanField(
        default=False,
        verbose_name='Comisión pagada'
    )

    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    fecha_confirmacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de confirmación')

    # Notas
    notas = models.TextField(blank=True, verbose_name='Notas del cliente')

    # ✅ PROPERTY para mantener compatibilidad con el código existente
    @property
    def comision_total(self):
        """Calcula y devuelve la comisión total del pedido"""
        return self.comision_total_field

    @property
    def productos_lista(self):
        """Devuelve una lista legible de los productos del pedido"""
        items = self.items.all()
        if not items:
            return "Sin productos"

        productos = []
        for item in items:
            productos.append(f"{item.producto.nombre} (x{item.cantidad})")

        return " | ".join(productos)

    def puede_cambiar_estado(self, nuevo_estado):
        """Verifica si el pedido puede cambiar al nuevo estado"""
        estados_validos = {
            'PENDIENTE': ['CONFIRMADO', 'CANCELADO'],
            'CONFIRMADO': ['PROCESANDO', 'CANCELADO'],
            'PROCESANDO': ['ENVIADO', 'CANCELADO'],
            'ENVIADO': ['ENTREGADO'],
            'ENTREGADO': [],  # Estado final
            'CANCELADO': []  # Estado final
        }

        return nuevo_estado in estados_validos.get(self.estado, [])

    def __str__(self):
        if self.numero_pedido:
            return f"Pedido #{self.numero_pedido} - {self.usuario.username}"
        return f"Carrito de {self.usuario.username}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

    def save(self, *args, **kwargs):
        # Generar número de pedido solo cuando se confirma (no para carrito)
        if not self.numero_pedido and self.estado != 'PENDIENTE':
            fecha = timezone.now()
            prefijo = fecha.strftime('%Y%m%d')
            ultimo_pedido = Pedido.objects.filter(
                numero_pedido__startswith=prefijo,
                numero_pedido__isnull=False  # Agregado: excluir nulos
            ).exclude(numero_pedido='').order_by('-numero_pedido').first()

            if ultimo_pedido:
                try:
                    ultimo_numero = int(ultimo_pedido.numero_pedido[-3:])
                    nuevo_numero = ultimo_numero + 1
                except:
                    nuevo_numero = 1
            else:
                nuevo_numero = 1

            self.numero_pedido = f"{prefijo}{nuevo_numero:03d}"

        super().save(*args, **kwargs)

        # CAMBIO CRÍTICO: Solo actualizar total si ya existe en BD
        if self.pk:
            self.actualizar_total()

    def actualizar_total(self):
        """Recalcula el total del pedido y la comisión"""
        total = sum(item.subtotal for item in self.items.all())

        # Calcular comisión si hay afiliado
        if self.afiliado_referido:
            porcentaje = Decimal(str(self.porcentaje_comision))
            comision = (total * porcentaje) / Decimal('100')
        else:
            comision = Decimal('0')

        if self.total != total or self.comision_total_field != comision:
            self.total = total
            # ✅ CAMBIO CRÍTICO: Usar el campo normal, no la property
            self.comision_total_field = comision
            Pedido.objects.filter(pk=self.pk).update(
                total=total,
                comision_total_field=comision  # ✅ Usar el campo correcto
            )

            # productos/models.py - AGREGAR ESTOS CAMPOS AL MODELO PRODUCTO

            # ================ CAMPOS PARA COMISIONES (AGREGAR AL MODELO PRODUCTO) ================

            # Sistema de comisiones por producto
            comision_afiliado = models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=15.00,  # 15% por defecto
                verbose_name="Comisión para Afiliados (%)",
                help_text="Porcentaje de comisión que recibirán los afiliados por vender este producto"
            )

            comision_minima = models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=5.00,
                verbose_name="Comisión Mínima (%)"
            )

            comision_maxima = models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=50.00,
                verbose_name="Comisión Máxima (%)"
            )

            # Control de comisiones
            permite_modificar_comision = models.BooleanField(
                default=True,
                verbose_name="Permite Modificar Comisión",
                help_text="Permite que los administradores modifiquen la comisión de este producto"
            )

            comision_especial_activa = models.BooleanField(
                default=False,
                verbose_name="Comisión Especial Activa",
                help_text="Indica si hay una comisión especial temporal para este producto"
            )

            fecha_inicio_comision_especial = models.DateTimeField(
                null=True,
                blank=True,
                verbose_name="Inicio Comisión Especial"
            )

            fecha_fin_comision_especial = models.DateTimeField(
                null=True,
                blank=True,
                verbose_name="Fin Comisión Especial"
            )

            comision_especial = models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=0.00,
                verbose_name="Comisión Especial (%)",
                help_text="Comisión temporal especial para promociones"
            )

            # MÉTODOS ADICIONALES PARA AGREGAR AL MODELO PRODUCTO
            def get_comision_actual(self):
                """
                Retorna la comisión actual del producto, considerando promociones especiales
                """
                from django.utils import timezone

                # Verificar si hay comisión especial activa
                if (self.comision_especial_activa and
                        self.fecha_inicio_comision_especial and
                        self.fecha_fin_comision_especial and
                        self.fecha_inicio_comision_especial <= timezone.now() <= self.fecha_fin_comision_especial):
                    return self.comision_especial

                return self.comision_afiliado

            def calcular_comision_monto(self, precio_venta=None):
                """
                Calcula el monto de comisión en guaraníes para un precio de venta
                """
                precio = precio_venta or self.precio
                comision_porcentaje = self.get_comision_actual()
                return (precio * comision_porcentaje) / 100

            def is_comision_especial_vigente(self):
                """
                Verifica si la comisión especial está vigente
                """
                from django.utils import timezone

                if not self.comision_especial_activa:
                    return False

                if not self.fecha_inicio_comision_especial or not self.fecha_fin_comision_especial:
                    return False

                now = timezone.now()
                return self.fecha_inicio_comision_especial <= now <= self.fecha_fin_comision_especial

            def get_comision_display(self):
                """
                Retorna el display formateado de la comisión
                """
                if self.is_comision_especial_vigente():
                    return f"{self.comision_especial}% (ESPECIAL)"
                return f"{self.comision_afiliado}%"

            class Meta:
                verbose_name = "Producto"
                verbose_name_plural = "Productos"
                ordering = ['-fecha_creacion']


class ItemPedido(models.Model):
    """
    Cada producto dentro de un pedido
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='items_pedido',
        verbose_name='Producto'
    )

    cantidad = models.IntegerField(default=1, verbose_name='Cantidad')

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario'
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Subtotal'
    )

    fecha_agregado = models.DateTimeField(auto_now_add=True, verbose_name='Fecha agregado')

    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'
        unique_together = ('pedido', 'producto')

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
        self.pedido.actualizar_total()

    def delete(self, *args, **kwargs):
        pedido = self.pedido
        super().delete(*args, **kwargs)
        pedido.actualizar_total()

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"


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