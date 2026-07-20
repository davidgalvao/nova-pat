# curriculo/ — CLAUDE.md

## Papel deste app
`curriculo` modela a estrutura pedagógica que classifica o conteúdo: nível de ensino e componente curricular (disciplina). É consumido por `conteudos` via M2M (`ConteudoPage.componentes_curriculares`), mas a estrutura em si — níveis, categorias de componente, componentes — mora aqui.

**Correção de suposição anterior**: em conversa passada, assumiu-se que a plataforma cobria só "1º ao 3º ano do Ensino Médio". Isso está **errado** — confirmado em produção (URLs `pat.educacao.ba.gov.br/rotinas-de-estudo/ensino-fundamental-1` e `.../rotinas-de-estudo/ensino-medio`) que a plataforma cobre **Ensino Fundamental e Ensino Médio**, não só Médio. O schema legado (`niveis_ensino.name`, texto livre) não define os valores exatos — a granularidade real (se é "Fundamental I" e "Fundamental II" como blocos, ou nível por ano individual) precisa ser confirmada direto no admin de produção antes de povoar os dados na NOVA PAT. Não presumir a lista completa sem checar.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`.

## Fase atual: transposição
Estrutura estável do legado, sem mudança de escopo pedida no levantamento de requisitos. Só transpor.

## Hierarquia confirmada no schema legado

```
NivelEnsino (nome — ex: "1º ano do Ensino Médio")
CurricularComponentCategory (nome — agrupador de disciplinas)
CurricularComponent (nome, FK category, FK nivel) — cada componente pertence a EXATAMENTE UM nível e UMA categoria
```

**Atenção a um detalhe do schema que não é intuitivo**: `CurricularComponent` tem FK direta pra `NivelEnsino` (`nivel_id`) e pra `CurricularComponentCategory` (`category_id`) — **não são M2M entre si**. Um componente curricular (ex: "Matemática — 1º ano") é uma combinação fixa de disciplina + nível, não uma disciplina genérica reaproveitada entre níveis. Isso significa que "Matemática" do 1º ano e "Matemática" do 2º ano são **registros diferentes** de `CurricularComponent`, não o mesmo registro com nível variável.

> Se ao migrar os dados surgir muita duplicação de nome (ex: "Matemática" repetido 3x, uma por ano), isso é esperado pelo desenho do schema legado, não um erro de importação.

## Models

### `NivelEnsino` (Snippet)
- `name`

### `CurricularComponentCategory` (Snippet)
- `name` — agrupador (ex: "Ciências da Natureza", "Linguagens").

### `CurricularComponent` (Snippet)
- `name`
- `category` — FK para `CurricularComponentCategory`.
- `nivel` — FK para `NivelEnsino`.

## Relação com `conteudos`
`ConteudoPage.componentes_curriculares` é M2M direta para `CurricularComponent` (não para `NivelEnsino` — filtrar por nível de ensino na busca significa fazer join através de `CurricularComponent.nivel`, não via campo direto no conteúdo). Ver RN-L5 em `conteudos/CLAUDE.md`: mínimo 1 componente curricular por conteúdo é regra pedagógica obrigatória, não opcional.

## Relação com `canais` — filtro de categoria por canal
Existe uma M2M entre `CanalPage` e `CurricularComponentCategory` (pivot `canal_cc_categories` no legado) — um canal pode restringir quais **categorias** de componente curricular são relevantes para ele (mesmo padrão de restrição de `tipo_conteudo` visto em `canais/CLAUDE.md`). Essa M2M já foi apontada em `canais/CLAUDE.md` como dependente deste app — implementar aqui como `CurricularComponentCategory.canais` (`ManyToManyField` para `canais.CanalPage`) ou o inverso, e confirmar a direção mais natural no Wagtail com quem for codar.

## O que NÃO fazer neste app
- Não tratar `CurricularComponent` como reaproveitável entre níveis — é FK fixa pra um nível só, replicar essa rigidez do legado, não "corrigir" pra M2M sem que isso seja pedido.
- Não adicionar filtro de busca por `NivelEnsino` direto no `ConteudoPage` sem passar pelo join via `CurricularComponent` — não existe relação direta conteúdo↔nível no legado.
- Não esquecer o mínimo de 1 componente curricular obrigatório por conteúdo (regra vive em `conteudos`, mas depende deste app existir primeiro).
