from django.db import models
from core.models import BasePage

class HomePage(BasePage):
    """
    Página inicial ("home") do site, definida como `root_page` do site Wagtail
    (ver `home/migrations/0002_create_homepage.py`).

    Herda de `BasePage` (app `core`), herdando os campos de SEO/Open Graph
    (`og_title`, `og_description`, `og_image`) e os `promote_panels`
    correspondentes, além dos campos padrão de `wagtail.models.Page`.

    `template` é definido como atributo de classe (em vez de sobrescrever
    `get_template()`) porque a home tem um template fixo e único, sem variação
    por tipo/conteúdo — diferente de `ConteudoPage`, que escolhe o template
    dinamicamente pelo slug do `tipo` (ver `conteudos/models.py`).
    """
    template = "home/home_page.html"