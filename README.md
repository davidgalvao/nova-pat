# Nova PAT — Wagtail (desenvolvimento)

Projeto Django + Wagtail rodando em Docker com atualização automática de código (runserver + django-browser-reload).

Requisitos
- Docker (compose v2 integrado ou docker compose)
- (Opcional) WSL2 no Windows
- Git

Resumo sobre imagens e rebuild
- O projeto monta o código como volume (./:/code). Alterações de código são refletidas imediatamente sem rebuild.
- Rebuild só é necessário quando mudam dependências (requirements.txt/pyproject) ou o Dockerfile.
- Para acelerar builds e reaproveitar camadas, usamos uma imagem nomeada (nova-pat-web:latest) e cache_from no docker-compose. Assim o Docker pode reutilizar camadas da imagem local existente.

Como buildar e rodar (desenvolvimento)
1. Subir containers em background (usa imagem local se existir):
   ```bash
   docker compose up -d
   ```
2. Usar a imagem local sem rebuild:
   ```bash
   docker compose up -d --no-build
   ```
3. Forçar rebuild (ao alterar Dockerfile ou dependências):
   ```bash
   docker compose build web
   docker compose up -d --force-recreate
   ```
4. Parar e remover containers:
   ```bash
   docker compose down
   # remover volumes (DB):
   docker compose down -v
   ```

Reusar uma imagem local com outro nome
- Se você já tem uma imagem que quer reaproveitar, tagueie-a para o nome esperado:
  ```bash
  docker tag <IMAGE_ID ou NOME> nova-pat-web:latest
  ```
- Depois rode `docker compose up -d` ou `docker compose up -d --no-build` para iniciar usando essa imagem.

Acessos
- Site: http://localhost:8000
- Admin: http://localhost:8000/admin

Comandos úteis no serviço `web`
- Rodar migrations:
  ```bash
  docker compose exec web python manage.py migrate
  ```
- Criar superusuário:
  ```bash
  docker compose exec web python manage.py createsuperuser
  ```
- Django shell:
  ```bash
  docker compose exec web python manage.py shell
  ```
- Entrar no shell do container:
  ```bash
  docker compose exec web sh
  # ou
  docker compose exec web bash
  ```

Hot-reload
- O código local é montado como volume (./:/code) para refletir alterações imediatamente.
- `docker-compose.yml` já define `WATCHMAN_USE_POLLING=true` para evitar problemas de watch em FS montados (WSL/VMs).

Onde ficam os dados
- Postgres: ./postgres_data (ver docker-compose.yml).

Variáveis de ambiente (exemplo)
- Coloque variáveis sensíveis em `.env` (não commitar). Exemplo mínimo:
  ```env
  SECRET_KEY=troque_por_uma_chave_segura
  DEBUG=1
  DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
  DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
  ```
- Entrypoint suporta estas flags via env:
  - RUN_MIGRATIONS=1  → executar `migrate` na inicialização (configurado por padrão em dev)
  - COLLECTSTATIC=1  → executar `collectstatic` na inicialização (opcional)

Dicas rápidas / troubleshooting
- Alterações de código não aparecem:
  - Confirme `.:/code` no serviço `web`.
  - Reinicie: `docker compose restart web`.
  - Verifique `WATCHMAN_USE_POLLING=true`.
- Para evitar rebuilds desnecessários:
  - Não altere dependencies nem o Dockerfile sem necessidade.
  - Use `docker compose up -d --no-build` para usar a imagem local.
  - Use `docker tag` se quiser reaproveitar uma imagem local já existente.
- Problemas com permissões em volumes (mídia/estáticos): ajustar permissões no host ou UID no compose/Dockerfile.
- Logs:
  ```bash
  docker compose logs -f web
  docker compose ps
  ```

Notas finais
- O docker-compose já está configurado para usar `image: nova-pat-web:latest` e `cache_from` — aproveite isso para builds mais rápidos.
- Se quiser, aplico exemplos automáticos de CI/build que façam push da imagem para um registry para uso em máquinas sem a imagem local.

## Como clonar e rodar (rápido)

Instruções mínimas para um colega clonar e subir o projeto localmente usando Docker Compose:

```bash
git clone git@github.com:SEU-USER/NOME-DO-REPO.git
cd NOME-DO-REPO
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Altere `SEU-USER`/`NOME-DO-REPO` para os valores reais. Verifique o arquivo `.env.example` para variáveis necessárias.

Notas sobre versão do Wagtail
- Atualizado Wagtail para 7.3.1.
- Leia as notas de release/upgrade: https://docs.wagtail.org/en/stable/releases/7.3.html#upgrade-considerations-changes-affecting-all-projects
- Ações recomendadas após atualizar a dependência:
  1. Rebuild da imagem (para instalar a nova versão):
     ```bash
     docker compose build web
     docker compose up -d
     ```
  2. Rodar migrações:
     ```bash
     docker compose exec web python manage.py migrate
     ```
  3. Testar o site / admin e revisar logs:
     ```bash
     docker compose logs -f web
     ```
- Se seu código usar APIs internas ou pontos que foram marcados como depreciados nas notas de release, siga as instruções no link acima para aplicar correções.
