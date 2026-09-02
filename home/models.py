from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

from core.blocks import HomeStreamBlock
from core.models import BasePage


class HomePage(BasePage):
    """
    Página inicial ("home") do site, definida como `root_page` do site Wagtail
    (ver `home/migrations/0002_create_homepage.py`).

    Herda de `BasePage` (app `core`), herdando os campos de SEO/Open Graph
    (`og_title`, `og_description`, `og_image`) e os `promote_panels`
    correspondentes, além dos campos padrão de `wagtail.models.Page`.

    O conteúdo da Home é construído de forma modular via `StreamField`
    (`body`), usando os blocos reutilizáveis de `core/blocks.py`
    (`HomeStreamBlock`). O `body` é opcional (`required=False`), permitindo
    que a Home renderize corretamente mesmo vazia (estado inicial limpo).

    `template` é definido como atributo de classe (em vez de sobrescrever
    `get_template()`) porque a home tem um template fixo e único, sem variação
    por tipo/conteúdo — diferente de `ConteudoPage`, que escolhe o template
    dinamicamente pelo slug do `tipo` (ver `conteudos/models.py`).
    """
    template = "home/home_page.html"

    body = StreamField(
        HomeStreamBlock(),
        use_json_field=True,
        blank=True,
        verbose_name="Conteúdo da Home",
        help_text="Construa a Home adicionando seções modulares (hero, banners, carrosséis, destaques e recursos).",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("body"),
    ]