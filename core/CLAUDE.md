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
Base para as duas entidades de recurso educacional que compartilham campos reais: `ConteudoPage` (app `conteudos`) e `AplicativoEducacionalPage` (app `aplicativos`).

**Confirmado no schema legado** — o que é de fato compartilhado entre `conteudos` e `aplicativos`:
- `canal` (FK para `CanalPage`, app `canais`) — os dois têm, **mas com comportamento diferente**: em `conteudos`, o canal é escolha real do autor/curador. Em `aplicativos`, o legado **fixa o canal por constante no código** (`Aplicativo::CANAL_ID = 9`, sempre o mesmo canal — provavelmente "Aplicativos Educacionais" na lista de 12 canais, ver `canais/CLAUDE.md`) — não é campo livre no formulário. Replicar essa fidelidade: `AplicativoEducacionalPage` não deveria oferecer campo de canal editável, deve fixar automaticamente na criação.
- `autor` (FK para usuário publicador, `user_id` no legado) — os dois têm.
- **Tags** — **correção de suposição anterior**: tags **são** compartilhadas de fato. `Aplicativo.php` tem `belongsToMany(Tag::class, 'aplicativo_tag', ...)` — é a mesma classe `Tag`, só pivot diferente (`aplicativo_tag` vs `conteudo_tag`). Isso é trivial no Django com `django-taggit` (o model de tag já é global por natureza), mas vale registrar que a intenção do legado é reuso real da mesma taxonomia de tag entre os dois domínios.

**O que continua NÃO sendo compartilhado** (não colocar aqui, mesmo que pareça conveniente):
- **Categoria**: `conteudos.category_id` aponta para `categories`; `aplicativos.category_id` aponta para `aplicativo_categories` — são **duas árvores de categoria diferentes** no legado, não uma só. Cada app tem seu próprio Snippet de categoria.
- **Licença**: só `conteudos` tem `license_id`. `aplicativos` não tem licença no legado — não force esse campo em `AplicativoEducacionalPage`.
- **Fluxo de aprovação** (`is_approved`, `is_featured` como campo top-level, `approving_user_id`): confirmado que `aplicativos` **não tem workflow de aprovação** no legado — a policy de criação já restringe quem pode criar (só `super-admin`/`admin`/`coordenador`), então não existe o conceito de "pendente de aprovação" como em conteúdo. `is_featured` existe em `aplicativos`, mas dentro de `options` (jsonb), não como coluna própria — avaliar se estrutura como campo de verdade na NOVA PAT.

Se `AplicativoEducacionalPage` não usa `RecursoBasePage` (por ter pouquíssimo em comum — só canal e autor), fica a critério de quem implementar julgar se vale herança ou só repetir dois campos. Não é decisão fechada; se for repetir os dois campos, documentar aqui o porquê.

### Taxonomias compartilhadas (Snippets)
Confirmar antes de criar: um Snippet só entra em `core` se for usado por mais de um app. Candidatos identificados no schema legado que **são exclusivos de `conteudos`** (não devem morar em `core`): `Tipo` (com `options.formatos`, validação de extensão por tipo), `Licenca` (árvore), `NivelEnsino`, `CurricularComponent`. Esses ficam no app `conteudos` ou `curriculo`, não em `core`.

## O que NÃO fazer neste app
- Não crie um model "genérico" de categoria/taxonomia pensando em reuso futuro hipotético. O legado já mostrou que categoria de conteúdo e categoria de aplicativo são coisas diferentes — replicar essa separação é fidelidade ao sistema real, não falta de abstração.
- Não adicione lógica de aprovação/moderação aqui — isso é regra de `conteudos`, não de `core`.
- Pausar e perguntar antes de decidir se um campo novo é "compartilhado o suficiente" pra entrar em `core`. Regra prática: só entra se **dois ou mais apps já implementados** precisam dele, não por antecipação.