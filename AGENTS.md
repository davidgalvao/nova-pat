# AGENTS.md — Nova PAT

Instruções para agentes de IA (DSH, Cursor, Cline) trabalhando neste projeto.
Para documentação humana, veja `README.md` e `docs/`.

## Stack
- Django 6.0 + Wagtail 8.0
- Postgres via Docker (`docker compose exec web <comando>`)
- StreamField para composição editorial; Tailwind via CDN
- i18n: `pt-br`, `America/Sao_Paulo`

## Comandos do projeto
- Testes: `docker compose exec web pytest -x -q`
- Migrações: `docker compose exec web python manage.py makemigrations && ... migrate`
- Shell: `docker compose exec web python manage.py shell`
- Verificar migrações: `docker compose exec web python manage.py migrate --check`

## Convenções de código

### Wagtail / blocos
- Blocos StreamField vivem em `core/blocks.py`.
- Templates de bloco vivem em `core/templates/blocks/<nome>_block.html`.
- Nomear classe de bloco como `<Adjetivo><Substantivo>Block`.
- Blocos que dependem do contexto da página (parent) leem 
  `parent_context["page"]`; fora de contexto, retornam vazio sem quebrar.
- Sempre registrar blocos novos em `HomeStreamBlock`.

### Templates Django — armadilhas
- `{# #}` só funciona em **linha única**. Para comentários multilinha, use 
  `{% comment %} ... {% endcomment %}`. Comentários multilinha em `{# #}` 
  vazam como texto na página.

### Models e migrações
- Canal é OBRIGATÓRIO em todo `ConteudoPage` / `AplicativoEducacionalPage` 
  (FK `PROTECT`, sem `null=True`).
- Canal NÃO restringe tipos de mídia nem categorias — decisões D2/D4. Não 
  reintroduzir `tipos_permitidos` nem `categorias_componente_permitidas`.
- Higiene de migração (detalhes em `CONTRIBUTING.md`):
  nunca editar migração aplicada; nunca deletar arquivo sem desmarcar no banco.

### BasePage e mixins
- `core.BasePage`: só metadados (SEO/OpenGraph). Não adicionar StreamField 
  nem lógica de negócio.
- `FlexLayoutMixin`: abstrato, mantido sem uso (decisão D5). Não aplicar em 
  conteúdo.

## Antes de commitar
1. `docker compose exec web pytest -x -q`
2. `docker compose exec web python manage.py migrate --check`
3. `docker compose exec web python manage.py makemigrations --check --dry-run`

## Git
- Por enquanto, commit direto em `main` (projeto solo).
- Quando a equipe crescer: kanban + branches por feature.

## Padrões de entrega (o que o agente deve produzir)
- Antes de aplicar código: mostrar o diff e aguardar OK.
- Docstrings em Python: propósito, contexto de uso, comportamento 
  com/sem parent_context.
- Testes para toda lógica nova (models, blocos, view).
- Não inventar CSS: reutilizar classes dos blocos existentes.