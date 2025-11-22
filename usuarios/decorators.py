from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def datos_afiliacion_requeridos(view_func):
    """
    Decorador que verifica si el usuario tiene los datos de afiliación completos
    antes de permitir acceso a funcionalidades de afiliación.

    Uso: @datos_afiliacion_requeridos encima de cualquier vista que requiera datos completos
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar que esté logueado
        if not request.user.is_authenticated:
            return redirect('usuarios:login')

        # Verificar que sea vendedor
        if not request.user.es_vendedor():
            messages.error(request, 'Necesitas ser vendedor/afiliado para acceder a esta funcionalidad.')
            return redirect('usuarios:upgrade_vendedor')

        # Verificar que tenga datos de afiliación completos
        if not request.user.datos_afiliacion_completos:
            campos_faltantes = request.user.get_campos_faltantes_afiliacion()

            messages.warning(
                request,
                f'Debes completar tu perfil de afiliación antes de continuar. '
                f'Faltan: {", ".join(campos_faltantes)}. '
                f'Ve a Mi Perfil para completar los datos.'
            )
            return redirect('usuarios:perfil')

        # Si todo está bien, ejecutar la vista original
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def puede_afiliarse_check(user):
    """
    Función auxiliar para verificar en templates si el usuario puede afiliarse
    """
    return (user.is_authenticated and
            user.es_vendedor() and
            user.datos_afiliacion_completos)


# Context processor para usar en templates
def afiliacion_context(request):
    """
    Context processor para agregar información de afiliación a todos los templates
    """
    context = {}

    if request.user.is_authenticated:
        context.update({
            'puede_afiliarse': puede_afiliarse_check(request.user),
            'datos_afiliacion_completos': getattr(request.user, 'datos_afiliacion_completos', False),
            'es_vendedor': request.user.es_vendedor(),
        })

    return context