# ADR-003 — Busca "ambos" combina por IDs, não `union()`

- **Status**: ✅ Aceito
- **Data**: 2026-08-27
- **Decisões relacionadas**: D6 (fechamento de pendência conceitual)

## Contexto

A busca avançada (`search/views.py`) suporta três modos: `conteudo`, `aplicativo` e `ambos`. No modo `ambos`, os resultados de `ConteudoPage` e `AplicativoEducacionalPage` são combinados via `values_list('id', flat=True)` + `filter(id__in=...)` sobre `Page.objects.live().specific()`.

Essa abordagem tem duas limitações conhecidas:
1. **Perde a ordenação por relevância** do Wagtail search (a ordenação por relevância é descartada quando os IDs são recombinados).
2. **Potencial custo de query** com acervo grande (20.000+ conteúdos), embora a paginação de 12 itens limite o custo real.

A alternativa seria usar `union()` nativo do Django, mas os dois models têm campos diferentes, o que complica o `union()` e exigiria projeção de campos comuns.

## Decisão

**Manter a combinação por IDs** na fase atual, documentando a limitação. A ordenação por relevância é sacrificada no modo `ambos` em favor de simplicidade e de evitar `union()` entre models com campos distintos.

**Reavaliação futura**: se a performance ou a relevância se tornarem problema real (ex: reclamação de produto sobre ordenação, ou lentidão medida), reavaliar com `union()` de campos comuns ou busca separada por aba (conteúdo/aplicativo).

## Consequências

**Positivas:**
- Implementação simples e correta, sem dependência de campos comuns entre os models.
- Paginação de 12 itens já limita o custo de query.

**Negativas / riscos:**
- Ordenação por relevância perdida no modo `ambos`.
- Potencial custo de query com acervo muito grande.

**Mitigação:**
- Documentar a limitação no `search/views.py` e no `search/ARCHITECTURE.md`.
- Monitorar performance; reavaliar com `union()`/abas se necessário.