# analytics/ — CLAUDE.md

## Papel deste app
`analytics` cobre RF006 (Relatórios de Uso — Admin). Construção nova, sem equivalente direto no legado além dos contadores brutos que já existem.

Fonte da verdade: `docs/requisitos-vs-legado.md` (RF006 e seção "Document — Google Sheets: duas necessidades separadas").

## Fase atual: construção nova

## Dados que já existem e este app só consome (não escreve)
- `conteudos.qt_access`, `conteudos.qt_downloads` (app `conteudos`)
- `interacoes` — likes, favoritos, avaliações (app `interacoes`)

## Direção — não confundir com importação de Sheets
Este app é sobre a PAT **gerar** métrica própria e expor via painel — direção oposta à importação de planilha pra dentro da plataforma (essa outra necessidade não tem app próprio, é método utilitário via `gspread` onde o dado importado for consumido, ver `docs/requisitos-vs-legado.md`).

## Restrição de privacidade — caixa preta para cruzamento individual (decisão fechada)
O par usuário↔conteúdo (quem curtiu/favoritou/avaliou o quê) existe no banco por necessidade funcional dos apps `interacoes` (é o que evita, por exemplo, curtida duplicada — ver `unique_together` em `interacoes/CLAUDE.md`). Isso é esperado e correto. **O que não pode acontecer**: o dashboard deste app nunca deve expor, filtrar ou permitir drill-down desse cruzamento em nível individual — nem para "quais conteúdos o usuário X curtiu", nem para "quais usuários curtiram o conteúdo Y". Só números já agregados por conteúdo. Essa restrição vale mesmo para `super-admin` dentro do dashboard — ver `docs/lgpd-mapeamento-dados.md` para o raciocínio completo.

## Escopo da primeira versão
Painel administrativo básico, resolvido nativamente (admin do Wagtail + lib de charting Python simples), sem depender de exportação pra BI externo. Se exportação para Data Studio/Sheets virar requisito confirmado mais adiante, é extensão futura — não presumir escopo além do dashboard admin nesta fase.

## O que NÃO fazer neste app
- Não escrever em `conteudos`/`interacoes` a partir daqui — só leitura/agregação.
- Não misturar a lógica de importação de Google Sheets aqui — são necessidades de direção oposta.
- Não assumir exportação pra BI externo como parte do escopo atual sem confirmação nova.
