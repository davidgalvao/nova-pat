## Orientações rápidas para agentes de codificação

Objetivo: dar a um agente AI o contexto mínimo e ações concretas para ser produtivo neste projeto Django + Wagtail em Docker.

- Projeto: Django (provavelmente Django 6.x) + Wagtail (ver `requirements.txt`: `wagtail==7.3.1`).
- Execução local: via Docker Compose (arquivo `docker-compose.yml`) — código montado como volume `./:/code`.

Pontos essenciais (o "porquê" e o fluxo):

- Arquitetura: app Django com Wagtail; o servidor web é executado pelo comando padrão em `Dockerfile`/compose (`python manage.py runserver 0.0.0.0:8000`). O banco é Postgres (volume local `./postgres_data`).
- Entrada do container: `entrypoint.sh` — aplica `migrate` e `collectstatic` quando as variáveis de ambiente `RUN_MIGRATIONS=1` ou `COLLECTSTATIC=1` estiverem presentes.
- Build/Imagem: `Dockerfile` gera a imagem nomeada `nova-pat-web:latest` e o `docker-compose.yml` usa `cache_from` para acelerar rebuilds.

Comandos e fluxos específicos para desenvolvedores (use exatamente estes exemplos):

- Subir em background (usa imagem local se existir):

  ```bash
  docker compose up -d
  ```

- Subir sem rebuild (usar imagem local):

  ```bash
  docker compose up -d --no-build
  ```

- Forçar rebuild (quando mudar `requirements.txt` ou `Dockerfile`):

  ```bash
  docker compose build web
  docker compose up -d --force-recreate
  ```

- Migrations / shell / logs:

  ```bash
  docker compose exec web python manage.py migrate
  docker compose exec web python manage.py createsuperuser
  docker compose exec web python manage.py shell
  docker compose exec web sh
  docker compose logs -f web
  ```

Padrões e convenções do código (exemplos concretos):

- Configuração: `manage.py` aponta por padrão para `mysite.settings.dev` — verificar esse módulo se precisar mudar o comportamento em dev.
- Estrutura de templates/static: `home/templates/home/` contém páginas de front; `mysite/templates/` contém erros e `base.html`. Assets em `static/` e `mysite/static/`.
- Padrão de busca: `search/views.py` usa `Page.objects.live().search(query)` e paginação com `django.core.paginator.Paginator` — siga esse padrão ao adicionar busca/filtragem.
- Comentários úteis já existentes: o módulo `search` tem instruções comentadas para integrar `wagtail.contrib.search_promotions` — preserve a ideia de ativar via `INSTALLED_APPS` quando implementar promoção de resultados.

Integrações e pontos de atenção (o que quebrará facilmente):

- Volumes: o código é montado (`.:/code`) — mudanças no host aparecem imediatamente; não re-construa a imagem para alterações de código simples.
- Rebuild necessário quando dependências mudam (`requirements.txt`) ou o `Dockerfile` é alterado — caso contrário use `--no-build`.
- Collectstatic: removido do build por intenção (ver `Dockerfile`); se precisar coletar assets at startup, use `COLLECTSTATIC=1` no ambiente do serviço `web`.
- Permissões: `Dockerfile` cria usuário `wagtail` e altera dono de `/code`; problemas de permissão em volumes podem exigir ajuste no host ou no compose.

Onde procurar ao implementar mudanças:

- Entrypoint e flags: `entrypoint.sh` (migrations/collectstatic automáticos).
- Compose/build: `docker-compose.yml` (nome da imagem `nova-pat-web:latest`, `cache_from`, `WATCHMAN_USE_POLLING=true`).
- Views e rotas: `search/views.py`, `mysite/urls.py` (padrão Wagtail).
- Dependências: `requirements.txt` (versões de Django/Wagtail e libs de DB).

Contrato mínimo para mudanças pequenas (ex.: adicionar view ou endpoint):

- Inputs: manter compatibilidade com `.:/code` e o `manage.py` apontando para `mysite.settings.dev`.
- Outputs: servidor deve subir com `docker compose up -d` e rota/feature testável em http://localhost:8000.
- Erros esperados: falha no start se `DATABASE_URL` apontar para DB inacessível; entradas de log úteis em `docker compose logs -f web`.

Checks rápidos antes do PR/commit:

- Rodar `docker compose exec web python manage.py migrate` e garantir que o servidor responde.
- Confirmar que não foram exigidas mudanças no `requirements.txt` sem rebuild da imagem (se houver, documente no PR).

Notas finais e links rápidos:

- Dados Postgres persistem em `./postgres_data`.
- Porta padrão: 8000 (site e admin). Admin Wagtail: `/admin/`.

Se algo estiver faltando ou obscuro neste guia, diga qual parte você quer que eu detalhe (ex.: fluxos de CI, testes automatizados, ou políticas de branches) e eu atualizo o arquivo.
