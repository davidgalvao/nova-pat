from django.apps import AppConfig


class InteracoesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "interacoes"
    verbose_name = "Interações"

    def ready(self):
        # Import signals to register them
        import interacoes.signals  # noqa: F401