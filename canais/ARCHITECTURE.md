# canais/ — ARCHITECTURE.md

## Papel deste app
`canais` modela o agrupador de topo do site (TV Anísio Teixeira, Rádio Anísio Teixeira, EMITEC, Recursos Educacionais Abertos, Projetos Artísticos — nomes confirmados em produção). É `Page` hierárquica no Wagtail (`CanalPage`), pai de conteúdo/aplicativo.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`.

## Fase atual: transposição
Canal em si é estrutura estável do legado — o trabalho aqui é replicar comportamento existente, não inventar. As únicas mudanças de escopo (não deste app, mas que o afetam) são: RF001 (filtro de busca por canal, hoje ausente) e RF008 (Programa/Temporada, ver seção de risco de nome abaixo).

## ⚠️ Aviso de fonte: repo do Nico pode estar desatualizado
O repositório `nikoz84/plataforma-anisio-teixeira`, usado como referência de schema/regras neste documento, **pode não refletir fielmente o estado atual de produção** — pode haver defasagem entre o código público e o que está rodando hoje. Onde houver divergência entre o que está aqui e o que se observa em produção (admin, telas, comportamento real), **produção é a fonte de verdade**, não o código do Nico. Sempre que possível, confirmar visualmente em produção antes de tomar decisão de modelagem que dependa de detalhe fino do schema.

## Lista real de canais em produção (12, confirmados via menu, não pelo código)
1. Recursos Educacionais
2. TV Anísio Teixeira
3. Rádio Anísio Teixeira
4. Emitec
5. Projetos Artísticos
6. Sites Temáticos
7. Blog da Rede
8. Aplicativos Educacionais
9. Educação Profissional e Tecnológica
10. Rotinas de Estudo
11. Canal das Universidades
12. Canal Anísio Teixeira

**Não presumir que todos os 12 são registros `canais` "normais" com conteúdo próprio hospedado.** Pelo menos dois têm indício forte de serem espelhamento de sistema externo via API (explica o campo `token` do model):
- **Blog da Rede** — bate com `Services/WordpressService.php` no legado, provável integração com WordPress externo.
- **Sites Temáticos** e possivelmente **Aplicativos Educacionais** — podem ser agregadores/redirecionamento em vez de conteúdo nativo; `Services/ColaborativusService.php` também sugere integração com sistema externo (Colaborativus, mencionado na análise inicial do domínio).

Antes de migrar cada canal, checar individualmente se ele é conteúdo nativo (segue o fluxo normal de `ConteudoPage`) ou espelho de API externa (precisa de lógica de sincronização própria, fora do escopo de "transposição simples"). Isso é decisão por canal, não uma regra geral — não implementar até confirmar caso a caso.

## Anomalia observada em produção (não investigada, só registrada)
Em produção, os canais **"Blog da Rede"** e **"TV Anísio Teixeira"** exibem a mesma listagem de conteúdos ao navegar. Comportamento inesperado — o esperado seria cada canal mostrar só seus próprios `conteudos` (escopados por `canal_id`). Não investigado a fundo ainda; pode ser:
- bug de filtro/query específico dessas duas páginas no legado,
- ou os dois canais compartilharem os mesmos registros de conteúdo por decisão editorial antiga (menos provável, dado que `canal_id` é FK única por conteúdo, não M2M — ver seção RF008 em `docs/requisitos-vs-legado.md`).

Não assumir causa sem investigar o código de exibição desses dois canais especificamente quando for migrar. Se o comportamento for reproduzido sem querer na NOVA PAT, será regressão silenciosa difícil de notar — vale um teste manual específico comparando as duas listagens ao final da fase de transposição.

## Canais candidatos a desativação (decisão de negócio pendente, não bloqueia a fase atual)
Alguns dos 12 canais podem ser remanescentes da época da pandemia e não fazer mais sentido manter ativos na NOVA PAT. O legado já tem `is_active` (boolean) no model `Canal`, o que cobre bem esse caso — desativar não precisa apagar conteúdo histórico, só tirar de circulação/navegação. Essa decisão (quais canais desativar) é de negócio, não técnica, e **não bloqueia a modelagem atual** — o campo `is_active` já dá suporte a isso sem mudança de schema. Revisitar quando o levantamento de quais canais seguem ativos estiver fechado.

## Glossário — o que "ativo" significa neste app
"Ativo" no contexto de `canais` é **apenas o booleano `is_active`** do `CanalPage`. Não existe entidade "CanalPage pai" nem "canal default" — canais são filhos diretos de `root` (`parent_page_types = ["wagtailcore.Page"]`). Páginas internas com checkbox "ativo" marcado **não** são canais — são páginas comuns do Wagtail. Não inferir relação de hierarquia de canal a partir de `is_active` de outras páginas.

## Model `CanalPage(BasePage)`

Campos implementados (ver `canais/models.py`):
- `name` (único), `description` (RichTextField), `slug` (único)
- `is_active` (boolean)
- `token` — texto, **oculto na API/serialização** no legado (`protected $hidden = ['token']`). É credencial de conexão com API externa (provável integração tipo YouTube/Spotify, coerente com a seção de "Integrações Mandatórias" do ToR). Nunca expor esse campo em endpoint público; se for reimplementado, usar campo criptografado, não texto plano.
- `options` (JSONField) — carrega configurações flexíveis (ex: cor do canal usada em UI, badge colorido por canal).
- `body` (StreamField) — **composição editorial do canal** (ver seção abaixo).

Configuração de árvore de páginas:
- `parent_page_types = ["wagtailcore.Page"]` — canais ficam no nível superior (filhos de root).
- `subpage_types = ["conteudos.ConteudoPage", "aplicativos.AplicativoEducacionalPage"]`.

`get_context()` adiciona ao contexto os `conteudos` e `aplicativos` deste canal (filhos diretos, `live()`, ordenados por `-first_published_at`).

## Composição editorial do canal (StreamField `body`)

**Decisão D1**: o `CanalPage` tem poder de composição editorial igual ao da `HomePage`. O gestor escolhe quais blocos aparecem na página do canal e em que ordem, via StreamField, sem depender de template hardcoded.

- **Reutiliza os mesmos blocos da HomePage** (`HeroBlock`, `FullBannerBlock`, `CarrosselCategoriaBlock`, `DestaquesManuaisBlock`, `FeatureGridBlock` — via `core.blocks.HomeStreamBlock`). Não duplicar definição de blocos: se um bloco muda, muda para Home e Canal simultaneamente.
- **Coexistência com filhos**: os filhos (`ConteudoPage`, `AplicativoEducacionalPage`) continuam existindo como páginas reais (URL própria, SEO, sitemap). O `body` é o **layout de entrada** do canal, onde o gestor pode destacar conteúdo, incluir blocos de listagem dinâmica (que consultam `self.conteudos` / `self.get_children()`), compor chamadas para outras seções.
- **`get_context()` continua entregando** `conteudos` e `aplicativos`, e o template do canal renderiza `body` como estrutura principal. Blocos de listagem consomem esses dados do contexto quando precisam.

## Relações confirmadas
- `conteudos` — hasMany (via `canal_id` em `ConteudoPage`, FK simples, **não M2M** — ver `docs/requisitos-vs-legado.md`, seção RF008, achado confirmado em produção).
- `aplicativos` — hasMany (via `canal_id` em `AplicativoEducacionalPage`).
- `categories` — hasMany, escopada por canal (`categories.canal_id`), só ativas, só raiz (com subcategorias aninhadas). Esta é a árvore de categoria de **conteúdo**, exclusiva desse domínio (ver `core/ARCHITECTURE.md` — não confundir com a categoria de aplicativo).
- `appsCategories` — hasMany de `AplicativoCategory`, também escopada por canal. Árvore **separada** da anterior (confirma achado do `core/ARCHITECTURE.md`: categoria de conteúdo ≠ categoria de aplicativo, mesmo dentro do mesmo canal).

## ✅ Resolvido — "Programas" (rótulo de categoria) ≠ `Serie` (entidade nova do RF008)
Confirmado com o dono do produto: o rótulo hardcoded "Programas" no legado (`Canal::getCategoryNameAttribute()`) se refere ao jargão de TV — uma peça televisiva isolada (ex: um telejornal é "um programa"), **não** a uma hierarquia de série/temporada/episódio. É só o nome de exibição da árvore de `categories` daquele canal, sem relação com o RF008.

Para não colidir os dois conceitos, a entidade nova do RF008 foi **renomeada de `Programa` para `Serie`**:

```
Serie → Temporada → ConteudoPage (episódio)
```

`canais/ARCHITECTURE.md` não precisa de mudança de model por causa disso — é só um alerta de nomenclatura para quem for implementar o app `series/` (anteriormente cogitado como `programas/`). A categoria "Programas" de um canal continua sendo `categories` comum, sem relação com `Serie`.

## ❌ Descontinuado — restrições por canal (removidas)

Duas decisões de arquitetura fecharam a remoção de M2Ms que restringiam conteúdo por canal. O princípio comum: **regras editoriais ficam no nível do conteúdo, não do canal**. Canal é agrupador — não filtro do que pode existir nele.

- **`tipos_permitidos`** (era M2M para `conteudos.Tipo`) — **removida (D2)**. Sem motivo de negócio para um canal limitar quais tipos de mídia (vídeo, áudio, PDF...) podem existir nele. O gestor decide caso a caso.
- **`categorias_componente_permitidas`** (era M2M para `curriculo.CurricularComponentCategory`) — **removida (D4)**. Mesma lógica: dado morto no legado, sem uso real na filtragem. Categorias de componente curricular são escolhidas por conteúdo, não restringidas por canal.

Migrações: `0002_canalpage_body.py` e `0003_remove_canalpage_categorias_componente_permitidas.py`. A `tipos_permitidos` foi removida junto com a deleção da migração que a criava (`0002_initial.py`), sem deixar churn.

## Invariante — `canal` obrigatório em todo recurso

Todo `ConteudoPage` e `AplicativoEducacionalPage` DEVE ter um `CanalPage` vinculado. O campo `canal` é `ForeignKey(..., on_delete=PROTECT)`, sem `null=True`, sem `blank=True`. O gestor escolhe o canal em uma lista no momento do cadastro.

Consequências:
- Não criar conteúdo "órfão" de canal.
- Não tornar o campo opcional "para facilitar" — se a UI precisa permitir rascunho, isso é outro problema (resolver via fluxo de publicação do Wagtail), não justifica tornar o FK nulo.
- `PROTECT` impede deletar canal com conteúdo vinculado — preservar.

## O que NÃO fazer neste app
- Não expor `token` em nenhum serializer/API pública.
- Não restringir tipos de mídia por canal (removido em D2 — regra editorial é do conteúdo, não do canal).
- Não restringir categorias de componente curricular por canal (removido em D4 — mesma lógica).
- Não usar `null=True` / `blank=True` no FK `canal` de recursos (ver invariante acima).
- Não duplicar definição de blocos StreamField — `body` reutiliza `core.blocks.HomeStreamBlock`.