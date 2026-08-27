from django.apps import AppConfig


class ConteudosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'conteudos'
    verbose_name = 'Conteúdos Educacionais'
    
    def ready(self):
        import conteudos.wagtail_hooks  # noqa: F401