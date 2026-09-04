# search/ — ARCHITECTURE.md

## Papel deste app
`search` implementa a **busca avançada** (RF001) da plataforma. Orquestra a inferência de tipo de conteúdo, a aplicação de filtros multicritério e a paginação dos resultados, cobrindo tanto `ConteudoPage` quanto `AplicativoEducacionalPage`.

Fonte da verdade: `docs/requisitos-vs-legado.md` (RF001), `docs/adr/0003-busca-ambos-por-ids.md`.

## Fase atual: construção
A busca avançada é funcionalidade nova (o legado tinha busca limitada, sem filtro por canal — lacuna confirmada em produção).

## Estrutura do app

### `search/views.py` — view `search()`
- Renderiza a página de busca (`search/search.html`).
- Determina o tipo de busca via `resolver_tipo_busca(request.GET)` → `conteudo` / `aplicativo` / `ambos`.
- Obtém os valores dos filtros selecionados via `get_selected_filter_values(request.GET)` para exibição no template.
- Monta o contexto com todos os filtros disponíveis (canais, tipos, categorias, licenças, componentes, níveis de ensino) — alimentados por consultas dinâmicas ao banco (agregação via ORM, sem trazer datasets brutos para a memória).
- Aplica o FilterSet correspondente ao tipo inferido:
  - `conteudo` → `ConteudoSearchFilterSet` sobre `ConteudoPage.objects.live()`.
  - `aplicativo` → `AplicativoSearchFilterSet` sobre `AplicativoEducacionalPage.objects.live()`.
  - `ambos` → busca em cada modelo separadamente e **combina por IDs** (`values_list('id')` + `Page.objects.filter(id__in=...).specific()`), não via `union()` — ver ADR-003.
- Paginação: **12 resultados por página** (`Paginator(search_results, 12)`).

### `search/services.py` — lógica de decisão de tipo
- `resolver_tipo_busca(get_params) -> TipoBusca` (`Literal['conteudo', 'aplicativo', 'ambos']`).
  - **A inferência NÃO depende de checar em qual tabela um ID existe.** Cada tipo de categoria tem seu próprio parâmetro de URL/formulário (`categoria_conteudo` → conteúdo, `categoria_aplicativo` → aplicativo). O parâmetro preenchido já diz o tipo, sem lookup — elimina o bug de ambiguidade de ID entre tabelas independentes.
  - Preencher `tipo`, `licenca`, `componente` ou `nivel_ensino` → infere `conteudo` (esses campos não existem em aplicativo).
- `get_selected_filter_values(get_params) -> dict` — extrai os valores dos filtros selecionados para o template.

### `search/filters.py` — FilterSets
- `SafeModelChoiceFilter` — `ModelChoiceFilter` que **ignora valores de URL inválidos** (retorna `None`) em vez de lançar erro, protegendo a view contra parâmetros manipulados.
- `BaseSearchFilterSet` — filtros compartilhados: `query` (busca textual via Wagtail search) e `canal`.
  - `filter_search_query`: `queryset.search(value)` retorna `PostgresSearchResults` (não um QuerySet comum), então extrai os IDs e re-filtra o queryset original por esses IDs — permite combinar busca full-text com os demais filtros.
- `ConteudoSearchFilterSet(BaseSearchFilterSet)` — filtros de conteúdo: `tipo`, `categoria_conteudo` (→ `category`), `licenca` (→ `license`), `nivel_ensino` (→ `componentes_curriculares__nivel`), `componente` (→ `componentes_curriculares`).
- `AplicativoSearchFilterSet(BaseSearchFilterSet)` — filtros de aplicativo: `categoria_aplicativo` (→ `category`).

## Dependências entre apps
- `conteudos` — `ConteudoPage`, `Tipo`, `CategoriaConteudo`, `Licenca`.
- `aplicativos` — `AplicativoEducacionalPage`, `AplicativoCategory`.
- `canais` — `CanalPage`.
- `curriculo` — `CurricularComponent`, `NivelEnsino`.

## O que NÃO fazer neste app
- Não usar `media_avaliacao`/`total_avaliacoes` como filtro ou ordenação de busca — decisão fechada (RF011), são só exibição.
- Não fazer a inferência de tipo por lookup de ID (checar em qual tabela o ID existe) — cada parâmetro de URL já identifica o tipo.
- Não usar `union()` no modo "ambos" — combinar por IDs (ADR-003), sacrificando ordenação por relevância em favor de simplicidade.
- Não trazer datasets brutos para a memória do Python — usar agregação via ORM/PostgreSQL.