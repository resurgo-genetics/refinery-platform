# custom settings for development environment (e.g., Vagrant VM)

from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

STATICFILES_DIRS = (
    "/vagrant/refinery/static/development",
    "/vagrant/refinery/ui/development"
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable migrations when running unittests and use syncdb instead
SOUTH_TESTS_MIGRATE = False

# required for Django Debug Toolbar
# https://github.com/django-debug-toolbar/django-debug-toolbar/issues/529
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INSTALLED_APPS += (
    'debug_toolbar',
)
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'middleware.JsonAsHTML',
)
INTERNAL_IPS = ('192.168.50.1')
