# Nova PAT — Wagtail (desenvolvimento)

Projeto Django + Wagtail rodando em Docker com atualização automática de código (runserver + django-browser-reload).

## Índice

1. [Requisitos](#requisitos)
2. [Clone](#1-clone)
3. [Preparar variáveis de ambiente](#2-preparar-variáveis-de-ambiente)
4. [Build e subir containers](#3-build-opcional-e-subir-containers)
5. [Migrações e superusuário](#4-migrações-e-superusuário)
6. [Comandos úteis](#5-comandos-úteis)
7. [Hot-reload e desenvolvimento](#6-hot-reload-e-desenvolvimento)
8. [Onde ficam os dados](#7-onde-ficam-os-dados)
9. [Princípios de arquitetura (Wagtail)](#8-princípios-de-arquitetura-wagtail)
10. [Variáveis de ambiente](#9-variáveis-de-ambiente-exemplo)
11. [Troubleshooting](#10-troubleshooting-rápido)
12. [Documentação de arquitetura e decisões](#documentação-de-arquitetura-e-decisões)

---

## Requisitos

- Docker (compose v2 integrado ou `docker compose`)
- Git
- (Opcional) WSL2 no Windows

## Repositório

- SSH: `git@github.com:davidgalvao/nova-pat.git`
- HTTPS: `https://github.com/davidgalvao/nova-pat.git`

---

## 1) Clone

```bash
git clone git@github.com:davidgalvao/nova-pat.git
cd nova-pat
```

ou (HTTPS):

```bash
git clone https://github.com/davidgalvao/nova-pat.git
cd nova-pat
```

## 2) Preparar variáveis de ambiente

Copie o template e ajuste valores sensíveis localmente (não commitar):

```bash
cp .env.example .env
# Edite .env com SECRET_KEY e outras variáveis necessárias
```

Observação: o repositório inclui `.env.example` como template; mantenha `.env` no seu `.gitignore`.

## 3) Build (opcional) e subir containers

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

## 4) Migrações e superusuário

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## 5) Comandos úteis

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

## 6) Hot-reload e desenvolvimento

- O projeto monta o diretório local como volume (`.:/code`) para refletir alterações de código sem rebuild.
- `WATCHMAN_USE_POLLING=true` já está definido no compose para melhorar detecção de mudanças em ambientes montados (WSL/VMs).

## 7) Onde ficam os dados

- Postgres: `./postgres_data` (volume no host). Não comite esse diretório.

## 8) Princípios de Arquitetura (Wagtail)

Para manter a manutenibilidade e escalabilidade do projeto, seguimos estes padrões:

- **BasePage Enxuta**: A `core.BasePage` deve conter apenas metadados (SEO, Open Graph) e controles de layout globais. Não adicione StreamFields de conteúdo ou lógica de negócio pesada aqui.
- **Header e Footer**: Gerenciados via `wagtail.contrib.settings` (Multisite) e Snippets, desacoplados dos modelos de página.
- **Campos de Layout**: As flags `hide_header` e `hide_footer` vivem no `FlexLayoutMixin`, **não** na `BasePage`. O `FlexLayoutMixin` é um mixin abstrato (mantido sem uso atual — decisão D5) que documenta a intenção de suportar landing pages com layout flexível, e **não** deve ser aplicado em conteúdo (`ConteudoPage`/`AplicativoEducacionalPage`). Ver `core/models.py` e `core/CLAUDE.md`.
- **Localização**: O projeto está configurado para `pt-br` com fuso horário `America/Sao_Paulo`.

## 9) Variáveis de ambiente (exemplo)

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

## 10) Troubleshooting rápido

- Alterações de código não aparecem:
  - Confirme `.:/code` no serviço `web`.
  - Reinicie: `docker compose restart web`.
  - Verifique `WATCHMAN_USE_POLLING=true`.

- Problemas com permissões em volumes (mídia/estáticos): ajustar permissões no host ou UID no compose/Dockerfile.

- Para evitar rebuilds desnecessários:
  - Não altere dependencies nem o Dockerfile sem necessidade.
  - Use `docker compose up -d --no-build` para usar a imagem local.

## Notas finais

- O `docker-compose.yml` está configurado para usar `image: nova-pat-web:latest` e `cache_from` para builds mais rápidos.
- Consulte `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md` para diretrizes de contribuição.

## Documentação de arquitetura e decisões

A documentação técnica e as decisões de arquitetura do projeto vivem em `docs/`. Índice completo:

### Documentos gerais

- [`docs/schema-legado.md`](docs/schema-legado.md) — schema e regras de negócio do sistema legado (Laravel 9 + Postgres), fonte da verdade sobre o que o sistema atual realmente faz.
- [`docs/requisitos-vs-legado.md`](docs/requisitos-vs-legado.md) — cruzamento entre o `Levantamento de Requisitos NOVA PAT` (V1.0) e o comportamento real do legado; separa o que é "modernizar" do que é "construir do zero".
- [`docs/matriz-permissoes-rbac.md`](docs/matriz-permissoes-rbac.md) — matriz de permissões (RBAC) consolidada, mapeando ações por papel (`super-admin`, `admin`, `coordenador`, `editor`, `convidado`).
- [`docs/lgpd-mapeamento-dados.md`](docs/lgpd-mapeamento-dados.md) — mapeamento de dados pessoais (LGPD) por app, com inventário, base legal e decisões pendentes de conformidade.
- [`docs/runbook-backup-dr.md`](docs/runbook-backup-dr.md) — runbook de backup e recuperação de desastres (RTO/RPO, procedimentos, pontos de decisão).

### Architecture Decision Records (ADRs)

- [`docs/adr/README.md`](docs/adr/README.md) — índice e guia de uso dos ADRs (formato Contexto → Decisão → Consequências).
- [`docs/adr/0001-aplicativo-herda-recurso-base-page.md`](docs/adr/0001-aplicativo-herda-recurso-base-page.md) — `AplicativoEducacionalPage` herda `RecursoBasePage`.
- [`docs/adr/0002-canal-fixo-aplicativos.md`](docs/adr/0002-canal-fixo-aplicativos.md) — canal fixo `id=9` para aplicativos (constante `CANAL_ID`).
- [`docs/adr/0003-busca-ambos-por-ids.md`](docs/adr/0003-busca-ambos-por-ids.md) — busca "ambos" combina por IDs, não `union()`.
- [`docs/adr/0004-workflow-aprovacao-role-explicita.md`](docs/adr/0004-workflow-aprovacao-role-explicita.md) — workflow de aprovação por lógica de role explícita (replica RN-L1).
- [`docs/adr/0005-trilha-auditoria-django-simple-history.md`](docs/adr/0005-trilha-auditoria-django-simple-history.md) — trilha de auditoria com `django-simple-history`.
