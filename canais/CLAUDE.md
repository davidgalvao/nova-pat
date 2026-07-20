# canais/ — CLAUDE.md

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

## Model `CanalPage(BasePage)`

Campos confirmados no legado (`Canal.php` + migration):
- `name`, `description`, `slug` (único)
- `is_active` (boolean)
- `token` — texto, **oculto na API/serialização** no legado (`protected $hidden = ['token']`). É credencial de conexão com API externa (provável integração tipo YouTube/Spotify, coerente com a seção de "Integrações Mandatórias" do ToR). Nunca expor esse campo em endpoint público; se for reimplementado, usar campo criptografado, não texto plano.
- `options` (jsonb) — carrega pelo menos:
  - cor do canal (usada em UI, ex: badge colorido por canal)
  - `tipo_conteudo`: lista de IDs de `Tipo` — **regra de negócio real**: um canal pode restringir quais tipos de conteúdo são relevantes/exibidos nele. Não é decoração, é filtro ativo (`getTiposAttribute` no legado consulta `tipos` por esses IDs). Precisa ser preservado — provavelmente como M2M `CanalPage.tipos_permitidos` em vez de jsonb solto, já que Wagtail/Django lidam melhor com relação estruturada do que array de ID dentro de jsonb.

## Relações confirmadas
- `conteudos` — hasMany (via `canal_id` em `ConteudoPage`, FK simples, **não M2M** — ver `docs/requisitos-vs-legado.md`, seção RF008, achado confirmado em produção).
- `aplicativos` — hasMany (via `canal_id` em `AplicativoEducacionalPage`).
- `categories` — hasMany, escopada por canal (`categories.canal_id`), só ativas, só raiz (com subcategorias aninhadas). Esta é a árvore de categoria de **conteúdo**, exclusiva desse domínio (ver `core/CLAUDE.md` — não confundir com a categoria de aplicativo).
- `appsCategories` — hasMany de `AplicativoCategory`, também escopada por canal. Árvore **separada** da anterior (confirma achado do `core/CLAUDE.md`: categoria de conteúdo ≠ categoria de aplicativo, mesmo dentro do mesmo canal).
- `filterCategoryCC` — M2M com `CurricularComponentCategory` via pivot `canal_cc_categories`. Um canal pode restringir quais categorias de componente curricular são relevantes pra ele (mesmo padrão de restrição de `tipo_conteudo`). Depende do app `curriculo` — coordenar com quem implementar aquele app antes de fechar essa M2M.

## ✅ Resolvido — "Programas" (rótulo de categoria) ≠ `Serie` (entidade nova do RF008)
Confirmado com o dono do produto: o rótulo hardcoded "Programas" no legado (`Canal::getCategoryNameAttribute()`) se refere ao jargão de TV — uma peça televisiva isolada (ex: um telejornal é "um programa"), **não** a uma hierarquia de série/temporada/episódio. É só o nome de exibição da árvore de `categories` daquele canal, sem relação com o RF008.

Para não colidir os dois conceitos, a entidade nova do RF008 foi **renomeada de `Programa` para `Serie`**:

```
Serie → Temporada → ConteudoPage (episódio)
```

`canais/CLAUDE.md` não precisa de mudança de model por causa disso — é só um alerta de nomenclatura para quem for implementar o app `series/` (anteriormente cogitado como `programas/`). A categoria "Programas" de um canal continua sendo `categories` comum, sem relação com `Serie`.

## O que NÃO fazer neste app
- Não expor `token` em nenhum serializer/API pública.
- Não modelar `tipo_conteudo` (filtro de tipo permitido por canal) como jsonb solto se puder ser M2M estruturada — jsonb aqui é característica de limitação do Eloquent/Laravel antigo, não uma escolha de design a preservar.