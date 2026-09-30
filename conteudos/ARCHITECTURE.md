# conteudos/ — ARCHITECTURE.md

## Papel deste app
`conteudos` é a entidade central do sistema — o recurso educacional em si (vídeo, documento, áudio, apresentação, etc.). Contém `ConteudoPage` e as taxonomias que são **exclusivas** desse domínio (não compartilhadas com `aplicativos` — ver `core/ARCHITECTURE.md` para a lista do que não é compartilhado e por quê).

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`. Este app tem o maior volume de regra de negócio herdada do legado — ler os dois documentos inteiros antes de alterar qualquer coisa aqui, não só a seção de conteúdo.

## Fase atual: transposição, com uma peça nova (RF008/Serie)
A maior parte deste app é replicar o legado fielmente. A exceção é o suporte a episódio de série (`numero_episodio`, `parent_page_types` incluindo `Temporada`), que é RF008, uma peça nova — ver `docs/requisitos-vs-legado.md`.

## Model `ConteudoPage(RecursoBasePage)`

Campos próprios (além de `canal`, `autor` e `tags`, herdados de `RecursoBasePage`):
- `tipo` — FK para `Tipo` (snippet deste app, não do `core` — ver abaixo). É a **taxonomia pedagógica** (categoria usada em filtros de busca e currículo).
- `mecanismo_exibicao` — `CharField` com choices (7 mecanismos: `video`, `audio`, `documento_pdf`, `apresentacao`, `download_binario`, `link_externo`, `animacao_externa`). É o **formato técnico** que determina a view de renderização (player, visualizador, download, link externo). **Distinto de `tipo`** — decisão fechada em `CONTEXT.MD` seção 3 (ver seção "Player por mecanismo de exibição" abaixo).
- `category` — FK para `CategoriaConteudo` (snippet deste app, árvore própria escopada por canal; **não é a mesma árvore** de `AplicativoCategory` no app `aplicativos` — confirmado no schema legado, ver `core/ARCHITECTURE.md`).
- `license` — FK para `Licenca` (snippet deste app, estrutura em árvore tipo Creative Commons). Licença é exclusiva de conteúdo — `aplicativos` não tem licença no legado, não adicionar lá.
- `componentes_curriculares` — `ParentalManyToManyField` para `CurricularComponent` (app `curriculo`, cross-app).
- `arquivo`/upload — documento/mídia associado, validado por extensão conforme `tipo` (ver RN-L3 abaixo).
- `authors`, `source`, `options` — `authors`: autores do conteúdo; `source`: **URL de mídia
  externa** (MODO B — usada por `link_externo` e `animacao_externa`; ver "Resolução de embed"
  abaixo); `options`: JSON flexível.
- `is_approved`, `is_featured`, `is_site` (booleans).
- `qt_downloads`, `qt_access` (contadores).
- `numero_episodio` (nullable) — só preenchido quando o conteúdo é filho de uma `Temporada` (app `series`, RF008). Vídeo avulso mantém `null`.
- `media_avaliacao`, `total_avaliacoes` — desnormalizados, **somente para exibição** na busca (não usar em filtro/ordenação — decisão fechada em `docs/requisitos-vs-legado.md`, RF011). Atualizados via signal disparado pelo app `interacoes` (ver seção de dependências abaixo).

### `parent_page_types`
```python
parent_page_types = ['canais.CanalPage', 'series.Temporada']
subpage_types = []  # Conteúdo não tem filhos
```

## Taxonomias deste app (Snippets)

### `Tipo`
Tipo de mídia (vídeo, documento, podcast, etc.). Campo `options` (jsonb no legado — avaliar se justifica manter jsonb ou estruturar como campo próprio) carrega `formatos`: lista de extensões de arquivo aceitas para aquele tipo. **É configuração ativa de validação de upload, não etiqueta de exibição** — replicar a validação de extensão real, não só o rótulo.

### `Licenca`
Árvore (licença pode ter sublicenças, tipo Creative Commons).

### `CategoriaConteudo`
Árvore (`parent`), escopada por `canal` (constraint `unique_categoriaconteudo_slug_per_canal`). Distinta da categoria de aplicativo (`AplicativoCategory`) — não fundir. **Nota**: o model foi renomeado de `Categoria` para `CategoriaConteudo` (migration 0002).

## Regras de negócio a preservar (extraídas do legado, não óbvias no schema)

### RN-L1 — Criação de conteúdo é restrita a papel privilegiado, não aberta a todo usuário
**Correção de suposição anterior** (achado confirmado ao ler `ConteudoController.php` + `ConteudoPolicy.php`): eu tinha documentado que qualquer usuário autenticado podia criar conteúdo, ficando pendente de aprovação (`is_approved=False`). Isso está **errado**. O controller chama `$this->authorize('create', $conteudo)` antes de aceitar a criação, e `ConteudoPolicy::create()` só libera `super-admin`, `admin` ou `coordenador` — os papéis `editor` e `convidado` (ver RN-L4) **não conseguem criar conteúdo, são barrados antes** de qualquer lógica de aprovação.

Existe um trecho no `ConteudoFormRequest` que força `is_approved=False`/`approving_user_id=null` para "qualquer outro usuário" — isso é muito provavelmente **código defensivo que nunca executa na prática** (já que a Policy bloqueia antes), não uma segunda camada de regra ativa. Não replicar a ideia de "usuário comum cria mas fica pendente" — replicar o que de fato acontece: só `coordenador` pra cima cria conteúdo. Se a intenção de produto para a NOVA PAT for diferente (abrir criação pra `editor` com aprovação pendente, por exemplo), isso é uma **mudança de regra de negócio deliberada**, não transposição — precisa ser decisão explícita, não suposição.

### RN-L2 — Título não pode duplicar, mas só na criação
Checagem `ILIKE` (case-insensitive, substring) contra títulos existentes. **Só no create.** Na edição, a regra não se aplica — senão seria impossível salvar um conteúdo existente sem mudar o título.

### RN-L3 — Extensão de upload validada dinamicamente por tipo
Antes de aceitar o upload, validar a extensão do arquivo contra `tipo.options.formatos` (ou o campo estruturado equivalente). Sem tipo válido ou extensão fora da lista, upload é rejeitado.

### RN-L4 — Papéis reais (5, não 4 — correção de suposição anterior)
Confirmado em `roles` (migration + `Users/*.php`, cada subtipo com `role_id` fixo via global scope): `super-admin` (id 1), `admin` (id 2), `coordenador` (id 3), `editor` (id 4), `convidado` (id 5). **Não existe "professor"** como nome de papel — isso foi terminologia errada usada em versão anterior deste documento. `convidado` é o papel padrão de novo cadastro (`User::USER_DEFAULT_ROLE = 5`).

- `super-admin` — irrestrito.
- `admin` — quase irrestrito, abaixo de super-admin em ações destrutivas.
- `coordenador` — cria/edita/aprova conteúdo, gerencia tags. Não mexe em `Licenca`, `Categoria`, `Tipo` (essas são só `super-admin`/`admin`).
- `editor` — **capacidade em relação a `conteudos` não confirmada.** Não aparece na lista de papéis liberados para criar conteúdo (`ConteudoPolicy::create()`). Seu escopo real de permissão (talvez ligado a gestão de usuário, ou a outro domínio como `Contato`/`Playlist`) não foi levantado ainda — não presumir que "editor" edita conteúdo só porque o nome sugere isso. Confirmar antes de implementar qualquer permissão pra esse papel.
- `convidado` — papel padrão de cadastro. Sem evidência de permissão de criação em `conteudos` nas policies revisadas até agora.

**Nenhum papel abaixo de `coordenador` cria conteúdo** no comportamento real do legado (ver RN-L1). Se a NOVA PAT decidir abrir criação para `editor`, é mudança de regra deliberada — documentar aqui quando (e se) for decidida.

### RN-L5 — Campos obrigatórios com regra pedagógica
`componentes_curriculares`: mínimo 1. `tags`: mínimo 3, máximo 50. `description`: mínimo 100, máximo 5012 caracteres. Esses limites vieram de curadoria pedagógica real, não são arbitrários — não afrouxar sem confirmar com quem decide o conteúdo pedagógico.

### RN-L6 — Contadores sempre iniciam em zero
`qt_downloads`/`qt_access` sempre `0` na criação, independente do que vier no request.

## Player por mecanismo de exibição — decisão fechada
**Correção importante**: o player **não** é escolhido pelo slug do `tipo` (taxonomia pedagógica). A arquitetura distingue rigidamente (decisão em `CONTEXT.MD` seção 3):
- **Taxonomia pedagógica (`tipo`)** — categoria usada em filtros de busca e currículo (ex: Animação, Apresentação, Sequência Didática, Vídeo, Jogo).
- **Formato técnico (`mecanismo_exibicao`)** — atributo em `ConteudoPage` que determina a view de renderização.

`ConteudoPage.get_template()` escolhe o template pelo `mecanismo_exibicao`:
```python
def get_template(self, request, *args, **kwargs):
    fallback = "conteudos/conteudo_page.html"
    if self.mecanismo_exibicao:
        especifico = f"conteudos/conteudo_page_{self.mecanismo_exibicao}.html"
        return select_template([especifico, fallback]).template.name
    return fallback
```

Os 7 mecanismos e seus templates:
- `video` → `conteudo_page_video.html` (player responsivo 16:9).
- `audio` → `conteudo_page_audio.html` (player de áudio nativo estilizado).
- `documento_pdf` → `conteudo_page_documento_pdf.html` (visualizador embutido ou download seguro de PDF).
- `apresentacao` → `conteudo_page_apresentacao.html` (visualizador/download de apresentação).
- `download_binario` → `conteudo_page_download_binario.html` (download seguro de pacotes/executáveis .zip/.rar/.exe).
- `link_externo` → `conteudo_page_link_externo.html` (link externo seguro, `noopener noreferrer`).
- `animacao_externa` → `conteudo_page_animacao_externa.html` (iframe protegido para animações/sites externos).

### Resolução de embed (URL colada pelo gestor)
O gestor cola a URL do **navegador**, não a de embed: `youtube.com/watch?v=ID`, `youtu.be/ID`,
`youtube.com/shorts/ID`, `vimeo.com/ID`, `open.spotify.com/...`. Essas URLs **não** funcionam em
`<iframe src>` (X-Frame-Options bloqueia `/watch`, `/shorts` etc.), então a URL colada **nunca**
deve ir direto para o `src` de um iframe. Usar `{% embed url %}` ou `get_embed(url)` de
`wagtail.embeds`, que resolve a URL via oEmbed e devolve o HTML de incorporação correto.

Providers cobertos **nativamente** (verificados com URLs reais no Wagtail 8 deste projeto):
**YouTube** (`/watch`, `youtu.be`, `/shorts`), **Vimeo**, **Spotify**, **SoundCloud**
(80 providers oEmbed nativos no total).
**Não coberto:** Google Slides (`docs.google.com/presentation/...`) — requer provider custom em
`WAGTAILEMBEDS_FINDERS`; até lá, cai no fallback de link seguro (ver "Dívida técnica" ao fim
deste documento).

Comportamento verificado da tag: `{% embed url max_width=N %}` aceita **somente** `max_width`;
se a URL não for embeddável, captura `EmbedException` e devolve string vazia, sem quebrar a
página. Por isso o template usa `{% embed url as embed_html %}` + `{% if embed_html %}`, caindo
em link externo seguro (`target="_blank"` + `rel="noopener noreferrer"`) quando vazio.

Todos herdam de `conteudo_page_base.html`. O fallback `conteudo_page.html` garante que um mecanismo sem template dedicado ainda renderize (nunca dispara `TemplateDoesNotExist`).

Um conteúdo tem **um tipo só** e **um mecanismo de exibição só** (fiel ao legado). StreamField foi descartado para este caso — não reabrir essa discussão sem motivo novo real (ver `docs/requisitos-vs-legado.md` para o raciocínio completo).

## Episódio de série (RF008) — o que muda aqui
Quando `ConteudoPage.get_parent()` é uma `Temporada` (app `series`), o template deve exibir indicador de série (breadcrumb Serie › Temporada › Episódio, navegação para outros episódios via `get_siblings()`). Isso é resolvido no template a partir da posição na árvore — **não** criar campo extra tipo `is_episodio`, é derivável.

## Busca — lacuna confirmada em produção, corrigir na transposição
A busca em produção hoje só retorna resultado dentro do canal "Recursos Educacionais" e não tem filtro por canal na busca avançada (achado registrado em `docs/requisitos-vs-legado.md`, RF001). Ao implementar a busca deste app: incluir `canal` como critério de filtro explícito, junto com `tipo`, `category`, `license`, `componentes_curriculares` e `mecanismo_exibicao` (todos como `FilterField` no `search_fields`). Não usar `media_avaliacao`/`total_avaliacoes` como filtro nem ordenação (decisão fechada, RF011).

## Dependências entre apps — cuidado com direção
- `Favorito`, `Like`, `Avaliacao` **não moram neste app** — vivem em `interacoes/`, cada um com FK para `ConteudoPage`. `interacoes` depende de `conteudos`, não o contrário. A atualização de `media_avaliacao`/`total_avaliacoes` acontece via signal **definido em `interacoes`**, escutando `Avaliacao.post_save`/`post_delete` — `conteudos` não deve importar nada de `interacoes`.
- `componentes_curriculares` depende do app `curriculo` (M2M cross-app).
- `parent_page_types` depende do app `series` (RF008).

## O que NÃO fazer neste app
- Não confiar em valor de `is_approved`/`is_featured` vindo do request sem checar a role no servidor (RN-L1).
- Não aplicar a checagem de título duplicado na edição (RN-L2 é só create).
- Não deixar upload passar sem validar extensão contra o `tipo` (RN-L3).
- Não afrouxar os mínimos de `tags`/`componentes_curriculares`/`description` sem confirmar que é decisão de negócio, não conveniência técnica (RN-L5).
- Não usar `media_avaliacao` em filtro ou ordenação de busca — só exibição (decisão fechada).
- Não colocar `Favorito`/`Like`/`Avaliacao` neste app — pertencem a `interacoes`.
- Não reabrir a discussão de StreamField para o player sem um motivo de produto novo e real.
- **Não escolher o template pelo slug do `tipo`** — o player é determinado pelo `mecanismo_exibicao` (formato técnico), não pela taxonomia pedagógica (`tipo`). Confundir os dois é o erro que a decisão de `CONTEXT.MD` seção 3 corrige.
- Não usar `Categoria` como nome de model — foi renomeado para `CategoriaConteudo` (migration 0002).
- Não passar URL colada pelo gestor direto em `<iframe src>` — resolver com `{% embed %}` /
  `get_embed()` de `wagtail.embeds` (ver "Resolução de embed" na seção "Player por mecanismo de exibição").

## Dívida técnica

### Embed de Google Slides não suportado nativamente
- **Situação:** `docs.google.com/presentation/...` **não** está entre os 80 providers oEmbed nativos do Wagtail 8 deste projeto. Verificado com URL real: `get_embed()` levanta `EmbedUnsupportedProviderException` e `{% embed %}` devolve string vazia.
- **Comportamento atual (fallback):** cai no link externo seguro (`target="_blank"` + `rel="noopener noreferrer"`) — a página não quebra, mas a apresentação não é incorporada.
- **Para implementar:** registrar um provider custom em `WAGTAILEMBEDS_FINDERS`, mapeando `docs.google.com/presentation/d/<id>` para `https://docs.google.com/presentation/d/<id>/embed`.
- **Escopo:** **fora do escopo atual**. Só implementar com um caso de uso real e uma URL pública de apresentação para testar (o `AGENTS.md` exige testar 2–3 casos reais antes de propor código).
