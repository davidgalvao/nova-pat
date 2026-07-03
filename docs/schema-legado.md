# Schema e Regras de Negócio — PAT Legado (Laravel)

> Referência extraída do repositório legado (`nikoz84/plataforma-anisio-teixeira`, Laravel 9 + Postgres, GPL-3.0). Serve como fonte da verdade sobre o que o sistema atual realmente faz — não confundir com o `Levantamento de Requisitos NOVA PAT V1.0`, que descreve o que o sistema **deveria vir a fazer**. Ver `docs/requisitos-vs-legado.md` para o cruzamento entre os dois.

## Entidades principais

### `canais`
Agrupador de topo (TV Anísio Teixeira, Rádio Anísio Teixeira, EMITEC, etc.). Campos: `name`, `description`, `slug`, `active`, `options` (jsonb, inclui cor). Sem hierarquia própria — é um nível único acima de conteúdo/categoria.

### `conteudos`
Entidade central do sistema.

- Relaciona com: `tipo`, `canal`, `usuário autor` (`user_id`), `usuário aprovador` (`approving_user_id`), `license`, `category`.
- Campos próprios: `title`, `description`, `authors`, `source`, `options` (jsonb — acessibilidade, site associado, etc.), `is_approved`, `is_featured`, `is_site`, `qt_downloads`, `qt_access`.
- Busca full-text via tsvector (`ts_documento`, campo oculto no output da API).
- Soft delete habilitado.
- M2M com `curricular_components` (componente curricular/disciplina) e `tags`.

### `tipos`
Tipo de mídia do conteúdo (vídeo, documento, podcast, etc.). Cada tipo carrega em `options.formatos` (jsonb) a lista de extensões de arquivo permitidas para aquele tipo — **é configuração ativa de validação de upload, não só uma etiqueta de exibição**.

### `categories`
Árvore (`parent_id`), escopada por `canal`.

### `licenses`
Árvore de licenças (modelo tipo Creative Commons — licença pode ter sublicenças).

### `niveis_ensino` + `curricular_components_categories` + `curricular_components`
Estrutura curricular: nível de ensino (1º ao 3º ano do EM) → categoria de componente → componente curricular (disciplina). M2M com `conteudos`.

### `tags`
M2M com conteúdo, com contador de uso em busca.

### `aplicativos`
Entidade irmã de `conteudos` — mesma lógica (canal/categoria/usuário/URL), mas para aplicativos educacionais em vez de mídia.

### `comentarios`, `conteudos_likes`
Interação simples. **Não existe** avaliação por estrelas nem "favoritos" separado de "like" no legado — ver `docs/requisitos-vs-legado.md`, RF010/RF011.

### `user_canal`
Vínculo de usuários editores a canais específicos.

---

## Regras de negócio (não visíveis nas migrations, extraídas de Requests/Rules/Policies)

### RN-L1 — Aprovação editorial é decidida no servidor, nunca confiada ao front
Em `ConteudoFormRequest::whenCreate()`: se o usuário autenticado tem role `super-admin`, `admin` ou `coordenador`, o valor de `is_approved`/`is_featured` enviado pelo formulário é respeitado. Para qualquer outro usuário (ex: professor comum), o backend **força** `is_approved = false` e `approving_user_id = null`, independente do que o formulário mandou.

> Implicação pro Wagtail: isso é o equivalente ao fluxo de moderação nativo do Wagtail (`Page.live` / workflow de aprovação), mas com a regra de "quem pode publicar direto" amarrada a role, não a permissão de página. Vale decidir se usamos o workflow builtin do Wagtail ou replicamos a lógica de role explícita.

### RN-L2 — Título de conteúdo não pode duplicar (só na criação)
`ConteudoTitleExist` faz busca `ILIKE %valor%` (case-insensitive, substring, não exato) contra todos os títulos existentes. Vale **apenas no método POST** — na edição (PUT) a regra é ignorada, senão seria impossível salvar um conteúdo existente sem mudar o título.

### RN-L3 — Extensão de upload validada dinamicamente por tipo
`ValidExtensions` busca o `Tipo` pelo `tipo_id` enviado e checa a extensão do arquivo contra `tipo.options.formatos`. Sem tipo válido, upload é rejeitado.

### RN-L4 — Papéis (roles) confirmados
- `super-admin` — acesso irrestrito.
- `admin` — quase irrestrito, mas abaixo de super-admin em ações destrutivas (`forceDelete`, restaurar).
- `coordenador` — pode criar/editar conteúdo, aprovar, gerenciar tags/playlists/contato. Não mexe em `licenses`, `categories`, `tipos`, `niveis_ensino` (essas são só `super-admin`/`admin`).
- Role implícito (professor/usuário comum) — pode criar conteúdo, mas sempre entra como pendente de aprovação; pode editar/deletar apenas o próprio conteúdo.

### RN-L5 — Campos obrigatórios com regra pedagógica, não técnica
No `ConteudoFormRequest::rules()`: `componentes` (componente curricular) exige mínimo 1; `tags` exige mínimo 3, máximo 50; `description` exige mínimo 100 caracteres, máximo 5012.

### RN-L6 — `qt_downloads`/`qt_access` sempre iniciam em zero
Constante `Conteudo::INIT_COUNT = 0`, forçada na criação independente do que vier no request.

---

## Notas de mapeamento para Wagtail (decisões já discutidas)

- `canais` → `Page` (`CanalPage`), hierárquico.
- `conteudos` → `Page` filha do canal (`ConteudoPage`), com `StreamField` para blocos de mídia mapeando `tipos`.
- `categories`, `tipos`, `licenses`, `niveis_ensino`, `curricular_components` → Snippets.
- `tags` → `django-taggit`.
- `aplicativos` → `Page` própria (`AplicativoPage`), espelhando `ConteudoPage`.
- `comentarios`/`likes` → models Django puros, fora da árvore de páginas.
- Apps novos ficam soltos na raiz do projeto (convenção já estabelecida pelo scaffold `wagtail start`: `home/`, `search/`, `core/`), não aninhados em `apps/`.
