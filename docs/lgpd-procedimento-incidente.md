# Procedimento de Resposta a Incidentes de Segurança da Informação e Proteção de Dados Pessoais — Nova PAT

> Procedimento formal de resposta a incidente de segurança envolvendo dados pessoais, exigido pelo jurídico como pré-requisito antes da entrada em produção (ver `docs/lgpd-mapeamento-dados.md`, item 10). Aplica o regime do Poder Público da LGPD (Capítulo IV, Art. 23 a 32) e a Resolução CD/ANPD nº 15/2024 (comunicação à ANPD e aos titulares em até 3 dias úteis).

## 1. Objetivo e escopo

Estabelecer os passos obrigatórios para detectar, registrar, conter, avaliar, comunicar e remedia incidentes de segurança que afetem dados pessoais tratados pela Nova PAT (plataforma educacional da Secretaria da Educação do Estado da Bahia), incluindo vazamento, acesso não autorizado, alteração, perda ou destruição acidental de dados pessoais.

Aplica-se a todos os dados pessoais inventariados em `docs/lgpd-mapeamento-dados.md` (cadastro de usuários, comentários, likes/favoritos/avaliações, logs de acesso bruto e trilha de auditoria) e a qualquer ambiente onde esses dados estejam presentes (desenvolvimento, homologação e produção).

## 2. Regime jurídico aplicável

- **Poder Público (Art. 23 a 32 da LGPD)**: a Nova PAT é sistema da Secretaria da Educação; o tratamento de dados pessoais se funda no cumprimento de competência legal e execução de política pública educacional (Art. 23), não em consentimento genérico.
- **Controladora**: a Secretaria da Educação é a controladora dos dados. A PRODEB (ou provedor de infraestrutura) atua como operadora de infraestrutura e **não assume automaticamente a responsabilidade por notificação de incidente** (ver item 4 do mapeamento LGPD).
- **Comunicação à ANPD e titulares**: prazo de até **3 dias úteis** após a constatação do incidente, conforme Resolução CD/ANPD nº 15/2024.
- **LAI (Lei nº 12.527/2011)**: qualquer comunicação pública do incidente deve equilibrar transparência com a vedação de fornecer dado pessoal de terceiro sem base legal.

## 3. Papéis e responsabilidades

| Papel | Responsabilidade no incidente |
|---|---|
| Equipe técnica da Nova PAT | Detecção, registro, contenção, remediação técnica, preservação de evidências, comunicação interna. |
| Encarregado (DPO) | A ser designado pela SEC (item 5 do mapeamento LGPD). Recebe a comunicação do incidente, avalia a necessidade de notificação à ANPD e aos titulares, e acompanha o atendimento a solicitações de titulares decorrentes do incidente. |
| Secretaria da Educação (controladora) | Decide sobre a comunicação oficial à ANPD, aos titulares e à imprensa, se aplicável; assume a responsabilidade legal pela notificação. |
| PRODEB / provedor de infraestrutura | Fornece logs de infraestrutura (servidor web, WAF) e apoio técnico na contenção e restauração; não substitui a controladora na comunicação à ANPD. |

## 4. Fluxo de resposta ao incidente

### Etapa 1 — Detecção e registro

Quaisquer indício de incidente (alerta de segurança, tentativa de invasão, vazamento de credenciais, e-mail de titular reportando uso indevido, comportamento anômalo no sistema) deve ser reportado imediatamente à equipe técnica.

**Registro obrigatório**: abertura de registro interno do incidente contendo, no mínimo:
- data/hora da detecção e da ocorrência (se diferente);
- quem detectou e como;
- descrição resumida do ocorrido;
- sistemas e dados pessoais possivelmente afetados;
- gravidade inicial (baixa, média, alta, crítica).

O registro deve ser mantido mesmo que o incidente se revele, após avaliação, como não envolvendo dados pessoais.

### Etapa 2 — Contenção

Ações imediatas para limitar a propagação e o dano:
- isolar contas, credenciais ou sistemas comprometidos (ex: invalidação de sessões, reset de senhas, revogação de tokens de verificação e de API);
- bloquear acessos de origem suspeita no nível de infraestrutura (servidor web/WAF), quando possível;
- preservar logs e evidências (cópia dos logs de acesso bruto, de auditoria e de aplicação) antes de qualquer limpeza ou reinstalação — os logs de acesso bruto têm retenção proposta de ~90 dias (`docs/runbook-backup-dr.md`); a trilha de auditoria tem retenção indefinida e nunca deve ser apagada por rotina automática.

A contenção não deve destruir evidências necessárias para a avaliação de risco e para eventuais apurações.

### Etapa 3 — Avaliação de risco

A equipe técnica, com o Encarregado quando designado, avalia:
- quais dados pessoais foram afetados e quantos titulares estão envolvidos;
- se há dados de crianças/adolescentes (presença confirmada no escopo da Nova PAT);
- natureza e sensibilidade dos dados (dado de identificação, credencial, comportamento de uso, dado sensível de terceiro em comentários);
- probabilidade e severidade dos efeitos adversos aos titulares (discriminação, fraude, dano à reputação, perdas financeiras, exposição de estrutura de privilégio via roles, etc.);
- se o incidente apresenta **risco para os direitos e liberdades dos titulares**.

Classificar o risco como baixo, médio, alto ou crítico, fundamentando a classificação por escrito no registro do incidente.

### Etapa 4 — Comunicação interna

A equipe técnica comunica o incidente, o quanto antes, ao Encarregado (ou à Secretaria, se o Encarregado ainda não estiver designado) e à gestão do projeto, com:
- resumo do ocorrido e data/hora da ocorrência;
- dados pessoais afetados e quantidade estimada de titulares;
- classificação de risco e medidas de contenção já tomadas;
- previsão de remediação.

### Etapa 5 — Acionamento do Encarregado (DPO)

O Encarregado:
- confirma ou atualiza a classificação de risco;
- decide, com a Secretaria (controladora), se há obrigação de comunicar à ANPD e aos titulares (incidentes que apresentem risco ou risco elevado);
- orienta o conteúdo e o canal das comunicações, respeitando o prazo de 3 dias úteis da Resolução CD/ANPD nº 15/2024;
- acompanha solicitações dos titulares (acesso, correção, exclusão, portabilidade) decorrentes do incidente.

Se o Encarregado ainda não estiver designado (pendente de definição pela SEC — item 5 do mapeamento LGPD), a Secretaria assume temporariamente essas funções.

### Etapa 6 — Comunicação à ANPD e aos titulares

Quando o incidente apresentar risco para os titulares, a Secretaria (controladora) comunica:
- **à ANPD**: em até 3 dias úteis após a constatação, nos termos da Resolução CD/ANPD nº 15/2024, contendo pelo menos descrição do incidente, dados afetados, quantidade de titulares, medidas de contenção e remediação, e ponto de contato;
- **aos titulares afetados**: de forma clara e acessível, informando o ocorrido, os dados envolvidos, os possíveis efeitos, as medidas tomadas e como o titular pode se proteger e contatar o Encarregado.

Comunicações públicas (imprensa, site da Secretaria) devem respeitar a LAI e não expor dados pessoais de terceiros sem base legal.

### Etapa 7 — Remediação e recuperação

- Corrigir a vulnerabilidade ou falha que permitiu o incidente (patch, ajuste de configuração, reforço de controle de acesso, revisão de permissão RBAC — ver `docs/matriz-permissoes-rbac.md`).
- Restaurar dados e serviços a partir de backups, se necessário, seguindo `docs/runbook-backup-dr.md` (RTO/RPO ainda a serem formalmente definidos).
- Revalidar acesso de usuários e revisar privilégios comprometidos.

### Etapa 8 — Relatório final e pós-incidente

Encerrado o incidente, produzir relatório final contendo:
- cronograma completo (detecção, contenção, avaliação, comunicações, remediação);
- causa-raiz;
- dados pessoais afetados e titulares impactados;
- medidas tomadas e prazos cumpridos (incluindo o de 3 dias úteis, se aplicável);
- lições aprendidas e ações de melhoria (ex: atualização de controles, treinamento, ajuste de retenção de logs).

O relatório final fica arquivado internamente e é disponibilizado ao Encarregado e à Secretaria.

## 5. Documentos relacionados

- `docs/lgpd-mapeamento-dados.md` — inventário de dados pessoais e bases legais (itens 4, 8, 9, 10).
- `docs/runbook-backup-dr.md` — retenção de log de acesso bruto (~90 dias) e trilha de auditoria (indefinida), procedimento de backup e restauração.
- `docs/matriz-permissoes-rbac.md` — controle de acesso e perfis de usuário.

## 6. Status e revisão

**Status:** documento escrito (conclui o item 10 do mapeamento LGPD). Revisar após a definição do Encarregado pela SEC (item 5), da política de retenção de usuário inativo (item 6) e da infraestrutura de produção. Este documento não substitui assessoria jurídica.
