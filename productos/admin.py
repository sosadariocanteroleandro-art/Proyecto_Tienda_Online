from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Producto, Pedido, ItemPedido, ConfiguracionPagos

# Configuración del sitio admin
admin.site.site_header = "Panel de Administración - Tu Tienda"
admin.site.site_title = "Admin Tu Tienda"
admin.site.index_title = "Gestión de Tienda"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'get_stock_badge', 'tipo_producto', 'vendedor',
                    'get_afiliados_count', 'activo', 'fecha_creacion')
    list_filter = ('tipo_producto', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    filter_horizontal = ('afiliados',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'precio', 'imagen', 'tipo_producto', 'stock')
        }),
        ('Gestión', {
            'fields': ('vendedor', 'afiliados', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_stock_badge(self, obj):
        if obj.tipo_producto == 'DIGITAL':
            return format_html('<span style="color: #10b981; font-weight: bold;">♾️ Ilimitado</span>')

        if obj.stock == 0:
            color = '#ef4444'
            texto = '❌ Sin stock'
        elif obj.stock < 5:
            color = '#f59e0b'
            texto = f'⚠️ {obj.stock} unidades'
        else:
            color = '#10b981'
            texto = f'✅ {obj.stock} unidades'

        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, texto)

    get_stock_badge.short_description = 'Stock'

    def get_afiliados_count(self, obj):
        count = obj.afiliados.count()
        if count > 0:
            return format_html('<strong style="color: #3b82f6;">{} afiliados</strong>', count)
        return format_html('<span style="color: #9ca3af;">Sin afiliados</span>')

    get_afiliados_count.short_description = 'Afiliados'

    actions = ['alerta_bajo_stock']

    def alerta_bajo_stock(self, request, queryset):
        productos_bajo_stock = queryset.filter(tipo_producto='FISICO', stock__lt=5, stock__gt=0)
        if productos_bajo_stock.exists():
            mensaje = ', '.join([f'{p.nombre} ({p.stock} unidades)' for p in productos_bajo_stock])
            self.message_user(request, f'⚠️ Productos con bajo stock: {mensaje}', level='warning')
        else:
            self.message_user(request, '✅ No hay productos con bajo stock')

    alerta_bajo_stock.short_description = "⚠️ Alertar sobre bajo stock"


# Inline para mostrar items dentro del pedido
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'get_estado_badge', 'usuario', 'get_total_formateado',
                    'get_items_count', 'get_afiliado_info', 'get_comision',
                    'comision_pagada', 'fecha_creacion']

    list_filter = ['estado', 'comision_pagada', 'fecha_creacion', 'fecha_confirmacion']

    search_fields = ['numero_pedido', 'usuario__username', 'nombre_completo', 'email',
                     'telefono', 'afiliado_referido__username']

    readonly_fields = ['numero_pedido', 'total', 'comision_total',
                       'fecha_creacion', 'fecha_actualizacion']

    date_hierarchy = 'fecha_creacion'

    inlines = [ItemPedidoInline]

    fieldsets = (
        ('Información del Pedido', {
            'fields': ('numero_pedido', 'usuario', 'estado', 'total',
                       'fecha_creacion', 'fecha_actualizacion')
        }),
        ('Información de Entrega', {
            'fields': ('nombre_completo', 'email', 'telefono', 'direccion_envio', 'ciudad'),
            'classes': ('collapse',)
        }),
        ('Sistema de Afiliados', {
            'fields': ('afiliado_referido', 'porcentaje_comision', 'comision_total',
                       'comision_pagada'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_confirmacion',),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )

    actions = ['marcar_confirmado', 'marcar_procesando', 'marcar_enviado',
               'marcar_entregado', 'marcar_comision_pagada', 'exportar_csv']

    def get_estado_badge(self, obj):
        colors = {
            'PENDIENTE': '#f59e0b',
            'CONFIRMADO': '#3b82f6',
            'PROCESANDO': '#8b5cf6',
            'ENVIADO': '#14b8a6',
            'ENTREGADO': '#10b981',
            'CANCELADO': '#ef4444'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 12px; font-weight: bold; font-size: 11px; display: inline-block;">{}</span>',
            colors.get(obj.estado, '#6b7280'),
            obj.get_estado_display()
        )

    get_estado_badge.short_description = 'Estado'

    def get_total_formateado(self, obj):
        total_formateado = f'{obj.total:,.0f}'
        return format_html('<strong style="color: #10b981; font-size: 14px;">₲{}</strong>', total_formateado)

    get_total_formateado.short_description = 'Total'

    def get_items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold;">{} items</span>', count)

    get_items_count.short_description = 'Productos'

    def get_afiliado_info(self, obj):
        if obj.afiliado_referido:
            return format_html(
                '<span style="color: #3b82f6; font-weight: bold;">{}</span>',
                obj.afiliado_referido.username
            )
        return format_html('<span style="color: #9ca3af;">Sin afiliado</span>')

    get_afiliado_info.short_description = 'Afiliado'

    def get_comision(self, obj):
        if obj.comision_total > 0:
            color = '#10b981' if obj.comision_pagada else '#f59e0b'
            return format_html(
                '<strong style="color: {};">₲{:,.0f}</strong>',
                color,
                obj.comision_total
            )
        return format_html('<span style="color: #9ca3af;">₲0</span>')

    get_comision.short_description = 'Comisión'

    def marcar_confirmado(self, request, queryset):
        updated = queryset.filter(estado='PENDIENTE').update(
            estado='CONFIRMADO',
            fecha_confirmacion=timezone.now()
        )
        self.message_user(request, f'{updated} pedido(s) confirmado(s)')

    marcar_confirmado.short_description = "✅ Marcar como Confirmado"

    def marcar_procesando(self, request, queryset):
        updated = queryset.filter(estado='CONFIRMADO').update(estado='PROCESANDO')
        self.message_user(request, f'{updated} pedido(s) en proceso')

    marcar_procesando.short_description = "⚙️ Marcar como En Proceso"

    def marcar_enviado(self, request, queryset):
        updated = queryset.exclude(estado__in=['CANCELADO', 'ENTREGADO']).update(estado='ENVIADO')
        self.message_user(request, f'{updated} pedido(s) marcado(s) como enviado')

    marcar_enviado.short_description = "🚚 Marcar como Enviado"

    def marcar_entregado(self, request, queryset):
        updated = queryset.exclude(estado__in=['CANCELADO', 'ENTREGADO']).update(estado='ENTREGADO')
        self.message_user(request, f'{updated} pedido(s) marcado(s) como entregado')

    marcar_entregado.short_description = "✅ Marcar como Entregado"

    def marcar_comision_pagada(self, request, queryset):
        pedidos_con_comision = queryset.filter(afiliado_referido__isnull=False, comision_pagada=False)
        updated = pedidos_con_comision.update(comision_pagada=True)
        total_comision = sum(p.comision_total for p in pedidos_con_comision)
        self.message_user(
            request,
            f'Comisión pagada en {updated} pedido(s). Total: ₲{total_comision:,.0f}'
        )

    marcar_comision_pagada.short_description = "💰 Marcar Comisión Pagada"

    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow([
            'Número Pedido', 'Estado', 'Usuario', 'Email', 'Total',
            'Cantidad Items', 'Afiliado', 'Comisión', 'Comisión Pagada', 'Fecha'
        ])

        for pedido in queryset:
            writer.writerow([
                pedido.numero_pedido or 'Carrito',
                pedido.get_estado_display(),
                pedido.usuario.username,
                pedido.email or 'N/A',
                f'₲{pedido.total:,.0f}',
                pedido.items.count(),
                pedido.afiliado_referido.username if pedido.afiliado_referido else 'N/A',
                f'₲{pedido.comision_total:,.0f}',
                'Sí' if pedido.comision_pagada else 'No',
                pedido.fecha_creacion.strftime('%Y-%m-%d %H:%M')
            ])

        return response

    exportar_csv.short_description = "📊 Exportar a CSV"


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['get_pedido_info', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['fecha_agregado']
    search_fields = ['pedido__numero_pedido', 'producto__nombre']
    readonly_fields = ['subtotal', 'fecha_agregado']

    def get_pedido_info(self, obj):
        if obj.pedido.numero_pedido:
            return format_html('Pedido #{}', obj.pedido.numero_pedido)
        return format_html('Carrito de {}', obj.pedido.usuario.username)

    get_pedido_info.short_description = 'Pedido'


@admin.register(ConfiguracionPagos)
class ConfiguracionPagosAdmin(admin.ModelAdmin):
    list_display = ['banco_nombre', 'banco_cuenta', 'comision_afiliado_default']

    fieldsets = (
        ('Información Bancaria', {
            'fields': ('banco_nombre', 'banco_cuenta', 'banco_titular', 'banco_cedula')
        }),
        ('Configuración de Comisiones', {
            'fields': ('comision_afiliado_default',)
        }),
        ('Integraciones de Pago', {
            'fields': ('mercadopago_public_key', 'mercadopago_access_token'),
            'classes': ('collapse',)
        }),
        ('Configuración General', {
            'fields': ('requiere_direccion_digital',)
        }),
    )

    def has_add_permission(self, request):
        return not ConfiguracionPagos.objects.exists()