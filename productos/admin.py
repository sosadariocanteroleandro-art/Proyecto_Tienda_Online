from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum
from django.contrib.admin import SimpleListFilter
from .models import Producto, Pedido, ItemPedido, ConfiguracionPagos
import csv
from django.http import HttpResponse


# ============================================================================
# 🎯 FILTROS PERSONALIZADOS
# ============================================================================

class MetodoPagoFilter(SimpleListFilter):
    title = 'Método de Pago'
    parameter_name = 'metodo_pago'

    def lookups(self, request, model_admin):
        return (
            ('CONTRA_ENTREGA', '💵 Contra Entrega'),
            ('TRANSFERENCIA', '🏦 Transferencia'),
            ('TARJETA', '💳 Tarjeta'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(metodo_pago=self.value())
        return queryset


class EstadoPedidoFilter(SimpleListFilter):
    title = 'Estado del Pedido'
    parameter_name = 'estado'

    def lookups(self, request, model_admin):
        return (
            ('PENDIENTE', '⏳ Pendiente'),
            ('CONFIRMADO', '✅ Confirmado'),
            ('PROCESANDO', '⚙️ Procesando'),
            ('ENVIADO', '🚚 Enviado'),
            ('ENTREGADO', '📦 Entregado'),
            ('CANCELADO', '❌ Cancelado'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estado=self.value())
        return queryset


class ComprobanteFilter(SimpleListFilter):
    title = 'Comprobante de Pago'
    parameter_name = 'tiene_comprobante'

    def lookups(self, request, model_admin):
        return (
            ('si', '✅ Con Comprobante'),
            ('no', '❌ Sin Comprobante'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.exclude(comprobante_pago='').exclude(comprobante_pago__isnull=True)
        elif self.value() == 'no':
            return queryset.filter(comprobante_pago='') | queryset.filter(comprobante_pago__isnull=True)
        return queryset


# ============================================================================
# 🛍️ INLINE PARA ITEMS DEL PEDIDO
# ============================================================================

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('subtotal_display', 'producto_info')
    fields = ('producto_info', 'cantidad', 'precio_unitario', 'subtotal_display')
    can_delete = False

    def producto_info(self, obj):
        if obj.producto:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; margin-right: 8px;">'
                '<div>'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</div>'
                '</div>',
                obj.producto.imagen.url if obj.producto.imagen else '/static/img/no-image.png',
                obj.producto.nombre,
                obj.producto.get_tipo_producto_display()
            )
        return '-'

    producto_info.short_description = '📦 Producto'

    def subtotal_display(self, obj):
        return format_html(
            '<strong style="color: #2563eb;">₲{}</strong>',
            f'{obj.subtotal:,}'
        )

    subtotal_display.short_description = '💰 Subtotal'


# ============================================================================
# 🗂️ ADMIN PARA PRODUCTOS
# ============================================================================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('imagen_miniatura', 'nombre', 'precio_display', 'tipo_producto', 'stock_display', 'activo',
                    'fecha_creacion')
    list_filter = ('tipo_producto', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('activo',)
    readonly_fields = ('fecha_creacion', 'afiliados_count', 'ventas_count')

    fieldsets = (
        ('📦 Información Básica', {
            'fields': ('nombre', 'descripcion', 'imagen')
        }),
        ('💰 Precio y Stock', {
            'fields': ('precio', 'tipo_producto', 'stock')
        }),
        ('👤 Vendedor y Estado', {
            'fields': ('vendedor', 'activo')
        }),
        ('📊 Estadísticas', {
            'fields': ('afiliados_count', 'ventas_count', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )

    def imagen_miniatura(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;">',
                obj.imagen.url
            )
        return '📷 Sin imagen'

    imagen_miniatura.short_description = '🖼️'

    def precio_display(self, obj):
        return format_html('<strong>₲{}</strong>', f'{obj.precio:,}')

    precio_display.short_description = '💰 Precio'
    precio_display.admin_order_field = 'precio'

    def stock_display(self, obj):
        if obj.tipo_producto == 'DIGITAL':
            return format_html('<span style="color: #10b981;">∞ Ilimitado</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color: #ef4444;">⚠️ {}</span>', obj.stock)
        else:
            return format_html('<span style="color: #10b981;">✅ {}</span>', obj.stock)

    stock_display.short_description = '📦 Stock'

    def afiliados_count(self, obj):
        count = obj.afiliados.count()
        return format_html('<strong>{}</strong> afiliados', count)

    afiliados_count.short_description = '🤝 Afiliados'

    def ventas_count(self, obj):
        # Contar items vendidos de este producto
        ventas = ItemPedido.objects.filter(
            producto=obj,
            pedido__estado__in=['CONFIRMADO', 'PROCESANDO', 'ENVIADO', 'ENTREGADO']
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        return format_html('<strong>{}</strong> vendidos', ventas)

    ventas_count.short_description = '📈 Ventas'


# ============================================================================
# 🛒 ADMIN PARA PEDIDOS (PRINCIPAL)
# ============================================================================

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_pedido_display',
        'cliente_info',
        'productos_resumen',
        'total_display',
        'metodo_pago_display',
        'estado_display',
        'comprobante_display',
        'fecha_creacion'
    )

    list_filter = (
        EstadoPedidoFilter,
        MetodoPagoFilter,
        ComprobanteFilter,
        'fecha_creacion',
        'fecha_confirmacion'
    )

    search_fields = (
        'numero_pedido',
        'nombre_completo',
        'email',
        'telefono',
        'usuario__username'
    )

    # CORREGIDO: No usar list_editable con campos personalizados
    # list_editable = ('estado',)  # ← COMENTADO: estado_display no es editable

    readonly_fields = (
        'numero_pedido',
        'fecha_creacion',
        'total_calculado',
        'productos_detalle',
        'comprobante_imagen',
        'info_afiliado',
        'items_count'
    )

    inlines = [ItemPedidoInline]

    fieldsets = (
        ('📋 Información del Pedido', {
            'fields': ('numero_pedido', 'estado', 'fecha_creacion', 'fecha_confirmacion')
        }),
        ('👤 Información del Cliente', {
            'fields': ('usuario', 'nombre_completo', 'email', 'telefono')
        }),
        ('📍 Entrega', {
            'fields': ('ciudad', 'direccion_envio', 'notas')
        }),
        ('💳 Pago', {
            'fields': ('metodo_pago', 'comprobante_imagen', 'comprobante_pago')
        }),
        ('💰 Totales', {
            'fields': ('total_calculado', 'items_count')
        }),
        ('🤝 Afiliación', {
            'fields': ('info_afiliado',),
            'classes': ('collapse',)
        }),
        ('📦 Productos', {
            'fields': ('productos_detalle',),
            'classes': ('wide',)
        }),
    )

    # Acciones personalizadas
    actions = ['marcar_como_procesando', 'marcar_como_enviado', 'marcar_como_entregado', 'exportar_csv']

    def numero_pedido_display(self, obj):
        return format_html(
            '<strong style="color: #1f2937; font-size: 14px;">#{}</strong>',
            obj.numero_pedido
        )

    numero_pedido_display.short_description = '🔢 N° Pedido'
    numero_pedido_display.admin_order_field = 'numero_pedido'

    def cliente_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #6b7280;">{}</small><br>'
            '<small style="color: #6b7280;">📞 {}</small>'
            '</div>',
            obj.nombre_completo,
            obj.email,
            obj.telefono
        )

    cliente_info.short_description = '👤 Cliente'

    def productos_resumen(self, obj):
        items = obj.items.all()
        if not items:
            return format_html('<em style="color: #9ca3af;">Sin productos</em>')

        html = '<div style="max-width: 200px;">'
        for item in items[:2]:  # Mostrar solo los primeros 2
            html += format_html(
                '<div style="margin-bottom: 4px; font-size: 12px;">'
                '• {} <strong>({})</strong>'
                '</div>',
                item.producto.nombre[:30] + '...' if len(item.producto.nombre) > 30 else item.producto.nombre,
                item.cantidad
            )

        if items.count() > 2:
            html += format_html(
                '<small style="color: #6b7280;">...y {} más</small>',
                items.count() - 2
            )

        html += '</div>'
        return format_html(html)

    productos_resumen.short_description = '📦 Productos'

    def total_display(self, obj):
        return format_html(
            '<strong style="color: #059669; font-size: 16px;">₲{}</strong>',
            f'{obj.total:,}'
        )

    total_display.short_description = '💰 Total'
    total_display.admin_order_field = 'total'

    def metodo_pago_display(self, obj):
        iconos = {
            'CONTRA_ENTREGA': '💵',
            'TRANSFERENCIA': '🏦',
            'TARJETA': '💳'
        }
        colores = {
            'CONTRA_ENTREGA': '#059669',
            'TRANSFERENCIA': '#2563eb',
            'TARJETA': '#7c3aed'
        }

        icono = iconos.get(obj.metodo_pago, '💰')
        color = colores.get(obj.metodo_pago, '#6b7280')

        return format_html(
            '<span style="color: {}; font-weight: 500;">{} {}</span>',
            color,
            icono,
            obj.get_metodo_pago_display()
        )

    metodo_pago_display.short_description = '💳 Método'

    def estado_display(self, obj):
        colores = {
            'PENDIENTE': '#f59e0b',
            'CONFIRMADO': '#2563eb',
            'PROCESANDO': '#7c3aed',
            'ENVIADO': '#f97316',
            'ENTREGADO': '#059669',
            'CANCELADO': '#ef4444'
        }

        iconos = {
            'PENDIENTE': '⏳',
            'CONFIRMADO': '✅',
            'PROCESANDO': '⚙️',
            'ENVIADO': '🚚',
            'ENTREGADO': '📦',
            'CANCELADO': '❌'
        }

        color = colores.get(obj.estado, '#6b7280')
        icono = iconos.get(obj.estado, '📋')

        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">'
            '{} {}'
            '</span>',
            color,
            icono,
            obj.get_estado_display()
        )

    estado_display.short_description = '📊 Estado'

    def comprobante_display(self, obj):
        if obj.comprobante_pago:
            return format_html(
                '<a href="{}" target="_blank" style="color: #059669; text-decoration: none;">'
                '✅ Ver Comprobante'
                '</a>',
                obj.comprobante_pago.url
            )
        elif obj.metodo_pago == 'TRANSFERENCIA':
            return format_html('<span style="color: #ef4444;">❌ Sin comprobante</span>')
        else:
            return format_html('<span style="color: #6b7280;">-</span>')

    comprobante_display.short_description = '🧾 Comprobante'

    def comprobante_imagen(self, obj):
        if obj.comprobante_pago:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">'
                '<br><br>'
                '<a href="{}" target="_blank" style="background: #2563eb; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none;">'
                '🔍 Ver en tamaño completo'
                '</a>'
                '</div>',
                obj.comprobante_pago.url,
                obj.comprobante_pago.url
            )
        return format_html('<em style="color: #9ca3af;">No hay comprobante subido</em>')

    comprobante_imagen.short_description = '🖼️ Comprobante de Pago'

    def productos_detalle(self, obj):
        items = obj.items.all()
        if not items:
            return format_html('<em>No hay productos en este pedido</em>')

        html = '''
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <div style="background: #f9fafb; padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>📦 Detalle de Productos</strong>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">Producto</th>
                        <th style="padding: 8px; text-align: center; border-bottom: 1px solid #e5e7eb;">Cant.</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 1px solid #e5e7eb;">Precio Unit.</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 1px solid #e5e7eb;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for item in items:
            html += format_html(
                '<tr>'
                '<td style="padding: 8px; border-bottom: 1px solid #f3f4f6;">'
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 30px; height: 30px; object-fit: cover; border-radius: 4px; margin-right: 8px;">'
                '<div>'
                '<strong>{}</strong><br>'
                '<small style="color: #6b7280;">{}</small>'
                '</div>'
                '</div>'
                '</td>'
                '<td style="padding: 8px; text-align: center; border-bottom: 1px solid #f3f4f6;"><strong>{}</strong></td>'
                '<td style="padding: 8px; text-align: right; border-bottom: 1px solid #f3f4f6;">₲{}</td>'
                '<td style="padding: 8px; text-align: right; border-bottom: 1px solid #f3f4f6;"><strong>₲{}</strong></td>'
                '</tr>',
                item.producto.imagen.url if item.producto.imagen else '/static/img/no-image.png',
                item.producto.nombre,
                item.producto.get_tipo_producto_display(),
                item.cantidad,
                f'{item.precio_unitario:,}',
                f'{item.subtotal:,}'
            )

        html += format_html(
            '</tbody>'
            '<tfoot>'
            '<tr style="background: #f9fafb; font-weight: bold;">'
            '<td colspan="3" style="padding: 12px; text-align: right; border-top: 2px solid #e5e7eb;">TOTAL:</td>'
            '<td style="padding: 12px; text-align: right; border-top: 2px solid #e5e7eb; color: #059669; font-size: 16px;">₲{}</td>'
            '</tr>'
            '</tfoot>'
            '</table>'
            '</div>',
            f'{obj.total:,}'
        )

        return format_html(html)

    productos_detalle.short_description = '📋 Detalle Completo'

    def total_calculado(self, obj):
        return format_html(
            '<div style="font-size: 18px; font-weight: bold; color: #059669; text-align: center; padding: 8px; background: #f0fdf4; border-radius: 6px;">'
            '₲{}'
            '</div>',
            f'{obj.total:,}'
        )

    total_calculado.short_description = '💰 Total del Pedido'

    def items_count(self, obj):
        count = obj.items.count()
        total_productos = obj.items.aggregate(total=Sum('cantidad'))['total'] or 0
        return format_html(
            '<strong>{}</strong> tipos de productos<br>'
            '<strong>{}</strong> unidades total',
            count,
            total_productos
        )

    items_count.short_description = '📊 Cantidad de Items'

    def info_afiliado(self, obj):
        if obj.afiliado_referido:
            return format_html(
                '<div style="padding: 8px; background: #f0f9ff; border-radius: 6px;">'
                '<strong>🤝 Afiliado:</strong> {}<br>'
                '<strong>💰 Comisión:</strong> ₲{}'
                '</div>',
                obj.afiliado_referido.username,
                f'{obj.comision_total:,.0f}' if hasattr(obj, 'comision_total') else '0'
            )
        return format_html('<em>Sin afiliado referido</em>')

    info_afiliado.short_description = '🤝 Información de Afiliado'

    # Acciones personalizadas
    actions = ['marcar_como_procesando', 'marcar_como_enviado', 'marcar_como_entregado',
               'cancelar_pedido_devolver_stock', 'exportar_csv']

    def cancelar_pedido_devolver_stock(self, request, queryset):
        """Cancelar pedidos y devolver stock a los productos"""
        from django.db import transaction

        count = 0
        productos_actualizados = []

        with transaction.atomic():
            for pedido in queryset:
                if pedido.estado in ['PENDIENTE', 'CONFIRMADO', 'PROCESANDO']:
                    # Devolver stock para cada item del pedido
                    for item in pedido.items.all():
                        if item.producto.tipo_producto == 'FISICO':
                            # Devolver stock
                            item.producto.stock += item.cantidad
                            item.producto.save()
                            productos_actualizados.append(f"{item.producto.nombre} (+{item.cantidad})")

                    # Cambiar estado a cancelado
                    pedido.estado = 'CANCELADO'
                    pedido.save()
                    count += 1
                else:
                    self.message_user(
                        request,
                        f'No se puede cancelar el pedido #{pedido.numero_pedido} porque ya está {pedido.get_estado_display().lower()}',
                        level='warning'
                    )

        if count > 0:
            mensaje = f'{count} pedidos cancelados exitosamente.'
            if productos_actualizados:
                mensaje += f' Stock devuelto: {", ".join(productos_actualizados[:5])}'
                if len(productos_actualizados) > 5:
                    mensaje += f' y {len(productos_actualizados) - 5} más.'
            self.message_user(request, mensaje)

    cancelar_pedido_devolver_stock.short_description = "❌ Cancelar pedidos y devolver stock"

    def marcar_como_procesando(self, request, queryset):
        count = queryset.update(estado='PROCESANDO')
        self.message_user(request, f'{count} pedidos marcados como procesando')

    marcar_como_procesando.short_description = "⚙️ Marcar como procesando"

    def marcar_como_enviado(self, request, queryset):
        count = queryset.update(estado='ENVIADO')
        self.message_user(request, f'{count} pedidos marcados como enviado')

    marcar_como_enviado.short_description = "🚚 Marcar como enviado"

    def marcar_como_entregado(self, request, queryset):
        count = queryset.update(estado='ENTREGADO')
        self.message_user(request, f'{count} pedidos marcados como entregado')

    marcar_como_entregado.short_description = "📦 Marcar como entregado"

    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'
        response.write('\ufeff')  # BOM para UTF-8

        writer = csv.writer(response)
        writer.writerow([
            'Número Pedido', 'Cliente', 'Email', 'Teléfono',
            'Total', 'Estado', 'Método de Pago', 'Fecha'
        ])

        for obj in queryset:
            writer.writerow([
                obj.numero_pedido,
                obj.nombre_completo,
                obj.email,
                obj.telefono,
                obj.total,
                obj.get_estado_display(),
                obj.get_metodo_pago_display(),
                obj.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            ])

        return response

    exportar_csv.short_description = "📊 Exportar a CSV"


# ============================================================================
# 📄 ADMIN PARA ITEMS DE PEDIDO
# ============================================================================

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido_numero', 'producto_info', 'cantidad', 'precio_display', 'subtotal_display')
    list_filter = ('pedido__estado', 'producto__tipo_producto')
    search_fields = ('pedido__numero_pedido', 'producto__nombre')
    readonly_fields = ('subtotal',)

    def pedido_numero(self, obj):
        return format_html(
            '<a href="{}" style="text-decoration: none;">#{}</a>',
            reverse('admin:productos_pedido_change', args=[obj.pedido.id]),
            obj.pedido.numero_pedido
        )

    pedido_numero.short_description = '🔢 Pedido'

    def producto_info(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<img src="{}" style="width: 30px; height: 30px; object-fit: cover; border-radius: 4px; margin-right: 8px;">'
            '<strong>{}</strong>'
            '</div>',
            obj.producto.imagen.url if obj.producto.imagen else '/static/img/no-image.png',
            obj.producto.nombre
        )

    producto_info.short_description = '📦 Producto'

    def precio_display(self, obj):
        return format_html('₲{}', f'{obj.precio_unitario:,}')

    precio_display.short_description = '💰 Precio'

    def subtotal_display(self, obj):
        return format_html('<strong>₲{}</strong>', f'{obj.subtotal:,}')

    subtotal_display.short_description = '💰 Subtotal'


# ============================================================================
# ⚙️ ADMIN PARA CONFIGURACIÓN DE PAGOS
# ============================================================================

@admin.register(ConfiguracionPagos)
class ConfiguracionPagosAdmin(admin.ModelAdmin):
    list_display = ('banco_nombre', 'banco_cuenta', 'banco_titular', 'comision_default')

    fieldsets = (
        ('🏦 Datos Bancarios', {
            'fields': ('banco_nombre', 'banco_cuenta', 'banco_titular', 'banco_cedula')
        }),
        ('💰 Configuración de Comisiones', {
            'fields': ('comision_afiliado_default',)
        }),
    )

    def comision_default(self, obj):
        return f'{obj.comision_afiliado_default}%'

    comision_default.short_description = '💰 Comisión'

    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionPagos.objects.exists()