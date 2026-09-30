# Plano: Blocos de fallback para CanalPage (composição padrão)

## Contexto

D1 fechou: `CanalPage.body` é StreamField reutilizando `HomeStreamBlock`.
Mas template atual tem hardcode de "Conteúdos" e "Aplicativos" que:
- Ignora o body quando ele tem conteúdo (duas listagens duplicadas)
- Não tem identidade visual dos outros blocos

Solução aprovada: **zero hardcode no template**. Fallback vira composição
usando blocos da mesma coletânea.

## Regras de execução

R1. ANTES de escrever qualquer código, LER:
    - `core/blocks.py` (blocos existentes — entender padrão)
    - `core/templates/core/blocks/*.html` (templates existentes — copiar estilo)
    - CSS onde os blocos são estilizados (achar via grep por uma classe de bloco)
    - `home/templates/home/home_page.html` (como os blocos são renderizados lá)
    
    Se algum desses não existir, PARAR e perguntar.

R2. NÃO inventar classes CSS. Reaproveitar padrão dos blocos existentes.

R3. NÃO inventar JS. Se o carrossel precisa, procurar se há JS de carrossel
    já usado no projeto. Se não houver, usar CSS scroll-snap puro.

R4. ANTES de alterar cada arquivo, mostrar o diff proposto.

R5. Ao terminar, TESTAR de verdade (Playwright MCP):
    - Abrir um canal sem `body` → deve mostrar hero + carrossel (fallback)
    - Abrir um canal com `body` → deve mostrar apenas os blocos do gestor
    - Nenhum canal deve mostrar listagens duplicadas

## Arquivos a criar/alterar

### 1. `core/blocks.py` — adicionar 2 blocos
- `UltimoConteudoPlayerBlock` — hero com último conteúdo do canal em player
- `UltimosConteudosCarrosselBlock` — carrossel 9 itens (3 por página, passadores)

Ambos adicionados ao `HomeStreamBlock` existente.

### 2. `core/templates/core/blocks/ultimo_conteudo_player.html` (novo)
Hero com `<video>` ou `<audio>` (depende do `mecanismo_exibicao` do conteúdo)
ou capa com link. Reaproveitar classes CSS dos blocos existentes.

### 3. `core/templates/core/blocks/ultimos_conteudos_carrossel.html` (novo)
Grade de 3 colunas, paginação com passadores (prev/next).
Reaproveitar classes CSS.

### 4. CSS/JS (se necessário)
Procurar onde os blocos existentes são estilizados. Se o carrossel precisar
de interatividade, preferir CSS scroll-snap. Só JS se indispensável.

### 5. `canais/models.py` — método novo
`get_effective_body()`:
- Retorna `self.body` se preenchido
- Senão, retorna `StreamValue` sintético com 2 blocos default
- Usar `is_lazy=True` (obrigatório)

### 6. `canais/templates/canais/canal_page.html` — reescrever
Estrutura final:
<h1>{{ page.title }}</h1> {% if page.description %}<div>{{ page.description|richtext }}</div>{% endif %} {% for block in page.get_effective_body %}{% include_block block %}{% endfor %} ``` Zero hardcode. Zero menção a "Conteúdos" ou "Aplicativos".

Verificação final (obrigatória)
docker compose restart web (blocks.py mudou)

Playwright abre /admin/, edita um canal, verifica os 2 novos blocos
na lista de blocos disponíveis

Playwright abre canal SEM body → fallback aparece (hero + carrossel)

Playwright abre canal COM body → só os blocos do gestor

pytest passa

O que NÃO fazer
Não alterar HomeStreamBlock para além de adicionar os 2 blocos novos

Não criar template duplicado em canais/templates/ — blocos vivem em core/

Não inventar design system paralelo

Não deixar hardcode residual no canal_page.html

Ordem de execução sugerida
LEITURA (R1) — não escrever nada até entender o padrão

core/blocks.py — 2 blocos novos

Templates dos blocos (reaproveitando CSS)

CSS/JS se necessário

get_effective_body() em canais/models.py

canal_page.html reescrito

Reiniciar, testar, verificar com Playwright