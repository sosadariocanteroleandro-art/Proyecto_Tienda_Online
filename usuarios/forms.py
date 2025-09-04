from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Formulario personalizado para la creación de un nuevo usuario.
    Extiende de UserCreationForm para incluir los campos personalizados.
    """

    # Campo email adicional (NUEVO)
    email = forms.EmailField(
        label=_('Correo electrónico'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ejemplo@correo.com'}),
        help_text=_('Requerido. Ingrese un correo electrónico válido.')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Traducir labels al español
        self.fields['username'].label = _('Nombre de usuario')
        self.fields['password1'].label = _('Contraseña')
        self.fields['password2'].label = _('Confirmar contraseña')
        self.fields['nombre'].label = _('Nombre completo')

        # Traducir help texts al español
        self.fields['username'].help_text = _(
            'Requerido. 150 caracteres o menos. Solo letras, números y los caracteres @/./+/-/_.'
        )
        self.fields['password1'].help_text = _(
            "• Su contraseña no puede ser similar a su información personal.<br>"
            "• Debe contener al menos 8 caracteres.<br>"
            "• No puede ser una contraseña comúnmente utilizada.<br>"
            "• No puede ser enteramente numérica."
        )
        self.fields['password2'].help_text = _(
            "Ingrese la misma contraseña que antes, para verificación."
        )
        self.fields['nombre'].help_text = _('Ingrese su nombre completo.')
        self.fields['email'].help_text = _('Requerido. Ingrese un correo electrónico válido.')

    class Meta:
        # Utiliza el modelo de usuario personalizado que hemos definido
        model = CustomUser
        # Incluye los campos estándar, más email y nombre
        fields = ('username', 'email', 'nombre', 'password1', 'password2')
        # Asegúrate de no incluir campos que puedan ser sensibles o no deseados

        # Labels en español para los campos del modelo
        labels = {
            'username': _('Nombre de usuario'),
            'email': _('Correo electrónico'),
            'nombre': _('Nombre completo'),
        }
        help_texts = {
            'username': _('Requerido. 150 caracteres o menos. Solo letras, números y @/./+/-/_.'),
            'email': _('Requerido. Ingrese un correo electrónico válido.'),
            'nombre': _('Ingrese su nombre completo.'),
        }

    def clean_email(self):
        """Validación personalizada para verificar que el email no exista"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Este correo electrónico ya está registrado.'))
        return email


# Si necesitas el UserChangeForm también, aquí está
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'nombre')