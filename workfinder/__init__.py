# Celery app is optional and loaded conditionally
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    pass