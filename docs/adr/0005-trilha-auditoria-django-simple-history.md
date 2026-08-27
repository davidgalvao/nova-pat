# ADR-005 — Trilha de auditoria com `django-simple-history`

- **Status**: ✅ Aceito
- **Data**: 2026-08-27
- **Decisões relacionadas**: D8 (fechamento de pendência conceitual); `docs/runbook-backup-dr.md`; `docs/lgpd-mapeamento-dados.md`

## Contexto

O `docs/runbook-backup-dr.md` deixou em aberto entre `django-simple-history` e log estruturado próprio para a trilha de auditoria. A LGPD (e o regime de Poder Público) exige trilha de auditoria de **retenção indefinida** — registrar quem criou/editou/excluiu um registro, com o mínimo necessário (ex: ID do usuário, não o perfil inteiro) para minimizar exposição de dado pessoal.

Há duas categorias distintas de log, com regra de retenção diferente:
- **Trilha de auditoria** (quem alterou o quê): retenção indefinida — accountability de sistema público.
- **Log de acesso bruto** (IP, timestamp de requisição): retenção proposta de ~90 dias — fica em nível de infraestrutura (servidor web/WAF), fora do escopo de model.

## Decisão

**Adotar `django-simple-history`** para os models que exigem accountability (usuários, conteúdo, aplicativo, taxonomias), registrando o mínimo necessário (ID do usuário, não o perfil inteiro).

O **log de acesso bruto** fica em nível de infraestrutura (fora do escopo de model de aplicação), conforme já definido no `runbook-backup-dr.md`.

## Consequências

**Positivas:**
- Solução madura, testada e amplamente usada no ecossistema Django.
- Histórico por model, alinhado à decisão LGPD de retenção indefinida.
- Reduz esforço de implementação vs. log estruturado próprio.

**Negativas / riscos:**
- Nova dependência no projeto.
- Tabelas de histórico adicionais por model.
- Requer configurar `HistoricalRecords` por model e decidir **quais** models entram (nem todos precisam de trilha).

**Pendências:**
- Definir a lista exata de models que recebem `HistoricalRecords` (prioridade: `User`, `ConteudoPage`, `AplicativoEducacionalPage`, taxonomias).
- Confirmar se a PRODEB tem política própria de log antes de fixar a retenção de 90 dias do log bruto (se tiver, o padrão da PRODEB prevalece).