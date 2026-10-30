# Tech Context — Nova PAT

- **Stack:** Django 6.0.8, Wagtail 8.0, Postgres 15 (Docker), Tailwind CSS via CDN, django-taggit, django_filters, django-browser-reload, wagtail.embeds (oEmbed, 80 providers nativos; Google Slides não suportado).
- **Ambiente:** tudo via `docker compose` (raiz do repositório); serviço `web` (nunca `backend`); proibido rodar python/pip/pytest/manage.py direto no host; container web: `nova-pat-web-1`.
- **Comandos principais:** `docker compose exec web pytest -x -q` (211 testes passando); `docker compose exec web python manage.py makemigrations` / `migrate`; `migrate --check` e `makemigrations --check --dry-run` antes de commitar; `docker compose logs web --tail 30`; `docker compose restart web`.
- **Caminhos importantes (relativos à raiz):** `mysite/settings/base.py` (settings); `requirements.txt`; `docker-compose.yml`; `AUTH_USER_MODEL = "usuarios.User"`; `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`.
- **Banco:** `postgres_data/` (não mexer sem aprovação); `db.sqlite3` existe localmente.
