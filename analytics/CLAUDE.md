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

## Escopo da primeira versão
Painel administrativo básico, resolvido nativamente (admin do Wagtail + lib de charting Python simples), sem depender de exportação pra BI externo. Se exportação para Data Studio/Sheets virar requisito confirmado mais adiante, é extensão futura — não presumir escopo além do dashboard admin nesta fase.

## O que NÃO fazer neste app
- Não escrever em `conteudos`/`interacoes` a partir daqui — só leitura/agregação.
- Não misturar a lógica de importação de Google Sheets aqui — são necessidades de direção oposta.
- Não assumir exportação pra BI externo como parte do escopo atual sem confirmação nova.