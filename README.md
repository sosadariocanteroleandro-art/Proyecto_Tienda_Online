# Tienda Ecommerce con Django

Proyecto de ecommerce con sistema de afiliados desarrollado en Django.

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno: `venv\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Copiar `.env.example` a `.env` y configurar variables
6. Migrar base de datos: `python manage.py migrate`
7. Crear superusuario: `python manage.py createsuperuser`
8. Correr servidor: `python manage.py runserver`

## Tecnologías

- Django 5.2.5
- PostgreSQL
- Tailwind CSS
- Google OAuth