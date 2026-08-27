from django.apps import AppConfig


class CanaisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'canais'
    verbose_name = 'Canais'
    
    def ready(self):
        import canais.wagtail_hooks  # noqa: F401