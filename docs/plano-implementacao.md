# Plano de Implementação Macro — Nova PAT

Data: 30/10/2026

## Fase 1 — Consolidação do Core
**Objetivo:** estabilizar o núcleo: salvamento de conteúdo, trilha de auditoria e configuração global.
**Pronto:** NOVAPAT-69 entregado; 211 testes aprovados; ADR-005 aceito.
**Próximos passos (specs):** NOVAPAT-70 (bug ConteudoPage), NOVAPAT-51 (django-simple-history: models auditados, dependência, migrações), NOVAPAT-46 (Options via BaseSiteSetting + Contato).
**Aceite:** ConteudoPage salva tags e upload; histórico nos models definidos; Options e Contato com testes.

## Fase 2 — Gestão de Usuários e Contato
**Objetivo:** auto-cadastro seguro e formulário de contato.
**Pronto:** model User com verified/verification_token; Contato em docs/requisitos-vs-legado.md:129.
**Próximos passos (specs):** NOVAPAT-45 (cadastro/verificação, validadores fortes, token 1h, papel convidado), NOVAPAT-46 (form Contato, envio por anônimos).
**Aceite:** cadastro com validadores ativos; token expira em 1h; contato por anônimos; testes cobrindo ambos.

## Fase 3 — Engajamento e Relatórios de Uso (RF006)
**Objetivo:** painel de métricas para admin, regra LGPD "caixa preta" (sem usuário×conteúdo).
**Pronto:** qt_access/qt_downloads em conteudos; interacoes modeladas; analytics/ só com ARCHITECTURE.md.
**Próximos passos (specs):** NOVAPAT-58 (analytics em INSTALLED_APPS, agregações, painel admin, testes).
**Aceite:** app analytics registrado, agregações e painel funcionando, caixa preta respeitada, testes verdes.

## Fase 4 — Importação e Migração de Dados
**Objetivo:** trazer planilhas Google e dados do legado para a NOVA PAT.
**Pronto:** importador/ com ARCHITECTURE.md; sem command; gspread não em requirements.txt.
**Próximos passos (specs):** NOVAPAT-59 (avaliar gspread, command idempotente, manter ou não o app), NOVAPAT-71 (nova: plano de migração do legado campo a campo, pós-estabilização do schema).
**Aceite:** command idempotente com teste; plano de migração do legado registrado.

## Fase 5 — Operações e Continuidade (Infra)
**Objetivo:** backup, recuperação e RTO/RPO definidos com o cliente.
**Pronto:** runbook-backup-dr.md esqueleto (status vermelho).
**Próximos passos (specs):** NOVAPAT-54 (pg_dump Postgres, mídia, código/git, segredos; RTO/RPO; teste de restauração).
**Aceite:** backup rodando; RTO/RPO no runbook; teste de restauração executado e registrado.
