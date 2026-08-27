# ADR-004 — Workflow de aprovação por lógica de role explícita

- **Status**: ✅ Aceito
- **Data**: 2026-08-27
- **Decisões relacionadas**: D7 (fechamento de pendência conceitual); D2 (papel `editor`)

## Contexto

O `docs/schema-legado.md` levantou a dúvida entre usar o workflow de aprovação builtin do Wagtail ou replicar a lógica de role explícita do legado. A regra de negócio confirmada (RN-L1) é: **quem publica direto é amarrado a role** (`super-admin`/`admin`/`coordenador`), não a permissão de página.

O código atual usa `is_approved` (booleano) + métodos `can_create`/`can_edit`/`can_delete` nos ModelAdmin de cada app, replicando a lógica de role.

## Decisão

**Replicar a lógica de role explícita** (RN-L1), **não** o workflow builtin do Wagtail.

Justificativa:
- O workflow builtin do Wagtail modela aprovação por permissão de página/etapas, não a semântica "quem pode publicar direto por role" do legado — exigiria customização pesada.
- A lógica de role explícita já está implementada e é fiel ao comportamento real do legado.

**Nota sobre o papel `editor` (D2)**: a decisão atual é que `editor` não tem permissão de criação (igual a `convidado`). Se no futuro o produto decidir que `editor` cria conteúdo com aprovação pendente, isso é uma **mudança deliberada de regra de negócio** que deve ser registrada como novo ADR substituindo este, e exigirá implementar o fluxo de moderação que hoje não existe.

## Consequências

**Positivas:**
- Fiel ao legado (RN-L1).
- Controle fino por role, já implementado nos ModelAdmin.

**Negativas / riscos:**
- Não usa o workflow nativo do Wagtail (perde features como notificações e etapas).
- A lógica de aprovação fica **espalhada** nos `can_*` de cada ModelAdmin (conteudos, aplicativos, series, canais, usuarios, interacoes) — risco de divergência entre apps.

**Mitigação:**
- **Candidata a centralização futura**: extrair um mixin de permissão baseado em role (ex: `RolePermissionMixin`) para eliminar a duplicação dos `can_*`. Registrar como melhoria futura, não escopo atual.