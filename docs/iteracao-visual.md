# Iteração visual — hero e carrossel do canal (Fase 2)

Bússola: Nova PAT é plataforma de conteúdo educacional. O player de mídia é o
protagonista, não decoração de fundo. Referências mentais: MIT OpenCourseWare,
Coursera, edX, BBC Bitesize, TV Cultura digital. Sóbrio, confiável,
institucional moderno. Envelope: Tailwind CDN, paleta brand-50..700, WCAG 2.1 AA
(contraste, focus-visible, aria-labels), zero JS novo (scroll-snap + CSS puro),
reaproveitar classes dos blocos existentes.

## Iteração 0 — baseline (antes do refinamento)

- **Fix aprovado e aplicado:** hero `min-h-[60vh]` → `min-h-[70vh]` (alinha ao
  `hero_block`, corrige espaço vazio excessivo no topo).
- **Fix de bug:** comentários `{# #}` multilinha → `{% comment %}` em
  `canal_page.html`, `ultimo_conteudo_player.html`,
  `ultimos_conteudos_carrossel.html` (vazavam como texto renderizado).
- Dados: 52 conteúdos seed (5 canais × 10 + 2 extras criados por execuções), com
  capa PNG gerada localmente e stubs MP4/MP3 (players renderizam controles).
- Estado conhecido do hero: título 4xl/5xl à esquerda, player abaixo do título,
  CTA "Ver conteúdo". Hoje o player fica "espremido" dentro da coluna
  `max-w-3xl` — problema real de hierarquia: o protagonista (player) ocupa o
  mesmo espaço do texto de apoio.
- Estado conhecido do carrossel: cards com capa 16:9 + título + tipo; passadores
  são links numerados com aparência de botão primário (grande demais para o
  papel secundário de paginação; sem indicador de página ativa).

## Iterações

### Iteração 1 — cabeçalho do canal + hero protagonista + paginadores discretos

**O que tentei:**
- `canal_page.html`: `<h1>` cru e descrição solta fora de container → cabeçalho
  de página padronizado (`max-w-7xl`, `py-12`, `text-3xl/4xl font-bold`,
  descrição `text-lg leading-relaxed max-w-3xl`), mesmo container das seções.
- `ultimo_conteudo_player.html`: texto e player empilhados numa coluna só
  (`max-w-3xl`) → grade assimétrica em lg (`grid-cols-5`, texto 2/5, player
  3/5): o player vira protagonista. Adicionados: etiqueta de tipo (`uppercase
  tracking-wide text-brand-100`), data de publicação (`text-sm text-white/70`),
  gradiente direcional (`from-black/80 via-black/60 to-black/40`) em vez do
  véu uniforme, `poster` do vídeo a partir da og_image. Sem mídia, a coluna do
  player não renderiza e o texto ocupa sozinho (degradação editorial).
- `ultimos_conteudos_carrossel.html`: paginadores eram botões primários
  grandes (`px-6 py-3`) → chips circulares discretos
  (`h-9 w-9 rounded-full ring-1 ring-brand-200 text-brand-700 bg-white`),
  alinhados à direita. Peso visual alinhado à função secundária.

**O que funcionou:** markup validado no servidor local (h1 estilizado, hero em
grid, áudio full-width, nav compacta). Suíte completa: 199 passed.

**Descartado:** `min-h-[70vh]` removido do hero — com a grade 2/5+3/5 a altura
vem do conteúdo (player 16:9 define o ritmo); altura mínima fixa só criava
vácuo. Indicador de página ativa nos dots: sem JS não há seletor CSS puro
confiável o suficiente para isso no envelope (zero JS novo) — ficou `aria-label`
descritivo por dot.

**Pendente:** confirmação visual real (screenshot) — neste container o modelo
não lê imagem; resta avaliação por markup + revisão humana.

