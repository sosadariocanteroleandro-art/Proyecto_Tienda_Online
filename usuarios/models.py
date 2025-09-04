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


# Definimos el modelo Producto, que hereda de models.Model
# Este modelo se mapeará a una tabla en tu base de base de datos
class Producto(models.Model):
    # Campo para el nombre del producto, con un máximo de 200 caracteres
    nombre = models.CharField(max_length=200)

    # Campo de texto para una descripción más detallada
    descripcion = models.TextField()

    # Campo para el precio del producto. DecimalField es ideal para dinero
    # ya que evita errores de precisión que pueden ocurrir con float.
    # max_digits es el número total de dígitos permitidos
    # decimal_places es el número de decimales
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    # Campo para el inventario. Se usa IntegerField para un conteo de unidades
    stock = models.IntegerField(default=0)

    # Campo para una imagen del producto. Usamos un CharField para la URL de la imagen.
    # En un entorno de producción, sería mejor usar ImageField para subir archivos.
    imagen = models.CharField(max_length=500, default='https://placehold.co/600x400/007bff/fff?text=Sin+Imagen')

    # Campo para la fecha y hora de creación del producto.
    # auto_now_add=True se asegura de que la fecha se establezca automáticamente
    # cuando se crea el objeto por primera vez.
    fecha_creacion = models.DateTimeField(default=timezone.now)

    TIPO_PRODUCTO = [
        ('FISICO', 'Fisico'),
        ('DIGITAL', 'Digital')
    ]
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO, default='FISICO')


    class Meta:
        # Nombre singular del modelo en el panel de administración
        verbose_name = "Producto"
        # Nombre plural del modelo en el panel de administración
        verbose_name_plural = "Productos"
        # Ordenar los productos por la fecha de creación en orden descendente (los más nuevos primero)
        ordering = ['-fecha_creacion']

    def __str__(self):
        # Este método define la representación de cadena de un objeto.
        # Es útil para mostrar el nombre del producto en el panel de administración de Django
        return self.nombre