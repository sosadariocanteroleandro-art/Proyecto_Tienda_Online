from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Formulario para crear nuevos usuarios"""

    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Tu nombre completo'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'tu@email.com'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'nombre', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            })


class DatosAfiliacionForm(forms.ModelForm):
    """
    Formulario para completar datos de afiliación
    """

    class Meta:
        model = CustomUser
        fields = [
            'tipo_persona',
            'documento_identidad',
            'pais_residencia',
            'telefono',
            'experiencia_marketing',
            'biografia_afiliado',
            'canales_promocion',
            'areas_interes'
        ]

        widgets = {
            'tipo_persona': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'documento_identidad': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: 12345678'
            }),
            'pais_residencia': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: Paraguay'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: +595 21 123456'
            }),
            'experiencia_marketing': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe brevemente tu experiencia en marketing o ventas (opcional)'
            }),
            'biografia_afiliado': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Cuéntanos sobre ti y por qué quieres ser afiliado (opcional)'
            }),
            'canales_promocion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Facebook, Instagram, WhatsApp, Blog personal, etc. (opcional)'
            }),
            'areas_interes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Productos de belleza, tecnología, cursos online, etc. (opcional)'
            })
        }

        labels = {
            'tipo_persona': 'Tipo de Persona *',
            'documento_identidad': 'Documento de Identidad *',
            'pais_residencia': 'País de Residencia *',
            'telefono': 'Teléfono',
            'experiencia_marketing': 'Experiencia en Marketing',
            'biografia_afiliado': 'Biografía/Presentación Personal',
            'canales_promocion': 'Canales de Promoción',
            'areas_interes': 'Áreas de Interés'
        }

        help_texts = {
            'tipo_persona': 'Selecciona si eres persona física o jurídica',
            'documento_identidad': 'Tu número de cédula, RUC, pasaporte, etc.',
            'pais_residencia': 'País donde resides actualmente',
            'telefono': 'Número de contacto (opcional pero recomendado)',
            'experiencia_marketing': 'Ayuda a que los productores confíen más en ti',
            'biografia_afiliado': 'Preséntate de manera profesional',
            'canales_promocion': '¿Dónde planeas promocionar los productos?',
            'areas_interes': '¿Qué tipo de productos te interesa más?'
        }

    def clean(self):
        """
        Validación personalizada del formulario
        """
        cleaned_data = super().clean()

        # Validar campos obligatorios
        campos_obligatorios = ['tipo_persona', 'documento_identidad', 'pais_residencia']

        for campo in campos_obligatorios:
            if not cleaned_data.get(campo):
                self.add_error(campo, 'Este campo es obligatorio.')

        return cleaned_data

    def save(self, commit=True):
        """
        Guardar y marcar datos como completos si cumple requisitos
        """
        user = super().save(commit=False)

        if commit:
            # Verificar si se completaron los datos mínimos
            user.completar_datos_afiliacion()
            user.save()

        return user