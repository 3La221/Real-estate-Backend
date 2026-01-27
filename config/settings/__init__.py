"""
Settings package for Django project.
Loads the appropriate settings module based on DJANGO_SETTINGS_MODULE environment variable.
"""
import os


env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
