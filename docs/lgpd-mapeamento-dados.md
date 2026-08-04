# Mapeamento de Dados Pessoais (LGPD) — Nova PAT

> Atende à exigência do ToR de conformidade total com a LGPD (Lei nº 13.709/2018). Este documento identifica **onde** dado pessoal existe no sistema, **por quê** é coletado, **quem** acessa, e **decisões pendentes** que precisam de definição formal antes do lançamento. Não substitui assessoria jurídica — é o levantamento técnico que uma análise jurídica formal (RIPD/DPIA, se exigido) usaria como insumo.

## Por que este documento existe agora, nesta fase
A arquitetura de dados já está fechada nos `CLAUDE.md` de cada app. Este documento cruza essa arquitetura já decidida com a pergunta "isso é dado pessoal, e se for, está protegido do jeito certo?" — antes da implementação, não depois.

## Inventário de dado pessoal por app

### `usuarios`
| Dado | Sensibilidade | Base legal provável | Observação |
|---|---|---|---|
| `name`, `email` | Pessoal | Execução de contrato/cadastro | Coletado no cadastro público (self-registration). |
| `password` | Pessoal (credencial) | Execução de contrato | Nunca armazenado em texto plano — hash (ver `importador/CLAUDE.md` para migração de hash bcrypt→Django). |
| `role` | Pessoal | Execução de contrato | Não sensível isoladamente, mas define nível de acesso — vazamento revela estrutura de privilégio. |
| `verification_token` | Pessoal (credencial temporária) | Execução de contrato | Token de verificação de e-mail — deve expirar, não ficar retido indefinidamente. |

**⚠️ Idade do usuário não é coletada explicitamente** — nenhum campo de data de nascimento foi encontrado no schema legado. Como a plataforma atende Ensino Fundamental e Médio (confirmado em produção, ver `curriculo/CLAUDE.md`), é provável que **menores de idade se cadastrem diretamente**. A LGPD tem tratamento especial para dado de criança/adolescente (Art. 14) — **decisão pendente, não técnica**: confirmar com quem responde juridicamente pelo projeto se cadastro de estudante deve exigir consentimento de responsável, campo de idade, ou fluxo diferenciado. Não presumir que "não perguntamos idade" resolve o problema — geralmente é o oposto.

### `interacoes`
| Dado | Sensibilidade | Observação |
|---|---|---|
| `Comentario.body` | Pessoal, pode conter dado sensível de terceiro | Usuário pode escrever qualquer coisa em texto livre — moderação (já prevista em `interacoes/CLAUDE.md`) também é controle de proteção de dado, não só qualidade de conteúdo. |
| `Like`, `FavoritoConteudo`, `AvaliacaoConteudo` | Pessoal (comportamental) | Revela preferência/comportamento de uso do usuário — combinado, forma perfil de uso individual. |

### `analytics`
| Dado | Sensibilidade | Observação |
|---|---|---|
| `qt_access`, `qt_downloads` (agregados por conteúdo) | Nível de conteúdo, não de indivíduo | Números agregados, sem problema de exposição — são estatística de conteúdo, não de pessoa. |
| Par usuário↔conteúdo (`Like.user_id`+`conteudo_id`, mesmo padrão em `FavoritoConteudo`/`AvaliacaoConteudo`) | Pessoal (comportamental), mas **necessário para a própria funcionalidade** | Esse cruzamento **precisa existir** no banco — é o que permite, por exemplo, saber se um usuário já curtiu um conteúdo (evitando curtida infinita/duplicada), já modelado via `unique_together` em `interacoes/CLAUDE.md`. Não é um problema de dado existir; é decisão de onde ele pode ser **exposto**. |

**Decisão fechada — "caixa preta" no dashboard de `analytics`**: o par usuário↔conteúdo existe no banco por necessidade funcional, mas **nunca deve ser exposto, consultável ou cruzável no painel administrativo** (nem como filtro, nem como exportação, nem como drill-down a partir de um agregado). O app `analytics` só deve ler e exibir números já agregados por conteúdo ("este conteúdo tem X curtidas, Y favoritos, média Z de avaliação") — nunca uma consulta que responda "quais conteúdos o usuário W curtiu" ou "quais usuários curtiram o conteúdo X". Essa restrição vale mesmo para `super-admin` no painel de relatório — se um cruzamento individual for genuinamente necessário para alguma investigação pontual (ex: moderação de abuso), isso deve passar por acesso direto ao banco/admin de Django com log de acesso, não por uma feature do dashboard de analytics pensada para consulta recorrente.

Atualizar `analytics/CLAUDE.md` com esta restrição explícita quando o dashboard for implementado — hoje o arquivo já diz "não usar como filtro/ordenação" para `media_avaliacao`, mas não formaliza a proibição de drill-down individual; vale reforçar lá também.

### `usuarios` (vínculo) + logs de acesso (não modelado ainda)
Nenhum log de acesso/IP foi mapeado nos `CLAUDE.md` até agora — mas RNF de Segurança do ToR (OWASP, testes de penetração) e a própria noção de "relatório de uso" (RF006) provavelmente vão gerar log com IP/timestamp em algum nível de infraestrutura (servidor web, WAF, etc.), mesmo que não vire model Django. **Isso também é dado pessoal pela LGPD** (IP é considerado dado pessoal). Não documentado ainda — pendência a resolver quando a infraestrutura de deploy for definida.

## Regime específico — a Nova PAT é operada pelo Poder Público, não por empresa privada
A LGPD tem um capítulo próprio para isso: **Capítulo IV (Art. 23 a 32), "Do Tratamento de Dados Pessoais pelo Poder Público"**. Como a Nova PAT é sistema da Secretaria da Educação do Estado da Bahia, esse capítulo se aplica além das regras gerais — não é o mesmo regime de uma empresa privada comum. Pontos que afetam decisão de arquitetura/produto:

- **Finalidade pública obrigatória (Art. 23)**: o tratamento de dado só é legítimo se voltado ao cumprimento de competência legal/execução de política pública — o que já é o caso natural da PAT (plataforma educacional pública), mas vale ter isso documentado como base legal explícita, não presumido.
- **Publicidade do relatório de impacto (Art. 32)**: diferente do setor privado (onde o RIPD/DPIA normalmente só é entregue à ANPD se solicitado), **órgão público deve dar publicidade ao relatório de impacto à proteção de dados**. Se um RIPD formal vier a ser produzido para a Nova PAT, ele provavelmente precisa ser público, não só arquivado internamente — isso muda o nível de cuidado na redação dele.
- **Interação com a Lei de Acesso à Informação (LAI, Lei nº 12.527/2011)**: o tratamento de dado pelo Poder Público precisa equilibrar **transparência** (LAI) com **proteção de dado pessoal** (LGPD) — a LAI tem limite explícito de que não autoriza fornecer dado pessoal de terceiro sem base legal. Isso importa se a Nova PAT algum dia expuser dado agregado publicamente (ex: relatório de uso do RF006) — precisa continuar agregado, nunca virar canal indireto de exposição de dado individual sob pretexto de transparência pública.
- **Compartilhamento de dado entre órgãos públicos (Art. 26/27)**: se a Nova PAT algum dia compartilhar dado de usuário com outro sistema do governo (ex: SSO mencionado no ToR, seção de integrações mandatórias), esse compartilhamento tem regra própria no capítulo — não é o mesmo regime de compartilhar dado com um parceiro comercial privado.

**Recomendação prática**: como isso é regime jurídico específico de ente público, a leitura completa dos Art. 23-32 (não só o resumo acima) deveria ser feita por quem responde juridicamente pelo contrato — este documento é o levantamento técnico, não substitui essa leitura formal.

## Direitos do titular — o que falta implementar
A LGPD garante ao titular direito de acesso, correção, exclusão e portabilidade dos próprios dados. Nenhum dos `CLAUDE.md` de app até agora prevê:
- **Resolvido**: exportação de dado pessoal do próprio usuário — botão no perfil que gera o download dos dados do usuário (perfil, comentários, avaliações, favoritos). Formato exato (JSON, PDF legível) e escopo exato do que entra no export ficam para quando a implementação for desenhada, mas o mecanismo em si (self-service, não pedido manual por e-mail) está decidido.
- **Parcialmente resolvido, com uma exceção a confirmar**: fluxo de exclusão de conta com efeito real nos dados relacionados. Para `Like`, `FavoritoConteudo`, `AvaliacaoConteudo`: mantém a decisão de **apagar** (não anonimizar) ao excluir a conta — são métricas de engajamento puras, sem valor de conteúdo próprio, e anonimizar manteria a linha existindo, abrindo brecha para exploit de conta descartável inflando engajamento sem risco de reversão real.

  **`Comentario` é diferente e levanta um ponto válido**: comentário carrega conteúdo substantivo (texto), não é só sinal de engajamento — apagar duro pode quebrar contexto de moderação (histórico do que foi publicado e por quem, útil se houver denúncia/investigação posterior) e, se no futuro houver resposta a comentário, apagar duro deixaria resposta órfã. **Proposta, pendente de confirmação sua antes de fechar**: anonimizar `Comentario` na exclusão de conta (mantém o texto e a trilha de moderação, remove/desvincula a identidade do autor), em vez de apagar. O risco de exploit que motivou "apagar" nos outros três models não se aplica da mesma forma aqui — não existe ganho relevante em "inflar contagem de comentário" com conta descartável, diferente de curtida/avaliação, que afetam métrica visível (`media_avaliacao`, contagem de like). Confirmar se essa diferenciação faz sentido pra você antes de tratar como fechado.
- Prazo de retenção — quanto tempo um dado de usuário inativo é mantido antes de expurgo. Não definido em nenhum documento até agora.

## Retenção e minimização — não existe TTL único fixado em lei
Pesquisado: a LGPD **não fixa um número de dias/anos universal** para expurgo de dado pessoal de plataforma web. O Art. 40 dá à ANPD poder de regular tempo de guarda, mas não há regulamentação específica publicada pra esse tipo de plataforma até o momento. O princípio que vale é **finalidade**: o dado deve ser mantido só enquanto a razão que justificou a coleta persistir (Art. 15/16 da LGPD, término do tratamento) — não um prazo emprestado de outro setor (ex: trabalhista/fiscal têm prazos próprios que não se aplicam aqui). Isso significa que o prazo certo pra Nova PAT precisa ser **decidido e documentado por finalidade específica**, não copiado de um "padrão de indústria" genérico que não existe de forma vinculante para este caso.

Pontos a decidir, não a inventar:
- `verification_token` (usuários não verificados): **resolvido — expurgo em 1h**. Prazo curto e técnico, coerente com a finalidade (janela de verificação de e-mail).
- Dado de usuário `convidado` cadastrado e nunca verificado/nunca voltou: **resolvido — 3 meses**. Não existe número fixado em lei ou "padrão de indústria" vinculante para isso, mas 3 meses é valor comum e razoável em sistemas de cadastro (a maioria das plataformas que fazem essa limpeza usa uma janela entre 30 e 90 dias para conta nunca ativada) — dentro dessa faixa, é uma escolha defensável. Distinto do prazo de usuário **já ativo** que ficou inativo depois (ver abaixo) — aqui não há relação de uso real estabelecida, então o prazo pode ser mais curto sem perda de legitimidade.
- Usuário ativo que ficou inativo: **proposta de 18 meses, pendente de confirmação do cliente**. Se o cliente não se manifestar, 18 meses é o valor a implementar por padrão.
- **Log de acesso vs. trilha de auditoria — são duas coisas diferentes, com regra diferente**:
  - **Log de acesso bruto** (IP, timestamp de requisição, sem ligação a uma ação específica de mudança de dado): esse sim tem janela de retenção limitada, porque a finalidade (segurança operacional, detectar abuso) se esgota depois de um tempo — normalmente semanas a poucos meses é suficiente para esse propósito.
  - **Trilha de auditoria de alteração** (quem criou/editou/excluiu um registro — accountability, não monitoramento de acesso): esse é um caso legítimo de **retenção indefinida**. A própria LGPD prevê "responsabilização e prestação de contas" como princípio (Art. 6º, X), e para Poder Público isso pesa ainda mais — auditoria de quem alterou o quê num sistema público é interesse legítimo de longo prazo, diferente de rastrear acesso comum. Boa prática: a trilha deve guardar referência mínima (ex: ID do usuário, não o perfil inteiro) para minimizar exposição de dado pessoal dentro do próprio log de auditoria.

## O que este documento NÃO resolve sozinho
- Não substitui um RIPD/DPIA formal se o órgão contratante exigir um processo jurídico formal — este é o levantamento técnico de insumo.
- Não define texto de política de privacidade/termo de uso — isso é conteúdo jurídico, não arquitetura de dado.
- Não resolve a pendência de consentimento de menor sozinho — precisa de decisão de quem responde legalmente pelo projeto.

## O que ainda falta definir (atualizado)
Depois desta rodada, a maior parte das pendências técnicas de retenção/exclusão está fechada. O que resta:

1. **Consentimento de menor de idade** — maior pendência, não é técnica, precisa de decisão jurídica (ver seção acima sobre ausência de campo de idade no cadastro).
2. **Confirmação do cliente sobre 18 meses** de retenção de usuário inativo — se não vier resposta, implementar 18 meses por padrão, conforme decidido.
3. **Confirmação sua sobre anonimizar `Comentario`** em vez de apagar na exclusão de conta (ver seção de exclusão acima).
4. **Encarregado (DPO) designado** — achado novo: o Art. 23, III da LGPD exige que pessoa jurídica de direito público **indique um encarregado pelo tratamento de dados**. Isso não é decisão de arquitetura de software, é decisão organizacional de quem, na Secretaria da Educação, assume esse papel — mas o sistema pode precisar expor um canal de contato do encarregado (ex: e-mail visível na política de privacidade). Verificar se esse papel já existe formalmente antes do lançamento.
5. **Procedimento de notificação de incidente de segurança** (Art. 48 — comunicação à ANPD e ao titular em caso de vazamento) — não documentado em lugar nenhum ainda. É mais próximo do runbook de segurança/BDR do que deste documento, mas precisa existir em algum lugar antes do lançamento.
6. **Compartilhamento com terceiro privado** — se a integração com YouTube/Spotify (mencionada no ToR) envolver enviar dado de usuário (não só embed de player), isso é compartilhamento de dado com processador privado e tem regra própria (Art. 26/27) — checar se a integração planejada envia algum dado de usuário ou é só embed de conteúdo público.

## Status
🟡 Levantamento avançado. Pendências remanescentes têm dono definido (cliente, você, ou "verificar se existe" institucional) — não são mais lacunas em aberto sem direção.
