# Matriz de Permissões (RBAC) — Nova PAT

> Consolida em um único lugar as regras de autorização que hoje estão espalhadas em `usuarios/CLAUDE.md`, `conteudos/CLAUDE.md`, `aplicativos/CLAUDE.md` e `interacoes/CLAUDE.md`. Serve tanto de referência técnica quanto de material de treinamento para administradores/curadores (entregável exigido no ToR). Se um `CLAUDE.md` de app e esta matriz divergirem no futuro, o `CLAUDE.md` do app é a fonte de verdade viva — atualizar esta matriz junto.

## Papéis (5, confirmados no legado)

| Papel | Descrição |
|---|---|
| `super-admin` | Irrestrito, incluindo ações destrutivas permanentes. |
| `admin` | Quase irrestrito, abaixo de super-admin em ações destrutivas (forceDelete, restore). |
| `coordenador` | Curadoria de conteúdo/aplicativo — cria, edita, aprova. Não mexe em taxonomia estrutural. |
| `editor` | Papel legado sem permissão ativa implementada (busca exaustiva no código não achou nenhuma Policy que o cite). Preservado por compatibilidade de dado (ver `usuarios/CLAUDE.md`) — não recriar propósito por padrão na NOVA PAT sem decisão de produto nova. |
| `convidado` | Papel padrão de cadastro público. Usuário comum, sem privilégio de curadoria. |

## Matriz

| Ação | super-admin | admin | coordenador | editor | convidado |
|---|---|---|---|---|---|
| Criar conteúdo (`ConteudoPage`) | ✅ | ✅ | ✅ | ❌* | ❌ |
| Editar/aprovar conteúdo | ✅ | ✅ | ✅ | ❌* | ❌ |
| Apagar conteúdo (soft delete) | ✅ | ✅ | ✅ (próprio) | ❌* | ❌ |
| Apagar conteúdo permanentemente | ✅ | ❌ | ❌ | ❌ | ❌ |
| Criar/editar aplicativo educacional | ✅ | ✅ | ✅ | ❌* | ❌ |
| Gerenciar `Tipo`, `Licenca`, `Categoria`, `NivelEnsino` (taxonomia estrutural de conteúdo) | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerenciar `AplicativoCategoria` | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerenciar `Canal` | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerenciar tags | ✅ | ✅ | ✅ | ❌* | ❌ |
| Comentar (login obrigatório) | ✅ | ✅ | ✅ | ✅* | ✅ |
| Ter comentário publicado sem espera | ✅ | ✅ | ✅ | ❌* | ❌ (entra pendente) |
| Curtir (`Like`) | ✅ | ✅ | ✅ | ✅* | ✅ |
| Favoritar (`FavoritoConteudo`) | ✅ | ✅ | ✅ | ✅* | ✅ |
| Avaliar (`AvaliacaoConteudo`, nota 1–5) | ✅ | ✅ | ✅ | ✅* | ✅ |
| Gerenciar usuários de terceiros (listar/criar/editar/deletar) | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerenciar papéis (`Role`) — criar/editar/deletar | ✅ | ❌ | ❌ | ❌ | ❌ |
| Criar formulário de contato | ✅ | ✅ | ✅ | ✅ | ✅ (inclusive anônimo) |
| Criar playlist curada (admin) | ✅ | ✅ | ❌ (não confirmado) | ❌ | ❌ |
| Criar playlist pessoal (própria, construção nova) | ✅ | ✅ | ✅ | ✅ | ✅ (qualquer logado) |

`*` = comportamento de `editor` nestas linhas é **assumido igual a `convidado`** por não ter permissão diferenciada confirmada no legado — não é achado confirmado, é o valor padrão mais seguro até decisão em contrário.

## Regras que não são só "sim/não" — cuidado ao consultar esta tabela isoladamente
- **Aprovação de conteúdo não é sobre poder editar, é sobre poder pular a fila.** `coordenador` pra cima publica direto; abaixo disso, no legado, nem chega a criar (RN-L1 em `conteudos/CLAUDE.md`).
- **Playlist pessoal e Favorito/Avaliação/Like são construção nova** — não têm regra de autorização herdada do legado, a tabela reflete decisão já tomada (qualquer usuário logado), não comportamento confirmado em produção.
- **`user_canal`** (vínculo de usuário a canal específico) pode restringir ainda mais o escopo de um `coordenador` (só canais vinculados) — **não está refletido nesta matriz** porque a semântica exata não foi confirmada (ver `usuarios/CLAUDE.md`). Se confirmado, esta matriz precisa de uma coluna extra de "escopo por canal".

## Quando atualizar este documento
Toda vez que uma Policy nova for implementada (Wagtail permission ou lógica de role customizada), atualizar a linha correspondente aqui com o comportamento real implementado — não deixar esta matriz descrever intenção enquanto o código faz outra coisa.

## Status
🟡 Em andamento — estrutura e conteúdo principal fechados. Pendente: confirmar semântica de `user_canal` e comportamento real de `editor` (ambos dependem de acesso a produção ou decisão de negócio, não de leitura de código).
