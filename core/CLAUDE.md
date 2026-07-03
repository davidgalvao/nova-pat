# core/ — CLAUDE.md

## Papel deste app
`core` contém apenas abstrações e taxonomias **realmente compartilhadas** por mais de um app do domínio. Não é um "app de tudo genérico" — cada model aqui só existe se pelo menos dois outros apps dependem dele. Se uma taxonomia serve só a `conteudos`, ela mora em `conteudos`, não aqui.

Fonte da verdade para decisões deste app: `docs/schema-legado.md` e `docs/requisitos-vs-legado.md` (raiz do projeto). Não reintroduza regra de negócio aqui sem checar esses dois documentos primeiro.

## Fase atual: transposição
Estamos replicando o comportamento do sistema legado (Laravel), não criando funcionalidade nova. Se uma decisão de modelagem aqui parecer "faltando", confira se o RF correspondente em `docs/requisitos-vs-legado.md` está marcado ✅ (transpor) ou 🆕/⚠️ (não é escopo deste momento).

## Models deste app

### `BasePage(Page)` — abstrata
Base de SEO/Open Graph para **todas** as páginas do site. Contém *apenas*:
- `og_title`, `og_description`, `og_image` (Open Graph)
- properties `social_title`, `social_description`, `canonical_url` (fallback em cascata: campo customizado → SEO → título/descrição padrão da página)

**Não adicione campos de layout (hide_header, hide_footer, custom_body_class, etc.) aqui.** Esses campos já foram removidos de uma versão anterior desta classe porque vazavam pra todo tipo de página, incluindo conteúdo educacional, onde esconder header/footer não faz sentido de negócio. Se precisar de campos de layout flexível, crie um mixin/classe abstrata separada (`FlexLayoutMixin`) e aplique só nas páginas que realmente precisam (landing pages soltas, não conteúdo).

Não adicione métodos vazios tipo `get_context()` só de placeholder — adicione só quando houver uso real.

### `RecursoBasePage(BasePage)` — abstrata
Base para as duas entidades de recurso educacional que compartilham campos reais: `ConteudoPage` (app `conteudos`) e `AplicativoPage` (app `aplicativos`).

**Confirmado no schema legado** — o que é de fato compartilhado entre `conteudos` e `aplicativos`:
- `canal` (FK para `CanalPage`, app `canais`) — os dois têm.
- `autor` (FK para usuário publicador, `user_id` no legado) — os dois têm.

**O que NÃO é compartilhado** (não colocar aqui, mesmo que pareça conveniente):
- **Categoria**: `conteudos.category_id` aponta para `categories`; `aplicativos.category_id` aponta para `aplicativo_categories` — são **duas árvores de categoria diferentes** no legado, não uma só. Cada app tem seu próprio Snippet de categoria.
- **Licença**: só `conteudos` tem `license_id`. `aplicativos` não tem licença no legado — não force esse campo em `AplicativoPage`.
- **Tags**: só `conteudos` usa `tags` (M2M) no legado.
- **Fluxo de aprovação** (`is_approved`, `is_featured`, `approving_user_id`): só existe em `conteudos` no legado. `aplicativos` não tem esses campos — não assumir que aplicativo passa por aprovação editorial do mesmo jeito.

Se `AplicativoPage` não usa `RecursoBasePage` (por ter pouquíssimo em comum — só canal e autor), fica a critério de quem implementar julgar se vale herança ou só repetir dois campos. Não é decisão fechada; se for repetir os dois campos, documentar aqui o porquê.

### Taxonomias compartilhadas (Snippets)
Confirmar antes de criar: um Snippet só entra em `core` se for usado por mais de um app. Candidatos identificados no schema legado que **são exclusivos de `conteudos`** (não devem morar em `core`): `Tipo` (com `options.formatos`, validação de extensão por tipo), `Licenca` (árvore), `NivelEnsino`, `CurricularComponent`. Esses ficam no app `conteudos` ou `curriculo`, não em `core`.

## O que NÃO fazer neste app
- Não crie um model "genérico" de categoria/taxonomia pensando em reuso futuro hipotético. O legado já mostrou que categoria de conteúdo e categoria de aplicativo são coisas diferentes — replicar essa separação é fidelidade ao sistema real, não falta de abstração.
- Não adicione lógica de aprovação/moderação aqui — isso é regra de `conteudos`, não de `core`.
- Pausar e perguntar antes de decidir se um campo novo é "compartilhado o suficiente" pra entrar em `core`. Regra prática: só entra se **dois ou mais apps já implementados** precisam dele, não por antecipação.
