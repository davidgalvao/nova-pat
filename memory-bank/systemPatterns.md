# System Patterns — Nova PAT

- **Apps:** core (abstrações compartilhadas), home, search, conteudos, canais, curriculo, series, aplicativos, interacoes, usuarios, analytics, importador; mysite é o pacote de configuração (settings, urls, templates globais).
- **Hierarquia de páginas:** `BasePage` (SEO/Open Graph) → `RecursoBasePage` (canal, autor, tags) → `ConteudoPage` e `AplicativoEducacionalPage` (ADR-001; este sobrescreve `canal`).
- **StreamField:** blocos em `core/blocks.py` agregados em `HomeStreamBlock`, reutilizados por `HomePage.body` e `CanalPage.body`; `ConteudoPage` não usa StreamField para o player.
- **Conteúdo:** um `tipo` + um `mecanismo_exibicao`; `get_template()` escolhe `conteudo_page_<mecanismo>.html` com fallback `conteudo_page.html`.
- **Séries (RF008):** `Serie → Temporada → ConteudoPage` (episódio é `ConteudoPage`, não model separado); `Serie` independente de canal.
- **Navegação:** `NavigationItem` snippet com `parent` auto-referencial; renderização recursiva em `mysite/templates/components/nav_item.html` (Tailwind, WCAG AA hover/foco).
- **Fluxo de trabalho:** worktrees em `.worktrees/` para cards paralelos (subagentes codificam dentro da worktree, nunca na main); commit direto em `main` (projeto solo); nunca `git push`/`reset`/`commit` sem OK do usuário.
