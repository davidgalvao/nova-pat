# AGENTS.md — Nova PAT

Instruções para agentes de IA (DSH, Cursor, Cline) trabalhando neste projeto.
Para documentação humana, veja `README.md` e `docs/`.

## Contexto do projeto
- **Transposição de stack**, não greenfield: o sistema legado (Laravel + Vue.js)
  está **em produção** e está sendo reescrito em Django + Wagtail.
- Por isso **não existe "MVP"**: o critério de pronto é **paridade com o
  comportamento do legado**. Fonte da verdade do comportamento antigo:
  `docs/schema-legado.md` e `docs/requisitos-vs-legado.md`.
- Onde o legado tiver anti-padrão documentado, **não replicar** — seguir o que os
  docs definem para a NOVA PAT (`docs/requisitos-vs-legado.md`).
- Hierarquia das fontes, em caso de divergência:
  1. **ADRs** (`docs/adr/`) — vencem em decisão de arquitetura. Antes de alterar
     comportamento coberto por um ADR, ler o ADR; não reabrir decisão fechada sem
     motivo de produto novo.
  2. **`<app>/ARCHITECTURE.md`** — versão operacional viva do app; deve ser
     atualizado para refletir o ADR quando os dois divergirem.
  3. `docs/` global.
- As regras que antes viviam em `.roo/` (não versionado, invisível para o time)
  agora estão **neste arquivo**. O `.roo/` pode continuar no disco para o Roo
  Code, mas **`AGENTS.md` é a fonte de verdade**.

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

## Ambiente de execução (Docker)
- Toda a aplicação roda **exclusivamente** em contêineres via `docker compose`.
- **PROIBIDO** rodar `python`, `pip`, `pytest` ou `manage.py` direto no host.
- O serviço do backend/Django se chama **`web`** (NUNCA `backend`). Leia o
  `docker-compose.yml` antes de assumir nomes de serviços.

## Como investigar (leitura antes de escrita)
- Antes de propor qualquer código, ler os arquivos de referência citados no plano.
- Se um arquivo não existir no caminho indicado, **PARAR e perguntar**.
- **Buscar primeiro, ler depois:** priorizar busca — semântica/índice de código
  quando o harness oferecer, senão `grep`/`glob` — antes de abrir arquivos ou
  listar diretórios. Não carregar arquivos inteiros na memória sem antes localizar
  as funções/classes/rotas relevantes: filtrar o contexto primeiro, com termos de
  busca específicos.
- Ao renomear ou remover um model/símbolo, buscar referências no **projeto
  inteiro** (`grep -rn` ou equivalente): todos os apps, incluindo templates,
  admin/wagtail_hooks, forms, filters e testes. **Listar os arquivos encontrados
  antes de editar e confirmar o escopo com quem pediu a mudança.**

## Convenções de código

### Wagtail / blocos
- Blocos StreamField vivem em `core/blocks.py`.
- Templates de bloco vivem em `core/templates/blocks/` (a maioria em
  `<nome>_block.html`, mas não todos — siga o padrão do arquivo mais parecido que
  já exista no diretório).
- Nomear a classe do bloco com o sufixo `Block` e um nome descritivo
  (ex.: `HeroBlock`, `FeatureGridBlock`, `UltimoConteudoPlayerBlock`).
- Blocos que dependem do contexto da página (parent) leem 
  `parent_context["page"]`; fora de contexto, retornam vazio sem quebrar.
- Sempre registrar blocos novos em `HomeStreamBlock`.

### Arquitetura de apresentação
- O front-end é **Wagtail/Django Templates**. **NÃO** assumir SPA separado
  (React/Vue/Node) — o Vue do legado não é transposto como SPA.
- Variações de exibição de mídia (`ConteudoPage`) são resolvidas por método do
  model (`get_template()`), nunca por `if` no template nem pelo slug do `tipo`.

### Templates Django — armadilhas
- `{# #}` só funciona em **linha única**. Para comentários multilinha, use 
  `{% comment %} ... {% endcomment %}`. Comentários multilinha em `{# #}` 
  vazam como texto na página.
- Depois de editar template, rodar `python manage.py check` **antes** da suíte —
  pega sintaxe quebrada sem o ciclo completo de testes.
- Balancear as tags manualmente em templates grandes: todo `{% if %}`/`{% for %}`/
  `{% block %}` precisa do fechamento correspondente. `{% for %}` só aceita
  `{% empty %}` ou `{% endfor %}` — um `{% else %}` solto indica `{% for %}` não
  fechado.
- Não renderizar variável que a view não envia no `context`: o Django não avisa,
  a variável vira string vazia e mascara erro de lógica.
- Não misturar dois modos de renderização no mesmo bloco ("se existe X renderiza
  de um jeito, senão de outro") sem pedido explícito — é a origem mais comum de
  tags desbalanceadas.

### Models e dados
- Canal é OBRIGATÓRIO em todo `ConteudoPage` / `AplicativoEducacionalPage` 
  (FK `PROTECT`, sem `null=True`).
- **Exceção conhecida e deliberada:** `series.Serie` sobrescreve `canal` para
  `null=True`/`SET_NULL` (série é independente de canal — decisão fechada, ver
  `series/ARCHITECTURE.md`). Não "corrigir" para `PROTECT` sem confirmar.
- Canal NÃO restringe tipos de mídia nem categorias — decisões D2/D4 de `canais/ARCHITECTURE.md`. Não 
  reintroduzir `tipos_permitidos` nem `categorias_componente_permitidas`.
  (Cuidado: `D2` também nomeia o papel `editor` em `docs/adr/README.md` — são
  numerações diferentes.)
- Não usar `null=True` em FK para "facilitar teste".
- **Nunca** inferir de qual model/tabela um registro veio apenas pelo **ID**: dois
  models com auto-increment próprio podem ter o mesmo número. Exigir
  desambiguação explícita (campo/parâmetro/tipo dedicado) — nunca "existe na
  tabela X? então é X".
- Ao encontrar models com nomes parecidos (ex.: `CategoriaConteudo` vs
  `AplicativoCategory`), **perguntar** antes de assumir que são o mesmo conceito
  ou que são intercambiáveis.

### Qualidade de código Python
- Type hints explícitos em funções e métodos.
- Datas sempre em UTC com `timezone.now()`, de forma consistente.
- Evitar magic numbers: extrair constantes/thresholds para `constants.py` do app
  (criar quando fizer sentido) ou `settings`. Exemplo real: `CANAL_ID` hoje mora
  em `aplicativos/models.py`.
- Tratar exceções específicas (`DatabaseError`, `ValidationError`,
  `ObjectDoesNotExist`) e registrar logs estruturados.

### Bibliotecas — não reinventar a roda
- Preferir bibliotecas maduras do ecossistema Django/Wagtail a implementar do zero.
- Tags: `django-taggit`. Busca: busca nativa do Wagtail (evitar tsvector manual
  se o Wagtail Search cobrir).
- Agregações (`Count`, `Sum`, `Avg`, `annotate`, `aggregate`) direto no ORM/
  Postgres — não trazer dataset bruto para a memória do Python.
- Planilhas Google: `gspread`.

### BasePage e mixins
- `core.BasePage`: só metadados (SEO/OpenGraph). Não adicionar StreamField 
  nem lógica de negócio.
- `FlexLayoutMixin`: abstrato, mantido sem uso (decisão D5). Não aplicar em 
  conteúdo.

## Testes (disciplina obrigatória)
- Rodar a suíte **do app afetado por inteiro** (ex.: `pytest search/tests/ -v`),
  não só o teste que motivou a mudança.
- **Nunca** declarar tarefa concluída sem ter rodado os testes **por último**. Se
  alterou código depois da última rodada (mesmo algo pequeno), rodar de novo.
  "Deveria funcionar" não substitui "rodei e confirmei".
- Reportar sempre, sem ser pedido: quantos passaram, quantos falharam e o nome de
  cada teste que falhou.
- Se um teste que passava começar a falhar após uma correção não relacionada (ou
  vice-versa), **sinalizar explicitamente** — indica acoplamento/ambiguidade; não
  corrigir em silêncio.

## Antes de commitar
1. `docker compose exec web pytest -x -q`
2. `docker compose exec web python manage.py migrate --check`
3. `docker compose exec web python manage.py makemigrations --check --dry-run`

### Higiene de migrações
Contexto completo em `CONTRIBUTING.md`. Migração aplicada é **imutável**:
- Nunca editar arquivo de migração já aplicada — criar migração NOVA que corrige.
  (Exceção: migração criada na **mesma sessão** e ainda **não aplicada** pode ser
  editada livremente.)
- Nunca deletar arquivo de migração já aplicado sem antes desmarcá-lo no banco:
  1. `python manage.py migrate <app> <migração_anterior> --fake`
  2. deletar o arquivo
  3. confirmar com `python manage.py showmigrations <app>`
- Após reorganizar migrações, limpar registros órfãos em `django_migrations` via
  `MigrationRecorder.Migration.objects.filter(...).delete()`.
- Violar isso não quebra só o seu ambiente: quebra o `pytest` (o banco de teste é
  criado a partir das migrações), o CI, o ambiente de outro dev e **produção**.

## Git
- **Fluxo atual (projeto solo):** commit direto em `main`. O fluxo de
  fork + branch `feat/`/`fix/` + PR descrito em `CONTRIBUTING.md` ainda **não** se
  aplica — quando houver mais de uma pessoa, migrar para ele.
- Nunca `git reset --hard`, `git clean -fd`, `git checkout .` ou `git push` sem
  OK explícito. Em operação destrutiva, mostrar o comando primeiro e aguardar.

## Padrões de entrega (o que o agente deve produzir)
- Antes de aplicar código: mostrar o diff e aguardar OK.
- Docstrings em Python: propósito, contexto de uso, comportamento 
  com/sem parent_context.
- Testes para toda lógica nova (models, blocos, view).
- Não inventar CSS: reutilizar classes dos blocos existentes.

## Docker — comandos permitidos

Você agora TEM Docker CLI + socket. Use com responsabilidade.

### Permitido sem aprovação
- `docker compose -f /home/dgalvao/nova-pat/docker-compose.yml exec -T web pytest -x -q`
- `docker compose ... exec -T web python manage.py <comando>`
- `docker compose ... logs web --tail 30`
- `docker compose ... restart web`
- `docker compose ... ps`

`-T` (sem TTY) é obrigatório em **`exec`** — você não tem terminal interativo.
`-T` **não existe** para `logs`, `ps` ou `restart` (é flag exclusiva de `exec`);
usá-la ali falha com `unknown shorthand flag: 'T'`.

Se o diretório de trabalho não for `/home/dgalvao/nova-pat`, acrescente
`-f /home/dgalvao/nova-pat/docker-compose.yml` (os `...` acima abreviavam isso).
Dentro do diretório do projeto, `docker compose exec web <comando>` é válido.

### Exige minha aprovação explícita
- `docker compose down` ou `stop`
- `docker system prune`, `docker volume rm`, `docker rmi`
- Qualquer coisa que toque em `db` ou `postgres_data`
- `docker rm` ou `docker kill`

### Nunca
- `docker compose exec` SEM `-T`
- Comandos destrutivos em lote (`rm -rf`, `docker system prune -a`)

## Mídia externa
- Gestor cola URL do navegador (youtube.com/watch, youtu.be, vimeo.com/ID)
- NUNCA passar essa URL direto para `<iframe src>`
- Sempre usar {% embed %} ou get_embed() do wagtail.embeds
- Testar com URLs reais: YouTube watch, YouTube curto, YouTube shorts, Vimeo

## Antes de propor código que usa biblioteca externa
1. Ler a doc oficial da lib
2. Testar com 2-3 casos reais (não só sintaxe)
3. Se algum caso falhar, mostrar qual e como contornar
4. Só então propor o diff

Aplicado a: wagtail.embeds, faker-file, Playwright, qualquer lib nova.
