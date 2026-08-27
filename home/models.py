from django.db import models
from core.models import BasePage

class HomePage(BasePage):
    """
    Página inicial do site, herdando de `BasePage` (SEO/Open Graph).

    `template` é definido como atributo de classe (em vez de sobrescrever
    `get_template()`) porque a home tem um template fixo e único, sem variação
    por tipo/conteúdo — diferente de `ConteudoPage`, que escolhe o template
    dinamicamente pelo slug do `tipo` (ver `conteudos/models.py`).
    """
    template = "home/home_page.html"