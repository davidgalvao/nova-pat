# ADR-001 — `AplicativoEducacionalPage` herda `RecursoBasePage`

- **Status**: ✅ Aceito
- **Data**: 2026-08-27
- **Decisões relacionadas**: D3 (fechamento de pendência conceitual)

## Contexto

O `core/ARCHITECTURE.md` deixou em aberto se `AplicativoEducacionalPage` deveria herdar `RecursoBasePage` (a base abstrata compartilhada com `ConteudoPage`) ou repetir os campos `canal`/`autor`/`tags` diretamente. O argumento para repetir era que "pouco é compartilhado de fato" (só canal e autor).

O código atual **já herda** `RecursoBasePage` e sobrescreve o campo `canal` para `null=True` (já que aplicativo não pertence a um canal escolhido pelo usuário — ver ADR-002). A dúvida era se essa herança deveria ser mantida ou revertida.

## Decisão

**Manter a herança de `RecursoBasePage`** em `AplicativoEducacionalPage`, sobrescrevendo o campo `canal` (null=True) e fixando-o no `save()`.

Justificativa:
- Os campos realmente compartilhados (`canal`, `autor`, `tags`) são reais e usados — não é herança "por conveniência".
- A sobrescrita de `canal` resolve a única diferença de comportamento relevante entre os dois domínios.
- Manter a herança garante consistência de painéis e de comportamento com `ConteudoPage`, reduzindo duplicação.

## Consequências

**Positivas:**
- Reuso real de campos, painéis e validações herdadas.
- Consistência estrutural entre `ConteudoPage` e `AplicativoEducacionalPage`.

**Negativas / riscos:**
- O campo `canal` herdado precisa ser sobrescrito (já feito) — se `RecursoBasePage` evoluir, é preciso garantir que a sobrescrita continue válida.
- Risco de herdar comportamento indesejado de `RecursoBasePage` no futuro (ex: novos campos obrigatórios que não fazem sentido para aplicativo).

**Mitigação:**
- A sobrescrita de `canal` deve ser mantida como decisão explícita e documentada no model.
- Qualquer novo campo adicionado a `RecursoBasePage` deve ser avaliado contra os dois domínios antes de ser aceito.