# Requisitos NOVA PAT vs. Sistema Legado

> Cruzamento entre `Levantamento de Requisitos para a Modernização da Nova PAT` (V1.0, 13/03/2026) e o comportamento real do sistema legado (ver `docs/schema-legado.md`). Objetivo: separar o que é "modernizar algo que já existe" do que é "construir algo novo do zero", e sinalizar decisões de arquitetura em aberto.

## Legenda
- ✅ **Confirma** — o legado já modela isso; a fase de transposição cobre.
- 🆕 **Novo** — sem equivalente no legado; feature nova, fora do escopo de "transpor".
- ⚠️ **Decisão pendente** — depende de escolha sua antes de modelar.

---

## Requisitos Funcionais

| RF | Nome | Status | Nota |
|---|---|---|---|
| RF001 | Busca Avançada | ✅ ⚠️ | Busca full-text já existe (tsvector); Wagtail search nativo substitui. Multi-critério (tipo, disciplina, nível, licença) é composição de filtros sobre entidades que já existem. **Lacuna real confirmada em produção (13/03/2026+)**: a busca hoje só retorna resultados dentro do canal "Recursos Educacionais" — não há filtro por `canal` na busca avançada, e navegar por outro canal não segue o termo buscado. `canal_id` já existe como campo indexado (`conteudos.canal_id`), então é filtro barato de adicionar — vale incluir explicitamente como critério na busca avançada da fase de transposição, não deixar para depois. |
| RF002 | Playlists Personalizadas | 🆕 | Não existe no legado. `Services/DashboardData.php` sugere alguma lógica de agregação, mas não achei model de playlist persistente com dono. Confirmar antes de modelar. |
| RF003 | Recomendação (IA) | 🆕 | Sem equivalente. Ver nota de tensão sobre "tecnologia livre e aberta" abaixo. |
| RF004 | Fóruns de Discussão | 🆕 | Sem equivalente — `comentarios` do legado é comentário simples em conteúdo, não fórum com threads. |
| RF005 | Leitor de PDF Integrado | 🆕 | Legado só oferece download; não há viewer embutido. |
| RF006 | Relatórios de Uso (Admin) | ✅ | `qt_downloads`/`qt_access` já são contados por conteúdo (RN-L6), dado bruto existe. Dashboard em si é novo — ver app `analytics/`, seção "Decisões de arquitetura já fechadas". Não confundir com a importação de Google Sheets (direção oposta, ver seção `Document`). |
| RF007 | Manutenção do Download | ✅ | Já é comportamento padrão do legado — manter. |
| RF008 | Vídeos estilo "streaming" (série → episódios) | ✅ | Resolvido: `Serie` → `Temporada` → `ConteudoPage` (episódio). Renomeado de "Programa" para "Serie" para não colidir com o jargão já usado na equipe ("programa de TV" = peça isolada, ex: telejornal). Ver seção "Decisões de arquitetura já fechadas". |
| RF009 | Gestão de Usuários e Perfis | ✅ | Roles já existem e são bem definidos (RN-L4). Modernizar UI/fluxo de cadastro, não a lógica de permissão. |
| RF010 | Favoritos Pessoais | ✅ | Resolvido: `FavoritoConteudo`, entidade própria, distinta de like e de avaliação. Ver seção "Decisões de arquitetura já fechadas". |
| RF011 | Avaliação e Feedback de Conteúdo | ✅ | Resolvido: `AvaliacaoConteudo` (nota 1-5) é entidade própria, separada de like. Média desnormalizada só para exibição, não usada em filtro/busca. Ver seção "Decisões de arquitetura já fechadas". |
| RF012 | Players Otimizados | ✅ | Já é conteúdo de mídia com tipo/formato; troca é de camada de apresentação (front), não de modelo de dado. |
| RF013 | Upload e Curadoria Otimizados | ✅ | Fluxo de aprovação (RN-L1) já existe e deve ser preservado; RF013 pede melhorar a UX de curadoria, não a regra. |
| RF014 | Expansão de Categorias | ✅ | `categories` já é árvore (`parent_id`) por canal — só precisa de UI de administração melhor. |

---

## Requisitos Não Funcionais — pontos de atenção

- **Segurança / LGPD (RN11)**: o legado já separa dado de usuário (`User`) de dado de conteúdo, mas não há evidência de mecanismo de consentimento/LGPD explícito nas migrations vistas. Precisa levantamento à parte antes da fase de gestão de usuários.
- **Acessibilidade WCAG 2.1 AA (RNF Acessibilidade / RN12)**: `conteudos.options` já tem campo de acessibilidade no jsonb do legado, mas não há garantia de que os dados migrados estejam preenchidos — checar completude ao migrar.
- **Escalabilidade (+50% em 2 anos sem rearquitetura)**: decisão de arquitetura Django/Wagtail em Docker já favorece isso; não é regra que muda o schema, é critério de infra (caching, queries).

---

## Tensões e pontos a esclarecer com quem emitiu o ToR

1. **Filosofia "Tecnologia Livre e Aberta (Mandatório)" vs. IA de recomendação (RF003 / seção 4c)**
   O documento pede que ferramentas de IA para recomendação **priorizem** bibliotecas open source (TensorFlow/PyTorch) — a palavra usada é "priorizando", não "exclusivamente". A cláusula de exclusividade mandatória (seção 4a) é sobre a stack geral do projeto (linguagens, frameworks, banco). Ainda assim, é uma zona cinzenta: se em algum momento a recomendação usar um serviço de IA fechado (ex: API de terceiros), vale checar com o cliente se isso conflita com a leitura que ele faz do "mandatório" antes de decidir, e não assumir que "priorizando" dá liberdade total.

2. **RN10 — "equipe de desenvolvimento" / pair programming**
   O documento inteiro pressupõe um time formal fazendo pair programming com a equipe interna do Instituto para transferência de conhecimento. Você está executando sozinho ("EUquipe"). Isso não invalida a entrega, mas é uma discrepância entre o que o ToR descreve como processo e a realidade de execução — vale deixar isso registrado (mesmo que só como nota interna sua) para não ser cobrado depois por um processo formal de pair programming que não está acontecendo da forma descrita.

3. **RN9 — migração com "integridade total"**
   Bate com a decisão já tomada de não migrar dados até o schema novo estabilizar (ver `schema-legado.md` e conversa sobre o importador isolado). "Integridade total" é compatível com migrar depois, desde que a migração final seja auditada campo a campo contra o legado — não é incompatível com adiar, é incompatível com migrar malfeito.

---

## Decisões de arquitetura já fechadas

### ConteudoPage x AplicativoEducacionalPage — não fundir
Ficam como models separados. `aplicativos` é semanticamente um link de saída pra ferramenta externa (sem tipo de mídia, sem player, sem arquivo), enquanto `conteudos` é recurso de mídia com player. Compartilham uma base abstrata comum (`RecursoBasePage`) só para os campos realmente iguais: `canal`, `category`, `tags`, atribuição de usuário. Motivo: no legado as duas já têm `Policy` diferentes (`AplicativoPolicy` vs `ConteudoPolicy`), sinal de que são entidades de propósito distinto.

### ConteudoPage — troca de player por tipo: template condicional, não StreamField
Um conteúdo mantém **um tipo só** (`tipo` como FK, igual ao legado — `ConteudoFormRequest`/`ValidExtensions` já pressupõem isso). A variação de player (vídeo, áudio, PDF, apresentação, download) é resolvida via `get_template()` na `ConteudoPage`, escolhendo o template pelo slug do `tipo`:

```python
def get_template(self, request, *args, **kwargs):
    return f"conteudos/conteudo_page_{self.tipo.slug}.html"
```

StreamField foi descartado para este caso — ele resolve o problema de conteúdo editorial composto e variável (não é o caso aqui: um conteúdo tem um tipo fixo, só a exibição varia) e adicionaria complexidade de migração sem necessidade. Se no futuro surgir um caso real de conteúdo composto (candidato: RF008, hierarquia de programa/episódio), StreamField pode ser reavaliado *para aquele caso específico*, não como padrão geral de `ConteudoPage`.

---

### Favorito, Like e Avaliação — três entidades distintas, não uma
Resolvido: são três conceitos diferentes, com três models.

- **`FavoritoConteudo`** — requer usuário logado (dado pessoal, não engajamento público). `user` + `conteudo`, único por par.
- **`Like`** — mantém o padrão binário já existente no legado (`conteudos_likes`), só migrando pro app novo.
- **`AvaliacaoConteudo`** — nota 1 a 5 por usuário/conteúdo (único por par, permite reeditar). Pensado para uso futuro em curadoria/ranking, mas **decisão explícita: não entra como critério de busca/filtro/ordenação por enquanto** — preocupação levantada foi que poucos votos negativos (ex: "hate" de alunos) poderiam esconder conteúdo bom se usado como filtro direto. A média (`media_avaliacao`, `total_avaliacoes`) é desnormalizada no `ConteudoPage` via signal apenas para **exibição discreta** no card de busca (evita agregação por item numa lista de 20.000+ conteúdos), nunca usada em `WHERE`/`ORDER BY`. Se no futuro quiser usar como critério de busca, isso é uma nova decisão de produto, não implícita nesta.

---

### RF008 — Organização estilo streaming (Serie → Temporada → Episódio)
Resolvido. Modelo decidido:

```python
class Serie(RecursoBasePage):           # Page, independente de Canal
    sinopse = models.TextField(blank=True)
    capa = models.ForeignKey('wagtailimages.Image', null=True, blank=True, ...)

class Temporada(Page):                   # filha de Serie
    parent_page_types = ['series.Serie']
    numero = models.PositiveSmallIntegerField()

class ConteudoPage(RecursoBasePage):
    parent_page_types = ['canais.CanalPage', 'programas.Temporada']
    numero_episodio = models.PositiveSmallIntegerField(null=True, blank=True)  # ordenação manual do curador
```

Decisões que fecham o modelo:
- Vídeo avulso continua existindo — Serie é opcional, não todo vídeo precisa pertencer a uma série.
- Existe conceito de Temporada (Serie → Temporada → Episódios), não só Serie → Episódios direto.
- Ordenação dos episódios dentro da temporada é manual (`numero_episodio`, definido pelo curador), não por data de publicação.
- Serie é independente de Canal (não herda nem é restrito a um canal específico).
- Episódio **não é uma entidade nova** — é a própria `ConteudoPage` (mesmo model de vídeo que já existe), só posicionada na árvore como filha de uma `Temporada` em vez de um `CanalPage`. O indicador visual de "você está assistindo um episódio de uma série" (breadcrumb Serie › Temporada › Episódio, lista de outros episódios) é resolvido no template a partir da posição na árvore (`get_parent()`/`get_siblings()`), sem precisar de campo extra pra isso.
- **Confirmado no schema legado**: `conteudos.canal_id` é FK direta (`nullable`, mas nunca múltipla) — não existe tabela pivô `conteudo_canal`. Um conteúdo pertence a no máximo um canal. Isso reforça manter `canal` como FK simples na `ConteudoPage` (não M2M), inclusive para episódios.
- **Sobre o nome "Serie" (não "Programa")**: no legado, "Programa" já é o termo usado pela equipe pra uma peça de TV isolada (ex: um telejornal), sem relação com hierarquia de série/temporada. Pra não confundir curador nem dev, a entidade nova foi renomeada de `Programa` para `Serie`. Ver `canais/CLAUDE.md` para a nota completa sobre esse conflito de nomenclatura.

---

## Varredura de fechamento — entidades do legado ainda sem app atribuído
Antes de escrever `importador/CLAUDE.md`, foi feita uma varredura cruzando todos os `Policies`/`Models` do legado contra os 8 apps já documentados (`core`, `canais`, `conteudos`, `series`, `curriculo`, `interacoes`, `aplicativos`, `usuarios`). Achados:

### `PlayList` — correção de status do RF002
**RF002 estava marcado 🆕 ("sem equivalente no legado") — errado.** `PlayList` existe (`app/Models/PlayList.php`, extends `Document`). Mas o legado implementa só **metade** do que o RF002 pede: a `PlayListPolicy::create()` restringe criação a `super-admin`/`admin` — bate com a parte do RF002 de "administradores/curadores podem criar playlists temáticas", mas **não existe** a outra metade pedida ("usuários logados podem criar suas próprias playlists"). Ou seja: playlist curada por admin é transposição; playlist pessoal de usuário comum é construção nova.

**Anti-padrão a não replicar**: `PlayList` e `Document` (ver abaixo) compartilham a mesma tabela (`documents`) sem coluna discriminadora de tipo — são distinguidos só por convenção (prefixo `pl-` no slug). Pior ainda, a lista de conteúdos de uma playlist é um array de IDs dentro do campo jsonb (`document.ids: [...]`), não uma relação M2M de verdade — sem integridade referencial, sem cascade, sem lookup reverso fácil ("em quais playlists este conteúdo aparece"). **Não replicar esse padrão.** Na NOVA PAT, modelar `Playlist` como model próprio com M2M real pra `ConteudoPage` (through-model se precisar de campo `ordem`, já que a lista original é ordenada).

### `Document` — integração com Google Sheets: duas necessidades separadas, não uma
Confirmado com o dono do produto: são **duas direções distintas**, não devem virar o mesmo app.

1. **Importação de planilha → conteúdo** (transposição, o que o legado já faz via `Document.getGoogleSpreadsheetsData()`): puxa dado de uma planilha Google pra dentro da PAT. Não justifica app próprio — é um método/service utilitário (usar `gspread` como dependência) chamado a partir de onde o dado importado é consumido. Atenção: `gspread` teve recentemente um aviso de busca por novos mantenedores no repositório oficial — checar status atual antes de travar essa dependência num projeto público de longo prazo.
2. **BI/relatório de uso** (RF006, construção nova): a plataforma gera métrica própria (`qt_access`, `qt_downloads`, engajamento de `interacoes`) e expõe via painel — direção **oposta** à da importação. Ver app novo `analytics/` abaixo.

### `analytics/` — app novo para RF006 (Geração de Relatórios de Uso)
Consome dados já existentes em `conteudos` (`qt_access`, `qt_downloads`) e `interacoes` (likes, favoritos, avaliações), agregando para dashboard administrativo. Só leitura desses apps — não escreve neles. Se exportação para BI externo (Data Studio etc.) for confirmada como requisito real mais adiante, a direção do `gspread` aqui seria **exportar pra fora**, não importar — não confundir com a necessidade 1 acima. Painel administrativo básico pode ser resolvido nativamente (gráfico simples no admin do Wagtail ou lib de charting Python) sem depender de Sheets/BI externo para a primeira versão.

### `Options` — configuração global do site
Chave-valor (`name` + `meta_data` jsonb) pra configuração geral do site (o método `createDestaque`, restrito a `super-admin`, sugere que "destaques" da home são geridos por aqui). Restrito a `super-admin`/`admin`. Mapeia bem pro padrão nativo do Wagtail (`BaseSiteSetting`) em vez de precisar de app próprio — avaliar na hora de implementar.

### `Contato` — formulário de contato
Simples (`name`, `email`, `url`, `subject`, `message`, `action`). Criação aberta a qualquer um (`ContatoPolicy::create()` retorna `true` sempre, inclusive anônimo). Baixa complexidade, não decisão de arquitetura relevante — pode virar um app `contato/` enxuto ou form simples dentro de `core`.

### `Resumo` — código morto, nada a transpor
Existe `ResumoPolicy.php`, mas **o model `Resumo` não existe** no repositório — foi apagado (ou nunca criado) e a Policy ficou órfã. Não há nada para migrar aqui; mencionar só para não gerar confusão caso alguém veja a Policy e presuma que existe uma feature "Resumo" ativa.

### Nomenclatura — nada de errado adicional encontrado
Revisão cruzada de nomes de model/Policy contra os 8 `CLAUDE.md` já escritos não achou mais inconsistência de nome além das já corrigidas (`AplicativoPage` → `AplicativoEducacionalPage`, `Programa` → `Serie`, papéis reais `editor`/`convidado`).

---

## Como isso deve ser usado nos `CLAUDE.md` por app

Cada app (`conteudos/`, `curriculo/`, etc.) deve referenciar a seção correspondente deste documento e do `schema-legado.md` no seu próprio `CLAUDE.md`, indicando explicitamente se o app está em fase de **transposição** (RF marcado ✅) ou **construção nova** (RF marcado 🆕/⚠️) — isso evita que um agente de IA tente "adivinhar" uma regra de negócio que na verdade ainda não foi decidida.