from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado.
    Hereda de AbstractUser para extender el modelo de usuario por defecto de Django.
    """
    # Campo para el nombre del usuario
    nombre = models.CharField(max_length=100)

    # Campo para el correo electrónico (NUEVO)
    email = models.EmailField(
        _('correo electrónico'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        }
    )

    # Agregamos related_name para evitar conflictos con el modelo de usuario por defecto de Django.
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    # Campos requeridos para el modelo (NUEVO)
    REQUIRED_FIELDS = ['email', 'nombre']

    def __str__(self):
        # Representación en cadena del objeto, útil para el panel de administración
        return self.username


