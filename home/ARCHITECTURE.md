# home/ — ARCHITECTURE.md

## Papel deste app
`home` contém a página inicial ("home") do site, definida como `root_page` do site Wagtail (ver `home/migrations/0002_create_homepage.py`). É a porta de entrada da plataforma e o único app responsável pela página raiz.

Fonte da verdade: `core/ARCHITECTURE.md` (para `BasePage` e blocos), `core/blocks.py` (para `HomeStreamBlock`).

## Fase atual: construção
A Home é construída de forma modular via `StreamField`, consumindo os blocos reutilizáveis de `core/blocks.py`.

## Model `HomePage(BasePage)`

Herda de `BasePage` (app `core`), herdando os campos de SEO/Open Graph (`og_title`, `og_description`, `og_image`) e os `promote_panels` correspondentes, além dos campos padrão de `wagtail.models.Page`.

Campos próprios:
- `body` — `StreamField(HomeStreamBlock())`, **opcional** (`blank=True`), permitindo que a Home renderize corretamente mesmo vazia (estado inicial limpo). Usa `use_json_field=True`.

Configuração:
- `template = "home/home_page.html"` — definido como **atributo de classe** (não sobrescreve `get_template()`), porque a home tem um template fixo e único, sem variação por tipo/conteúdo — diferente de `ConteudoPage`, que escolhe o template dinamicamente pelo `mecanismo_exibicao` (ver `conteudos/ARCHITECTURE.md`).

## Dependências entre apps
- `core.blocks.HomeStreamBlock` — define os blocos disponíveis no `body`.
- `core.models.BasePage` — base de SEO/Open Graph.

## O que NÃO fazer neste app
- Não sobrescrever `get_template()` — a home tem template fixo (`home/home_page.html`).
- Não adicionar campos de layout (hide_header, hide_footer, custom_body_class) em `BasePage` — esses campos vivem no `FlexLayoutMixin` (app `core`), que **não** deve ser aplicado em conteúdo nem na home.
- Não criar outros models de página aqui — a home é a única página deste app; páginas institucionais/landing pages devem ser avaliadas em `core` ou app próprio.