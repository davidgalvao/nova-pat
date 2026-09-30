# Plano para Refinamento Visual dos Blocos de Fallback e Canal Page

## A. Bugs visuais — o que, onde, como corrigir (descrição)

1. **Comentários {# ... #} aparecendo como texto**
   - **Ocorrências:**
     - `canais/templates/canais/canal_page.html`, linhas 14-15 (comentário multilinha sobre composição editorial)
     - `core/templates/blocks/ultimos_conteudos_carrossel.html`, linhas 2-4 (descrição do carrossel) e linhas 45-46 (descrição dos passadores)
     - `core/templates/blocks/ultimo_conteudo_player.html`, linhas 2 (descrição do hero) e linha 6 (comentário sobre imagem de fundo)
   - **Como corrigir:** Substituir comentários `{# ... #}` por `{% comment %}...{% endcomment %}` pois o Django apenas processa `{# #}` em linha única.

2. **Hero com altura `min-h-[60vh]` empurrando conteúdo para baixo**
   - **Local:** `core/templates/blocks/ultimo_conteudo_player.html`, linha 4
   - **Análise:** O hero usa flexbox com `items-center` para centralizar verticalmente o conteúdo interno. Porém, a altura mínima de 60vh combinada com o padding interno (`py-20`) pode estar causando excesso de espaço acima do conteúdo em telas menores. O bloco `hero_block.html` usa `min-h-[70vh]` com o mesmo padding interno e não apresenta o problema relatado.
   - **Como corrigir:** Primeiro, alterar `min-h-[60vh]` para `min-h-[70vh]` para manter consistência com `hero_block`. Se o problema persistir, ajustar o padding-top interno (reduzir de `py-20` para um valor menor) para mover o conteúdo para cima, mantendo a simetria visual sempre que possível.

## B. Diagnóstico estético — análise do que existe

- **Padrões observados nos blocos existentes** (`hero_block`, `full_banner_block`, `carrossel_categoria_block`, `destaques_manuais_block`, `feature_grid_block`):
  - **Layout:** Contêores externos com `mx-auto w-full max-w-7xl px-4 py-12 sm:px-6 lg:px-8` (exceto blocos de hero/banner que usam padding interno no bloco filho).
  - **Cores:** Uso consistente das cores da marca definidas no Tailwind (`brand-500`, `brand-600`, `brand-700`, `brand-50`, etc.).
  - **Tipografia:** Títulos em `text-2xl font-bold text-gray-900 sm:text-3xl` para seções; `text-4xl font-extrabold leading-tight text-white` para heroes.
  - **Botões:** Estilo primário: `inline-flex items-center justify-center rounded-md bg-brand-500 px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-700`.
  - **Acessibilidade:** Atributos `aria-label` em seções e botões, estilos de foco visível (`focus-visible:ring-*`), contraste adequado assumido nas cores da marca.
  - **Componentização:** Nenhuma extração evidente necessária nos blocos atuais; padrão utility-first do Tailwind é seguido.

- **Análise dos blocos alvo:**
  - `ultimo_conteudo_player.html`: Já segue muitos padrões do `hero_block` (cores, padding interno, estilo de botão, overlay). Diferenças principais: altura mínima (`60vh` vs `70vh`) e tratamento específico de mídia (vídeo/áudio).
  - `ultimos_conteudos_carrossel.html`: Totalmente consistente com padrões de seções não-hero (padding externo, título, estilo de botão de paginação, classes de cartão idênticas ao `carrossel_categoria_block`).

## C. Proposta de mudanças — arquivo por arquivo, descritivo

### 1. `canais/templates/canais/canal_page.html`
   - **Mudança:** Substituir o bloco de comentário multilinha (linhas 14-15) por:
     ```django
     {% comment %}
     Composição editorial efetiva: blocos do gestor (body) ou
     fallback sintético (hero player + carrossel) — zero hardcode.
     {% endcomment %}
     ```

### 2. `core/templates/blocks/ultimos_conteudos_carrossel.html`
   - **Mudanças:**
     - Linhas 2-4: Substituir por:
       ```django
       {% comment %}
       Carrossel dos últimos conteúdos do canal: 9 itens, 3 por página,
          passadores prev/next via CSS scroll-snap puro (sem JS — R3).
          Classes reaproveitadas de carrossel_categoria_block.html (R2).
       {% endcomment %}
       ```
     - Linhas 45-46: Substituir por:
       ```django
       {% comment %}
       Passadores: UM único nav, fora do scroll container.
          Âncoras #pagina-N rolam o container via scroll-snap (sem JS — R3).
       {% endcomment %}
       ```

### 3. `core/templates/blocks/ultimo_conteudo_player.html`
   - **Mudanças:**
     - Linha 2: Substituir por:
       ```django
       {% comment %}
       Hero com o último conteúdo do canal em player (vídeo/áudio) ou capa com link.
       {% endcomment %}
       ```
     - Linha 6: Substituir por:
       ```django
       {% comment %}
       Imagem de fundo com sobreposição de gradiente para legibilidade (mesmo padrão do hero_block)
       {% endcomment %}
       ```
     - Linha 4: Alterar `min-h-[60vh]` para `min-h-[70vh]` (alinhado com `hero_block`).
     - **Se após teste o problema de espaçamento persistir:** Considerar reduzir o `padding-top` interno do bloco filho (classe `px-4 py-20 sm:px-6 lg:px-8`) para `pt-10 pb-20 sm:px-6 lg:px-8` (reduz padding-top de 5rem para 2.5rem, mantendo padding-bottom em 5rem) para mover o conteúdo para cima sem alterar a altura mínima.

### 4. Considerações de refinamento visual adicional (se necessário após correção de bugs)
   - **`ultimo_conteudo_player.html`:** Verificar se os elementos `<video>` e `<audio>` necessitam de estilos de foco explícitos para acessibilidade (por exemplo, adicionar `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-700`). Porém, como são controles nativos, pode ser que já tenham estilos adequados do navegador; validar em testes.
   - **`ultimos_conteudos_carrossel.html`:** Nenhuma mudança visual necessária além da correção de comentários; já segue padrões estabelecidos.

## D. Riscos e trade-offs

- **Risco de alterar CSS global:** Nenhum, pois não estamos modificando arquivos CSS nem introduzindo novas classes. Todas as alterações são confinadas aos templates e utilizam classes existentes do Tailwind ou padrões já presentes nos blocos.
- **Trade-off na ajuste de altura do hero:** Alterar `min-h-[60vh]` para `min-h-[70vh]` aumenta a altura do hero em telas maiores, o pode afetar a quantidade de conteúdo visível acima da dobra. Porém, mantém consistência com o `hero_block` existente e é mais provável que resolva o problema de espaçamento.
- **Trade-off no ajuste de padding assimétrico:** Se for necessário reduzir apenas o padding-top, introdói assimetria visual no bloco. Porém, essa alteração seria apenas se a mudança de altura mínima não resolver o problema, e seria feita com cuidado para não afetar negativamente a aparência em diferentes tamanhos de tela.
- **Risco de quebra em blocos existentes:** Nenhum, pois não estamos alterando blocos existentes (`hero_block`, `carrossel_categoria_block`, etc.), apenas os dois blocos de fallback e o template de página de canal.

## E. Proposta de testes

1. **Testes de correção de bugs:**
   - Verificar que os comentários `{# ... #}` não aparecem mais como texto renderizado na página (inspecionar o HTML gerado).
   - Confirmar que o hero não apresenta espaçamento excessivo acima do conteúdo em diferentes tamanhos de tela (desktop, tablet, mobile).

2. **Testes de renderização dos blocos:**
   - **`UltimoConteudoPlayerBlock`:**
     - `get_effective_body()`: retornar `body` quando preenchido, fallback quando vazio, tratar `StreamValue` válido.
     - `get_context()`: buscar último conteúdo do canal; retornar `None` fora do contexto de canal.
     - Renderização: bloco renderiza corretamente com dados (vídeo, áudio, imagem) e sem dados (não exibe nada).
     - Edge cases: canal sem conteúdos, conteúdo sem `og_image`, mecanismo de exibição desconhecido (não vídeo nem áudio).
   - **`UltimosConteudosCarrosselBlock`:**
     - `get_context()`: buscar últimos 9 conteúdos do canal; agrupar em páginas de 3.
     - Renderização: bloco renderiza com dados (mostra carrossel com 3 items por página) e sem dados (exibe mensagem vazia ou não renderiza se `paginas` vazio).
     - Edge cases: canal com menos de 9 conteúdos, canal sem conteúdos, mecanismo de exibição variado.

3. **Testes de acessibilidade (WCAG 2.1 AA):**
   - Verificar contraste de texto em fundos (usando ferramentas de desenvolvedor).
   - Confirmar que todos os elementos interativos têm indicadores de foco visíveis.
   - Garantir que atributos `aria-label` sejam significativos e presentes onde necessário.

4. **Testes de regressão:**
   - Assegurar que os blocos existentes (`hero_block`, `carrossel_categoria_block`, etc.) continuam renderizando corretamente após as alterações (nenhum impacto esperado).

**Próximos passos:** Aguardar aprovação deste plano antes de prosseguir com as alterações.