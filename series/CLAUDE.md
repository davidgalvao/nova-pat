# series/ — CLAUDE.md

## Papel deste app
`series` existe só para o RF008 (organização de vídeos estilo streaming). É a **única peça de arquitetura nova** discutida até agora que não é transposição de comportamento legado — o legado não tem esse conceito, só uma categoria de canal rotulada "Programas" que **não tem relação** com esta hierarquia (ver `canais/CLAUDE.md`, seção "Resolvido — Programas ≠ Serie", antes de nomear qualquer coisa aqui como "Programa").

Fonte da verdade: `docs/requisitos-vs-legado.md`, seção RF008 (todas as decisões abaixo já foram fechadas lá — este arquivo é a versão operacional pra quem for implementar).

## Fase atual: construção nova (não transposição)
Diferente da maioria dos outros apps, aqui não existe comportamento legado pra replicar. As decisões de modelagem já foram tomadas e fechadas — não redecidir do zero, só implementar.

## Hierarquia
```
Serie → Temporada → ConteudoPage (episódio, do app conteudos)
```

### `Serie(RecursoBasePage)`
- `Page`, **independente de Canal** — decisão fechada: uma série não pertence nem é restrita a um canal específico.
- `sinopse` (texto)
- `capa` (imagem)

### `Temporada(Page)`
- Filha de `Serie` (`parent_page_types = ['series.Serie']`).
- `numero` (número da temporada).

### Episódio — não é uma entidade nova
Um episódio **é** a própria `ConteudoPage` (app `conteudos`, mesmo model de vídeo que já existe), só posicionada na árvore como filha de `Temporada` em vez de `CanalPage`. **Não criar um model `Episodio` separado.**

O campo de ordenação (`numero_episodio`) mora em `ConteudoPage`, no app `conteudos` — é nulo para vídeo avulso, preenchido só quando o conteúdo é filho de uma `Temporada`. Consultar `conteudos/CLAUDE.md` para o campo exato.

## Decisões já fechadas (não reabrir sem motivo novo)

- **Vídeo avulso continua existindo.** `Serie` é opcional — nem todo vídeo precisa pertencer a uma série.
- **Existe conceito de Temporada.** Não é direto `Serie → Episódios`; é `Serie → Temporada → Episódios`.
- **Ordenação é manual**, definida pelo curador (`numero_episodio`), não por data de publicação.
- **Serie é independente de Canal.**
- **Indicador visual de "você está assistindo um episódio"** (breadcrumb Serie › Temporada › Episódio, lista de outros episódios da mesma temporada) é resolvido no **template**, a partir da posição na árvore (`get_parent()`/`get_siblings()` da `ConteudoPage`) — não precisa de campo extra pra isso.

## Dependência entre apps — direção importa
- `series` não precisa importar nada de `conteudos` em Python — a relação de `parent_page_types`/`subpage_types` do Wagtail é declarada por string (`'conteudos.ConteudoPage'`), então não há import circular real, só referência de app_label.
- `conteudos.ConteudoPage.parent_page_types` inclui `'series.Temporada'` — isso é declarado no app `conteudos`, não aqui. Ver `conteudos/CLAUDE.md`.

## O que NÃO fazer neste app
- Não criar model `Episodio` separado — é `ConteudoPage` reaproveitada.
- Não nomear nada aqui como "Programa" — esse termo já tem significado diferente e conflitante no vocabulário da equipe (peça de TV isolada, tipo telejornal). Ver `canais/CLAUDE.md`.
- Não amarrar `Serie` a um `Canal` específico — decisão fechada de que é independente.
- Não ordenar episódio por data de publicação — é número manual do curador.
- Não confundir a categoria "Programas" de um canal (rótulo hardcoded no legado, só nome de exibição de `categories`) com esta hierarquia — são conceitos não relacionados.
