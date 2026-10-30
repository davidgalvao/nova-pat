# Product Context — Nova PAT

- **O que o sistema resolve:** plataforma educacional pública de curadoria editorial — consumo de conteúdos por canal, busca avançada multicritério e gestão de aplicativos, conteúdos e interações.
- **Taxonomia pedagógica (`tipo`: Animação, Vídeo, Jogo...) ≠ formato técnico (`mecanismo_exibicao`: video, audio, documento_pdf, apresentacao, download_binario, link_externo, animacao_externa). O player/view é escolhido por `mecanismo_exibicao` via `get_template()`, nunca pelo slug de `tipo`.
- **Canal obrigatório** em todo `ConteudoPage` e `AplicativoEducacionalPage` (FK `PROTECT`, sem `null`). Exceção deliberada: `Serie` (canal opcional, `SET_NULL`).
- **RBAC:** 5 papéis (super-admin, admin, coordenador, editor, convidado). Criação de conteúdo restrita a coordenador ou acima (RN-L1); `editor` sem permissão de curadoria na fase atual (D2); `user_canal` é informativo, sem efeito de permissão (D1).
- **Aprovação por role explícita** (ADR-004), não workflow builtin do Wagtail.
- `ConteudoPage` e `AplicativoEducacionalPage` são models separados (`RecursoBasePage` compartilhado); não fundir.
- `Favorito`, `Like` e `Avaliacao` são três entidades distintas (app `interacoes`); avaliação (1-5) é só exibição, nunca filtro ou ordenação de busca.
