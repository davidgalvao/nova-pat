# aplicativos/ — CLAUDE.md

## Papel deste app
`aplicativos` modela ferramentas/softwares educacionais externos — um link de saída, não um arquivo de mídia com player. É semanticamente diferente de `conteudos` (ver `core/CLAUDE.md`) mesmo compartilhando algumas coisas.

**Nomenclatura do model: `AplicativoEducacionalPage`, não `AplicativoPage`.** Decisão deliberada: "app"/"aplicativo" já é termo sobrecarregado no ecossistema Django (`INSTALLED_APPS`, cada pasta do projeto já é chamada de "app"). Nomear a entidade de negócio de forma mais específica evita ambiguidade em conversa e em código entre "o Django app `aplicativos`" e "a entidade `Aplicativo`". A pasta do app Django continua `aplicativos/` (nome curto, contexto já dado pela estrutura de pastas) — só a classe do model é mais explícita.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`, `core/CLAUDE.md` (para o que é/não é compartilhado com `conteudos`).

## Fase atual: transposição

## Model `AplicativoEducacionalPage(RecursoBasePage ou BasePage direto)`
Ver `core/CLAUDE.md` para a decisão em aberto de herdar `RecursoBasePage` ou repetir campo — pouco em comum de fato (canal, autor).

Campos confirmados no legado:
- `name`, `description` (mínimo 140 caracteres — regra de validação real, `AplicativoRequest::rules()`)
- `url` — obrigatória, e o legado valida com a regra `active_url` do Laravel (checagem de DNS/resolução real da URL, não só formato). Replicar validação equivalente (checar se a URL resolve) antes de aceitar.
- `category` — FK para `AplicativoCategory` (árvore **própria**, diferente de `categories` de `conteudos` — ver `core/CLAUDE.md`).
- `tags` — M2M com `Tag`, **mesma tabela/taxonomia usada por `conteudos`** (pivot diferente no legado, `aplicativo_tag`, mas é o mesmo conceito de tag). Regra de validação do legado: mínimo 3, máximo 15 tags (note que é diferente do limite de `conteudos`, que é mínimo 3, máximo 50 — não usar o mesmo número por engano).
- `image`/ícone — upload de imagem, formatos aceitos `jpeg`, `png`, `jpg`, `svg`, até 1MB (1024kb) no legado.
- `is_featured` — no legado vive dentro de `options` (jsonb), não como coluna própria. Avaliar estruturar como campo booleano de verdade na NOVA PAT (mais simples de consultar/filtrar do que jsonb).
- `qt_access` — também dentro de `options` no legado (`options.qt_access`, inicializado em `0` na criação, via constante `Aplicativo::QT_ACCESS_INIT`). Mesmo comentário: campo de verdade é preferível a jsonb aqui.

### Canal — fixo, não é escolha do usuário
**Achado importante**: diferente de `conteudos`, onde o canal é escolha real do autor, em `aplicativos` o legado **fixa o canal por constante no código**:
```php
public const CANAL_ID = 9;
```
Todo aplicativo criado recebe esse `canal_id` fixo, independente do que o formulário mandar — não é campo editável na prática. `id=9` é muito provavelmente o canal "Aplicativos Educacionais" (um dos 12 canais confirmados em produção, ver `canais/CLAUDE.md`), mas isso não foi confirmado com certeza absoluta (não temos acesso direto ao banco de produção) — **confirmar no admin antes de fechar**. Ao implementar `AplicativoEducacionalPage`, não expor campo de canal editável no formulário de criação — fixar automaticamente, replicando o comportamento real.

### Sem license, sem workflow de aprovação
Confirmado: `aplicativos` não tem `license_id` nem fluxo de `is_approved`/`approving_user_id` no legado. Isso é coerente com a regra de autorização abaixo — só quem já é privilegiado pode criar aplicativo, então não existe "pendente de aprovação" como em conteúdo comum.

## Regras de autorização (diferentes de `conteudos` — não copiar RN-L1 direto)
Confirmado em `AplicativoPolicy.php`:
- **Criar**: só `super-admin`, `admin` ou `coordenador`. **Mesma restrição de `conteudos`** (RN-L1 em `conteudos/CLAUDE.md`, corrigido de uma suposição anterior errada) — nenhum papel abaixo de `coordenador` cria conteúdo nem aplicativo no comportamento real do legado. Não é uma diferença entre os dois domínios, é a mesma regra.
- **Editar/deletar**: papel privilegiado, ou o próprio autor (`aplicativo.user_id == user.id`) — mas como só papel privilegiado cria, essa cláusula de "próprio autor" na prática só se aplica a coordenador editando o que ele mesmo criou.
- **Restaurar**: `super-admin`/`admin`.
- **Apagar permanentemente**: só `super-admin`.

## O que NÃO fazer neste app
- Não copiar a regra de aprovação de `conteudos` (RN-L1) pra cá — não existe workflow de aprovação em `aplicativos`, a restrição acontece na permissão de criação, não depois.
- Não deixar usuário comum criar aplicativo — só papel privilegiado, sem exceção.
- Não expor campo de canal editável no formulário — é fixo por regra de negócio (constante no legado).
- Não usar o mesmo limite de tags de `conteudos` (3–50) — aqui é 3–15.
- Não usar a mesma árvore de categoria de `conteudos` — `AplicativoCategory` é separada.
- Não adicionar `license` a este model — não existe no domínio de aplicativo.
- Não aceitar `url` sem validar que ela resolve de fato (equivalente ao `active_url` do Laravel).