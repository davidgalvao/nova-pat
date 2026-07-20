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
Estrutura curricular: nível de ensino → categoria de componente → componente curricular (disciplina). M2M com `conteudos`. **Correção**: a suposição anterior de que a plataforma cobre só "1º ao 3º ano do Ensino Médio" está errada — confirmado em produção que também há conteúdo de Ensino Fundamental (URLs `rotinas-de-estudo/ensino-fundamental-1` e `rotinas-de-estudo/ensino-medio`). Ver `curriculo/CLAUDE.md` para a nota completa; valores exatos de `niveis_ensino` precisam ser confirmados no admin de produção.

### `tags`
M2M com conteúdo, com contador de uso em busca.

### `aplicativos`
Entidade irmã de `conteudos` — mesma lógica (canal/categoria/usuário/URL), mas para aplicativos educacionais em vez de mídia.

### `comentarios`, `conteudos_likes`
**Correção de suposição anterior**: achei antes que essas duas tabelas eram exclusivas de `conteudos`. Errado — confirmado no model (`Comentario.php`, campo `tipo` com valores literais `'conteudo'`/`'aplicativo'`, mais `conteudo_id` e `aplicativo_id` ambos nullable): **comentário e like já são polimórficos no legado**, valem tanto pra `conteudos` quanto pra `aplicativos`. `conteudos_likes` tem um campo `like` (`boolean`, nullable) cujo significado exato (like simples vs. like/dislike vs. toggle removível) não está claro só pelo schema — confirmar com uso real antes de replicar. Não existe avaliação por estrelas nem "favoritos" separado de "like" no legado — ver `docs/requisitos-vs-legado.md`, RF010/RF011.

### `user_canal`
Vínculo de usuários editores a canais específicos.

---

## Regras de negócio (não visíveis nas migrations, extraídas de Requests/Rules/Policies)

### RN-L1 — Aprovação editorial é decidida no servidor, nunca confiada ao front
### RN-L1 — Criação de conteúdo é restrita a papel privilegiado (correção de suposição anterior)
**Corrigido**: versão anterior deste documento dizia que qualquer usuário podia criar conteúdo, ficando pendente de aprovação. Errado — `ConteudoController` chama `$this->authorize('create', $conteudo)`, e `ConteudoPolicy::create()` só libera `super-admin`, `admin` ou `coordenador`. O trecho do `ConteudoFormRequest::whenCreate()` que força `is_approved=false`/`approving_user_id=null` para "qualquer outro usuário" é muito provavelmente código defensivo que nunca executa na prática, já que a Policy bloqueia antes.

> Implicação pro Wagtail: isso é o equivalente ao fluxo de moderação nativo do Wagtail (`Page.live` / workflow de aprovação), mas com a regra de "quem pode publicar direto" amarrada a role, não a permissão de página. Vale decidir se usamos o workflow builtin do Wagtail ou replicamos a lógica de role explícita.

### RN-L2 — Título de conteúdo não pode duplicar (só na criação)
`ConteudoTitleExist` faz busca `ILIKE %valor%` (case-insensitive, substring, não exato) contra todos os títulos existentes. Vale **apenas no método POST** — na edição (PUT) a regra é ignorada, senão seria impossível salvar um conteúdo existente sem mudar o título.

### RN-L3 — Extensão de upload validada dinamicamente por tipo
`ValidExtensions` busca o `Tipo` pelo `tipo_id` enviado e checa a extensão do arquivo contra `tipo.options.formatos`. Sem tipo válido, upload é rejeitado.

### RN-L4 — Papéis (roles) confirmados
- `super-admin` — acesso irrestrito.
- `admin` — quase irrestrito, mas abaixo de super-admin em ações destrutivas (`forceDelete`, restaurar).
- `coordenador` — pode criar/editar conteúdo, aprovar, gerenciar tags/playlists/contato. Não mexe em `licenses`, `categories`, `tipos`, `niveis_ensino` (essas são só `super-admin`/`admin`).
- Papéis reais (5, confirmado em `roles` + `Users/*.php`): `super-admin` (1), `admin` (2), `coordenador` (3), `editor` (4), `convidado` (5, papel padrão de cadastro). Não existe papel chamado "professor". Nenhum papel abaixo de `coordenador` cria conteúdo no comportamento real (ver correção de RN-L1 acima). Escopo exato de `editor` não levantado ainda.

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
- `aplicativos` → `Page` própria (`AplicativoEducacionalPage`), espelhando `ConteudoPage`.
- `comentarios`/`likes` → models Django puros, fora da árvore de páginas.
- Apps novos ficam soltos na raiz do projeto (convenção já estabelecida pelo scaffold `wagtail start`: `home/`, `search/`, `core/`), não aninhados em `apps/`.