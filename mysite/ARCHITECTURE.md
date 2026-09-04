# mysite/ — ARCHITECTURE.md

## Papel deste app
`mysite` é o **pacote de configuração do projeto** Django/Wagtail. Não contém models de domínio — concentra as configurações de ambiente, o roteamento de URLs e os templates globais do site. É o "esqueleto" gerado por `django-admin startproject` e customizado para a Nova PAT.

Fonte da verdade: `README.md`, `CONTEXT.MD`, `docs/` (ADRs e requisitos).

## Estrutura do app

### `mysite/settings/` — configurações por ambiente
- `base.py` — configurações compartilhadas entre todos os ambientes (dev e production herdam daqui). Decisões relevantes:
  - **`AUTH_USER_MODEL = "usuarios.User"`** — model de usuário customizado (estende `AbstractUser` com `role`, `verified`, `options` e soft delete). Definido antes de qualquer migração — ver `usuarios/ARCHITECTURE.md`.
  - **`WAGTAILSEARCH_BACKENDS`** — usa o backend de busca em banco de dados do Wagtail (não tsvector manual) — ver `docs/adr/0003-busca-ambos-por-ids.md`.
  - **`DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000`** — eleva o limite padrão do Django (1000) porque models de página do Wagtail podem exceder esse limite no editor.
  - **`WAGTAILDOCS_EXTENSIONS`** — restringe as extensões de documento permitidas na biblioteca de documentos (medida de segurança contra upload arbitrário).
  - **`LANGUAGE_CODE = "pt-br"`** e **`TIME_ZONE = "America/Sao_Paulo"`** — localização do projeto.
  - **`INSTALLED_APPS`** — registra os 10 apps locais (`core`, `home`, `search`, `conteudos`, `canais`, `curriculo`, `series`, `aplicativos`, `interacoes`, `usuarios`) + dependências (Wagtail, modelcluster, taggit, django_filters, django_browser_reload, contrib).
- `dev.py` — herda de `base.py`; configurações de desenvolvimento.
- `production.py` — herda de `base.py`; configurações de produção.

### `mysite/urls.py` — roteamento (URLconf)
Ordem das rotas (importante — o Django processa na ordem):
1. `django-admin/` — admin nativo do Django (não Wagtail).
2. `admin/` — admin do Wagtail (interface de gestão de conteúdo).
3. `documents/` — biblioteca de documentos do Wagtail.
4. `search/` — busca avançada customizada (RF001, ver `search/views.py`).
5. `__reload__/` — django-browser-reload para hot-reload em desenvolvimento.
6. (DEBUG) static/media — servidos pelo runserver em desenvolvimento.
7. `""` (catch-all) — **deve ser a última rota**: delega ao mecanismo de serving de páginas do Wagtail (`wagtail_urls`). Qualquer rota não capturada acima vira uma Page do Wagtail.

> **Não alterar a ordem sem entender as implicações** — o catch-all do Wagtail precisa ficar por último.

### `mysite/wsgi.py`
Entry point WSGI para servidores de aplicação.

### `mysite/templates/` — templates globais
- `base.html` — template base de todo o site (SEO/Open Graph, Tailwind via CDN, header, footer, blocks `content`/`extra_css`/`extra_js`).
- `includes/header.html` — menu superior (navegação via `NavigationItem`, busca global).
- `includes/footer.html` — rodapé institucional (links via `NavigationItem`, licenciamento, LGPD).
- `404.html`, `500.html` — páginas de erro.

## Dependências entre apps
- `mysite` depende de **todos** os apps (registrados em `INSTALLED_APPS`).
- `search` é referenciado em `urls.py` (`search/views.py`).
- Templates globais usam `core.templatetags.navigation_tags` (`get_navigation_items`, `get_footer_items`).

## O que NÃO fazer neste app
- Não adicionar models de domínio aqui — `mysite` é só configuração; models vivem nos apps de domínio.
- Não adicionar um app sem registrá-lo em `INSTALLED_APPS` (em `base.py`).
- Não alterar a ordem das rotas em `urls.py` sem entender que o catch-all do Wagtail deve ser o último.
- Não executar comandos Python/pytest/manage.py diretamente no host — usar o serviço `web` do Docker (`docker compose exec web <comando>`).