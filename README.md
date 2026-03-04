# Nova PAT — Wagtail (desenvolvimento)

Projeto Django + Wagtail rodando em Docker com atualização automática de código (runserver + django-browser-reload).

Requisitos
- Docker (compose v2 integrado ou docker compose)
- (Opcional) WSL2 no Windows
- Git

  # Nova PAT — Wagtail (desenvolvimento)

  Projeto Django + Wagtail preparado para desenvolvimento com Docker Compose. Este README está organizado na ordem natural de setup e execução: clone → configuração de ambiente → build → run → migrações → comandos úteis → troubleshooting.

  Repositório
  - SSH: git@github.com:davidgalvao/nova-pat.git
  - HTTPS: https://github.com/davidgalvao/nova-pat.git

  Requisitos
  - Docker (compose v2 integrado ou `docker compose`)
  - Git
  - (Opcional) WSL2 no Windows

  1) Clone

  ```bash
  git clone git@github.com:davidgalvao/nova-pat.git
  cd nova-pat
  ```

  ou (HTTPS):

  ```bash
  git clone https://github.com/davidgalvao/nova-pat.git
  cd nova-pat
  ```

  2) Preparar variáveis de ambiente

  Copie o template e ajuste valores sensíveis localmente (não commitar):

  ```bash
  cp .env.example .env
  # Edite .env com SECRET_KEY e outras variáveis necessárias
  ```

  Observação: o repositório inclui `.env.example` como template; mantenha `.env` no seu `.gitignore`.

  3) Build (opcional) e subir containers

  - Para buildar explicitamente a imagem do serviço `web` (quando alterar dependências ou Dockerfile):

  ```bash
  docker compose build web
  ```

  - Subir containers em background (build implícito se necessário):

  ```bash
  docker compose up -d
  ```

  - Se quiser usar uma imagem local previamente tagueada (evitar rebuild):

  ```bash
  docker tag <IMAGE_ID ou NOME> nova-pat-web:latest
  docker compose up -d --no-build
  ```

  4) Migrações e superusuário

  ```bash
  docker compose exec web python manage.py migrate
  docker compose exec web python manage.py createsuperuser
  ```

  5) Comandos úteis

  - Logs em tempo real:

  ```bash
  docker compose logs -f web
  ```

  - Entrar no shell do container `web`:

  ```bash
  docker compose exec web sh
  # ou
  docker compose exec web bash
  ```

  - Django shell:

  ```bash
  docker compose exec web python manage.py shell
  ```

  6) Hot-reload e desenvolvimento

  - O projeto monta o diretório local como volume (`.:/code`) para refletir alterações de código sem rebuild.
  - `WATCHMAN_USE_POLLING=true` já está definido no compose para melhorar detecção de mudanças em ambientes montados (WSL/VMs).

  7) Onde ficam os dados

  - Postgres: `./postgres_data` (volume no host). Não comite esse diretório.

  8) Variáveis de ambiente (exemplo)

  - Veja `.env.example`. Exemplo mínimo:

  ```env
  SECRET_KEY=troque_por_uma_chave_segura
  DEBUG=1
  DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
  DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
  ```

  - Entrypoint suporta flags via env:
    - `RUN_MIGRATIONS=1` → executar `migrate` na inicialização
    - `COLLECTSTATIC=1` → executar `collectstatic` na inicialização (opcional)

  9) Troubleshooting rápido

  - Alterações de código não aparecem:
    - Confirme `.:/code` no serviço `web`.
    - Reinicie: `docker compose restart web`.
    - Verifique `WATCHMAN_USE_POLLING=true`.

  - Problemas com permissões em volumes (mídia/estáticos): ajustar permissões no host ou UID no compose/Dockerfile.

  - Para evitar rebuilds desnecessários:
    - Não altere dependencies nem o Dockerfile sem necessidade.
    - Use `docker compose up -d --no-build` para usar a imagem local.

  10) Notas finais

  - O `docker-compose.yml` está configurado para usar `image: nova-pat-web:latest` e `cache_from` para builds mais rápidos.
  - Consulte `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md` para diretrizes de contribuição.

  Se quiser, eu posso criar o commit com a mensagem proposta (não farei push). Deseja que eu crie o commit agora?
Atenção: não comite arquivos com segredos (por exemplo `.env`); use `.env.example` como template.
