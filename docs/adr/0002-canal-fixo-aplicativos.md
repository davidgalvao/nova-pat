# ADR-002 — Canal fixo `id=9` para aplicativos

- **Status**: ✅ Aceito
- **Data**: 2026-08-27
- **Decisões relacionadas**: D4 (fechamento de pendência conceitual)

## Contexto

No legado (Laravel), `Aplicativo::CANAL_ID = 9` fixa o canal de todo aplicativo educacional por constante no código — o canal não é escolha do usuário no formulário. O código atual de `AplicativoEducacionalPage.save()` força `canal_id=9`, com fallback por slug `aplicativos-educacionais` caso o id não exista.

O valor `9` aparece como **número mágico inline** no `save()`, sem constante nomeada, e a dependência de o canal `id=9` existir em produção ainda não foi confirmada no admin.

## Decisão

**Manter o canal fixo**, mas **extrair o valor para uma constante nomeada** `CANAL_ID = 9` (em `aplicativos/models.py` ou `aplicativos/constants.py`), eliminando o número mágico inline. O fallback por slug é mantido como contingência de ambiente, documentado como tal.

**Pendência de confirmação**: validar no admin de produção que o canal `id=9` é de fato "Aplicativos Educacionais" antes de fechar a constante como definitiva. Se o id real diferir, apenas a constante muda.

## Consequências

**Positivas:**
- Remove o número mágico; a intenção fica explícita e centralizada.
- Facilita ajuste futuro (mudar o id em um único lugar).

**Negativas / riscos:**
- A dependência de o canal `id=9` existir permanece — se o canal for recriado com outro id, a constante precisa ser atualizada.
- O fallback por slug adiciona uma segunda fonte de verdade (id vs. slug) que pode divergir.

**Mitigação:**
- Confirmar o id real em produção antes de produção.
- Documentar a constante e o fallback no `aplicativos/CLAUDE.md`.