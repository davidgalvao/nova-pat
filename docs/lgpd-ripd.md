# Relatório de Impacto à Proteção de Dados Pessoais (RIPD/DPIA) — Nova PAT

> Relatório de impacto à proteção de dados pessoais da Nova PAT, elaborado antes da entrada em produção, conforme recomendação do jurídico (ver `docs/lgpd-mapeamento-dados.md`, item 11). Aplica o regime do Poder Público da LGPD (Capítulo IV, Art. 23 a 32). Em razão do Art. 32 da LGPD, órgão público deve dar publicidade ao relatório de impacto: este documento está estruturado para ter uma **versão pública** distinta da **versão técnica integral**, caso contenha informações sensíveis de segurança.

## 1. Identificação

| Campo | Informação |
|---|---|
| Nome do sistema | Nova PAT — Plataforma de Ambiente de Aprendizagem (educacional) da Secretaria da Educação do Estado da Bahia |
| Controladora | Secretaria da Educação do Estado da Bahia |
| Operadora de infraestrutura | PRODEB / provedor de hosting a definir (não assume responsabilidade de controladora) |
| Encarregado (DPO) | A ser designado pela SEC (item 5 de `docs/lgpd-mapeamento-dados.md`) |
| Elaborado por | Equipe técnica da Nova PAT (levantamento técnico; não substitui parecer jurídico formal) |
| Versão | 1.0 |
| Data | [preencher com a data de elaboração] |
| Status | Versão 1.0 — pré-produção |

## 2. Fundamentação legal e regime aplicável

- **LGPD, Capítulo IV (Art. 23 a 32)**: tratamento de dados pessoais pelo Poder Público. A Nova PAT trata dados pessoais para execução de política pública educacional e cumprimento de competência legal da Secretaria da Educação (Art. 23). Não se trata de tratamento por consentimento genérico; a base legal provável é o Art. 7º, II e III (cumprimento de obrigação legal/execução de política pública), combinado com o Art. 23.
- **Art. 32 da LGPD**: publicidade do relatório de impacto para órgãos públicos — diferente do setor privado, o RIPD deve ser dado publicidade (versão pública), não apenas arquivado internamente.
- **LAI (Lei nº 12.527/2011)**: transparência equilibrada com a vedação de fornecer dado pessoal de terceiro sem base legal.

## 3. Descrição do tratamento de dados pessoais

Os dados pessoais tratados pela Nova PAT estão inventariados em `docs/lgpd-mapeamento-dados.md` (seção "Inventário de dado pessoal por app"):

| App | Dados pessoais | Sensibilidade | Base legal provável |
|---|---|---|---|
| `usuarios` | name, email, password (hash), role, verification_token | Pessoal / credencial | Art. 7º II/III + Art. 23 |
| `interacoes` | Comentario.body (texto livre, pode conter dado sensível de terceiro) | Pessoal, pode conter dado sensível de terceiro | Art. 7º II/III + Art. 23 |
| `interacoes` | Like, FavoritoConteudo, AvaliacaoConteudo | Pessoal (comportamental) | Art. 7º II/III + Art. 23 (necessário à funcionalidade) |
| Infraestrutura | Log de acesso bruto (IP, timestamp) | Pessoal (IP é dado pessoal) | Interesse legítimo / segurança operacional |
| Infraestrutura | Trilha de auditoria (quem criou/editou/excluiu o quê) | Pessoal (mínimo: ID do usuário) | Accountability (Art. 6º X) |

**Finalidades:** cadastro e autenticação de usuários, publicação e consumo de conteúdos educacionais, interações (comentários, avaliações, favoritos), moderação de conteúdo, segurança operacional, prestação de contas do sistema público, relatórios de uso agregados (RF006).

**Necessidade e proporcionalidade:** os dados coletados são o estritamente necessário para as finalidades acima. Não há campo de idade ou data de nascimento no schema legado; a identificação de criança/adolescente, quando implementada, deve aplicar o princípio da necessidade (coletar só o estritamente necessário). O par usuário↔conteúdo existe no banco por necessidade funcional (evitar curtida/avaliação duplicada) e **não deve ser exposto no dashboard de analytics** nem ser consultável/cruzável individualmente, mesmo para super-admin.

**Não há compartilhamento de dados com terceiros:** integrações com YouTube/Spotify são apenas incorporação (embed) de conteúdo externo, via de mão única, sem envio de dados pessoais de usuários da Nova PAT a essas plataformas (não se aplica Art. 26/27).

## 4. Riscos identificados e medidas de mitigação

| Risco | Probabilidade | Severidade | Nível | Medida de mitigação |
|---|---|---|---|---|
| Vazamento de credenciais (senhas, tokens de verificação) | Média | Alta | Alto | Senhas nunca em texto plano (hash bcrypt/Django); tokens de verificação com expiração (1h) e expurgo de não verificados (3 meses); reset de senha e invalidação de sessões em incidente. |
| Acesso não autorizado a dados de usuários | Média | Alta | Alto | Controle de acesso RBAC (`docs/matriz-permissoes-rbac.md`); logs de acesso e trilha de auditoria; revisão periódica de privilégios. |
| Exposição individual de comportamento de usuário (par usuário↔conteúdo) | Baixa | Média | Médio | Proibição explícita de drill-down individual no dashboard de analytics; apenas agregados por conteúdo. |
| Comentário contendo dado sensível de terceiro | Média | Média | Médio | Moderação de conteúdo (prevista em `interacoes/ARCHITECTURE.md`); anonimização (não exclusão) do Comentario na exclusão da conta. |
| Retenção excessiva de dados de usuários inativos | Média | Média | Médio | Prazo de retenção definido por finalidade (18 meses proposto para usuário ativo inativo, pendente confirmação da SEC; 3 meses para nunca verificado; 1h para verification_token). |
| Incidente de segurança com dados pessoais | Média | Alta | Alto | Procedimento de resposta a incidente (`docs/lgpd-procedimento-incidente.md`) com comunicação à ANPD/titulares em até 3 dias úteis (Resolução CD/ANPD nº 15/2024). |
| Perda de dados por desastre/infraestrutura | Média | Alta | Alto | Backup diário do Postgres e mídia, procedimento de restauração (`docs/runbook-backup-dr.md`); RTO/RPO a definir com o cliente. |

## 5. Direitos do titular

A Nova PAT garante, por meio de mecanismos self-service (a serem implementados), os direitos LGPD de acesso, correção, exclusão e portabilidade dos dados pessoais:

- **Exportação de dados pessoais:** botão no perfil que gera download dos dados do usuário (perfil, comentários, avaliações, favoritos) — mecanismo decidido; formato exato a ser definido com a SEC (item 7 do mapeamento LGPD).
- **Exclusão de conta:** `Like`, `FavoritoConteudo` e `AvaliacaoConteudo` são apagados (não anonimizados); `Comentario` é anonimizado (mantém o texto e trilha de moderação, remove a identidade do autor), para não quebrar contexto de moderação e evitar respostas órfãs.
- **Retenção:** definida por finalidade específica, sem TTL único fixado em lei (ver seção 4 e `docs/runbook-backup-dr.md`).

## 6. Crianças e adolescentes

A plataforma atende menores de idade (contexto educacional da rede pública). Não há consentimento parental geral; base legal aplicável é Art. 7º II/III combinado com Art. 23 (resposta do jurídico, item 1 do mapeamento LGPD). Quando a lógica de identificação de menor for implementada, deve aplicar o princípio da necessidade — coletar só o estritamente necessário, sem campo ou dado supérfluo.

## 7. Plano de resposta a incidentes

O procedimento formal de resposta a incidente de segurança está documentado em `docs/lgpd-procedimento-incidente.md`, cobrindo detecção, registro, contenção, avaliação de risco, comunicação interna, acionamento do Encarregado e comunicação à ANPD e aos titulares em até 3 dias úteis (Resolução CD/ANPD nº 15/2024). A responsabilidade por notificação é da Secretaria (controladora); a PRODEB não assume automaticamente.

## 8. Publicidade do RIPD (Art. 32 da LGPD)

Como a Nova PAT é operada pelo Poder Público, este RIPD deve ser público, não apenas arquivado internamente. Recomenda-se:

- **Versão técnica integral:** este documento completo, contendo inventário detalhado, riscos e medidas de mitigação. Pode conter informações sensíveis de segurança (detalhes de contenção, logs, infraestrutura) — destinada ao Encarregado, à Secretaria e à ANPD, se solicitado.
- **Versão pública:** versão resumida deste relatório, adequada à publicação, contendo finalidade do tratamento, categorias de dados, bases legais, direitos do titular, medidas gerais de segurança e como contatar o Encarregado. **Não deve incluir** detalhes operacionais de segurança que possam facilitar ataques, nem dados pessoais de terceiros, respeitando a LAI.

A versão pública é publicada nos canais oficiais da Secretaria/Nova PAT; a versão técnica integral fica arquivada internamente.

## 9. Documentos relacionados

- `docs/lgpd-mapeamento-dados.md` — inventário de dados pessoais, bases legais, decisões fechadas/redirecionadas/abertas.
- `docs/lgpd-procedimento-incidente.md` — procedimento de resposta a incidente (item 10 do mapeamento LGPD).
- `docs/runbook-backup-dr.md` — backup, retenção de logs (~90 dias acesso bruto; indefinida auditoria) e recuperação de desastres.
- `docs/matriz-permissoes-rbac.md` — controle de acesso.

## 10. Responsável e revisão

Este relatório é um levantamento técnico de insumo e não substitui parecer jurídico formal da Secretaria. Deve ser revisado:
- antes da entrada em produção;
- sempre que houver mudança significativa nos dados tratados, nas finalidades ou na infraestrutura;
- periodicamente (frequência a definir com a SEC).

Responsável pela revisão: Encarregado (DPO) designado pela SEC, com a equipe técnica da Nova PAT.
