# series/ — ARCHITECTURE.md

## Papel deste app
`series` existe só para o RF008 (organização de vídeos estilo streaming). É a **única peça de arquitetura nova** discutida até agora que não é transposição de comportamento legado — o legado não tem esse conceito, só uma categoria de canal rotulada "Programas" que **não tem relação** com esta hierarquia (ver `canais/ARCHITECTURE.md`, seção "Resolvido — Programas ≠ Serie", antes de nomear qualquer coisa aqui como "Programa").

Fonte da verdade: `docs/requisitos-vs-legado.md`, seção RF008 (todas as decisões abaixo já foram fechadas lá — este arquivo é a versão operacional pra quem for implementar).

## Fase atual: construção nova (não transposição)
Diferente da maioria dos outros apps, aqui não existe comportamento legado pra replicar. As decisões de modelagem já foram tomadas e fechadas — não redecidir do zero, só implementar.

## Hierarquia
```
Serie → Temporada → ConteudoPage (episódio, do app conteudos)
```

### `Serie(RecursoBasePage)`
- `Page`, **independente de Canal** — decisão fechada: uma série não pertence nem é restrita a um canal específico.
- **Sobrescreve `canal`** (herdado de `RecursoBasePage`) para ser **opcional** (`null=True`, `blank=True`, `on_delete=SET_NULL`) — o campo fica disponível mas não é obrigatório nem usado para séries.
- `sinopse` (texto)
- `capa` (imagem, FK para `wagtailimages.Image`)
- `parent_page_types = ["wagtailcore.Page"]` (séries no nível superior), `subpage_types = ["series.Temporada"]`.
- `get_context()` adiciona as `temporadas` (filhas, `live()`, ordenadas por `numero`).

### `Temporada(Page)`
- Filha de `Serie` (`parent_page_types = ['series.Serie']`).
- `numero` (número da temporada), `sinopse` (texto), `capa` (imagem).
- `subpage_types = ["conteudos.ConteudoPage"]` — episódios são `ConteudoPage`.
- `clean()` valida que `numero` é **único dentro da mesma `Serie`** (via `sibling_of`).
- `get_context()` adiciona os `episodios` (filhos `ConteudoPage`, `live()`, ordenados por `numero_episodio`) e a `serie` pai.

### Episódio — não é uma entidade nova
Um episódio **é** a própria `ConteudoPage` (app `conteudos`, mesmo model de vídeo que já existe), só posicionada na árvore como filha de `Temporada` em vez de `CanalPage`. **Não criar um model `Episodio` separado.**

O campo de ordenação (`numero_episodio`) mora em `ConteudoPage`, no app `conteudos` — é nulo para vídeo avulso, preenchido só quando o conteúdo é filho de uma `Temporada`. Consultar `conteudos/ARCHITECTURE.md` para o campo exato.

## Decisões já fechadas (não reabrir sem motivo novo)

- **Vídeo avulso continua existindo.** `Serie` é opcional — nem todo vídeo precisa pertencer a uma série.
- **Existe conceito de Temporada.** Não é direto `Serie → Episódios`; é `Serie → Temporada → Episódios`.
- **Ordenação é manual**, definida pelo curador (`numero_episodio`), não por data de publicação.
- **Serie é independente de Canal.**
- **Indicador visual de "você está assistindo um episódio"** (breadcrumb Serie › Temporada › Episódio, lista de outros episódios da mesma temporada) é resolvido no **template**, a partir da posição na árvore (`get_parent()`/`get_siblings()` da `ConteudoPage`) — não precisa de campo extra pra isso.

## Dependência entre apps — direção importa
- `series` não precisa importar nada de `conteudos` em Python — a relação de `parent_page_types`/`subpage_types` do Wagtail é declarada por string (`'conteudos.ConteudoPage'`), então não há import circular real, só referência de app_label.
- `conteudos.ConteudoPage.parent_page_types` inclui `'series.Temporada'` — isso é declarado no app `conteudos`, não aqui. Ver `conteudos/ARCHITECTURE.md`.

## O que NÃO fazer neste app
- Não criar model `Episodio` separado — é `ConteudoPage` reaproveitada.
- Não nomear nada aqui como "Programa" — esse termo já tem significado diferente e conflitante no vocabulário da equipe (peça de TV isolada, tipo telejornal). Ver `canais/ARCHITECTURE.md`.
- Não amarrar `Serie` a um `Canal` específico — decisão fechada de que é independente.
- Não ordenar episódio por data de publicação — é número manual do curador.
- Não confundir a categoria "Programas" de um canal (rótulo hardcoded no legado, só nome de exibição de `categories`) com esta hierarquia — são conceitos não relacionados.
