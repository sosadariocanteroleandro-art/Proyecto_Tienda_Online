from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "precio", "descripcion", "imagen", "tipo_producto"]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe tu producto...',
                'rows': 5
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'tipo_producto': forms.Select(attrs={
                'class': 'form-control'
            })
        }

        labels = {
            'nombre': 'Nombre del Producto',
            'precio': 'Precio ($)',
            'descripcion': 'Descripción',
            'imagen': 'Imagen del Producto',
            'tipo_producto': 'Tipo de Producto'
        }

        help_texts = {
            'imagen': 'Formatos permitidos: JPG, PNG, GIF (máx. 5MB)',
            'precio': 'Ingresa el precio en formato decimal (ej: 99.99)'
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio and precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor a 0")
        return precio

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            # Validar tamaño (5MB máximo)
            if imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede superar los 5MB")

            # Validar tipo de archivo
            if not imagen.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                raise forms.ValidationError("Solo se permiten imágenes JPG, PNG, GIF o WebP")

        return imagen