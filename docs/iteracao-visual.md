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

(a preencher a cada tentativa: o que tentou / funcionou / descartou e por quê)
