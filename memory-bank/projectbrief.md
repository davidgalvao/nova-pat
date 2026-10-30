# Project Brief — Nova PAT

- **O que é:** Nova PAT (Plataforma Anísio Teixeira), portal educacional de vídeos, documentos, apresentações e aplicativos educacionais organizado por canais.
- **Objetivo principal:** transposição (não greenfield) do sistema legado Laravel + Vue.js, que está em produção, para Django 6 + Wagtail 8. Critério de pronto: paridade de comportamento com o legado. Não existe "MVP".
- **Escopo macro:** canais, conteúdos com players por formato, aplicativos educacionais, busca avançada, séries/temporadas/episódios, currículo (níveis e componentes), interações (like/favorito/avaliação/comentário), usuários e papéis, relatórios de uso.
- **Stack:** Docker + Postgres 15, Tailwind via CDN, templates Django/Wagtail (WCAG 2.1 AA), i18n pt-br / America/Sao_Paulo.
- **Fontes da verdade:** docs/schema-legado.md e docs/requisitos-vs-legado.md; ADRs em docs/adr/ vencem em decisão de arquitetura.
- A métrica de sucesso é comportamento igual ao legado; anti-padrões documentados não são replicados.

## Referência do legado
- Repositório do sistema legado (Laravel): https://github.com/nikoz84/plataforma-anisio-teixeira — referência técnica do comportamento antigo a ser transposto.
- Importante: pode estar desatualizado em relação à produção. Use para entender estrutura de dados e regras antigas, mas **NUNCA** como fonte da verdade final se os `docs/` da NOVA PAT disserem o contrário.
