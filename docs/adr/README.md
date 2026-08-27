# Architecture Decision Records (ADR) — Nova PAT

> Registro sequencial e rastreável das decisões de arquitetura do projeto. Cada ADR segue o formato **Contexto → Decisão → Consequências** e é a fonte de verdade para *por que* o código está como está. Se um `CLAUDE.md` de app e um ADR divergirem, o ADR é a fonte de verdade da decisão de arquitetura; o `CLAUDE.md` deve ser atualizado para refletir o ADR.

## Como usar

- **Antes de alterar** um comportamento coberto por um ADR, leia o ADR correspondente. Não reabra uma decisão fechada sem um motivo de produto/negócio novo e real.
- **Ao tomar uma decisão nova** de arquitetura, crie um novo ADR numerado (próximo número sequencial) e adicione-o ao índice abaixo.
- **Ao mudar uma decisão**, não edite o ADR antigo apagando o histórico — registre um novo ADR que "substitui" o anterior (padrão `ADR-XXX` → `ADR-YYY`), preservando a trilha.

## Índice

| ADR | Título | Status | Decisão |
|---|---|---|---|
| [ADR-001](0001-aplicativo-herda-recurso-base-page.md) | `AplicativoEducacionalPage` herda `RecursoBasePage` | ✅ Aceito | Manter herança, sobrescrevendo `canal` |
| [ADR-002](0002-canal-fixo-aplicativos.md) | Canal fixo `id=9` para aplicativos | ✅ Aceito | Manter fixo, extrair constante `CANAL_ID` |
| [ADR-003](0003-busca-ambos-por-ids.md) | Busca "ambos" combina por IDs, não `union()` | ✅ Aceito | Manter combinação por IDs, documentar limitação |
| [ADR-004](0004-workflow-aprovacao-role-explicita.md) | Workflow de aprovação por lógica de role explícita | ✅ Aceito | Replicar RN-L1, não workflow builtin do Wagtail |
| [ADR-005](0005-trilha-auditoria-django-simple-history.md) | Trilha de auditoria com `django-simple-history` | ✅ Aceito | Adotar `django-simple-history` |

## Decisões de negócio relacionadas (não são ADR, mas afetam arquitetura)

Estas decisões foram fechadas junto com os ADRs e estão documentadas nos respectivos `CLAUDE.md`/`docs`:

- **D1 — `user_canal`**: vínculo informativo (sem efeito de permissão) na fase atual; reavaliar com acesso a produção. Ver `usuarios/CLAUDE.md`.
- **D2 — papel `editor`**: sem permissão implementada (igual a `convidado`); candidato futuro a "criar com aprovação pendente", vinculado ao ADR-004. Ver `usuarios/CLAUDE.md` e `docs/matriz-permissoes-rbac.md`.
- **D5 — `FlexLayoutMixin`**: mantido com docstring de uso pretendido (landing pages), nunca em conteúdo. Ver `core/models.py` e `core/CLAUDE.md`.