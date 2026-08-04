# Runbook de Backup e Recuperação de Desastres (BDR) — Nova PAT

> Atende à exigência do ToR (RNF de Backup e Recuperação de Desastres: RTO/RPO definidos, testes periódicos, runbook documentado). Como o projeto é conduzido por um único profissional, este documento é também a rede de segurança operacional — precisa ser completo o suficiente para que qualquer pessoa (inclusive alguém sem contexto prévio do projeto) consiga restaurar o sistema seguindo só este documento.

## O que precisa ser decidido antes de este runbook estar completo
Este documento hoje é um **esqueleto com lacunas explícitas** — a infraestrutura de produção (onde o Postgres roda, quem hospeda, se há storage de mídia separado) ainda não foi definida nos `CLAUDE.md` de app. Preencher os `[DEFINIR]` abaixo é pré-requisito para o runbook ser confiável de verdade.

## O que precisa ser salvo em backup

| Item | Onde vive hoje (dev) | Onde vai viver em produção | Crítico? |
|---|---|---|---|
| Banco Postgres (todo o schema: conteúdo, usuário, taxonomia, etc.) | Container `db`, volume `./postgres_data` (ver `docker-compose.yml`) | `[DEFINIR]` | Sim — perda = perda de todo o acervo educacional e cadastro de usuário. |
| Mídia enviada (documento, vídeo, imagem — `wagtaildocs`/`wagtailimages`) | Sistema de arquivo local (dev) | `[DEFINIR — S3-compatível? Disco local com backup próprio?]` | Sim — 20.000+ recursos educacionais, alguns podem não ter cópia em outro lugar. |
| Código-fonte | Git (GitHub) | Git (GitHub) | Já coberto — versionamento é backup de código por natureza, desde que o repositório remoto não seja o único lugar (considerar espelho, já que GitHub também pode falhar). |
| Variáveis de ambiente / segredo (`.env`, chave de API, credencial de banco) | `.env` local, não versionado | `[DEFINIR — gerenciador de segredo? Vault? variável de ambiente do provedor de hosting?]` | Sim, mas de forma diferente — não é "recuperar", é "não perder o único lugar que guarda isso". Se só existir na sua máquina, é ponto único de falha grave. |

## RTO / RPO — ainda não definidos formalmente
O ToR exige que RTO (tempo máximo para restaurar o serviço) e RPO (perda de dado máxima tolerável) sejam definidos com valor concreto ("no máximo X horas"). Isso é decisão de negócio (quanto tempo fora do ar é aceitável, quanto dado perdido é aceitável), não técnica — **não presumir um número, levar a decisão para quem responde pelo contrato/cliente.**

Enquanto não há número formal, a prática mínima recomendada para não deixar isso em branco:
- **RPO informal até definição**: backup diário do Postgres cobre no máximo 24h de perda em caso de desastre. Se o cliente aceitar esse risco, formalizar como RPO = 24h; se não, aumentar frequência (backup incremental mais frequente).
- **RTO informal até definição**: depende inteiramente de onde a infraestrutura de produção roda (ainda `[DEFINIR]`) — sem isso definido, não há como estimar tempo de restauração real.

## Procedimento de backup (a implementar)

### Banco de dados
```bash
# Backup completo (exemplo, ajustar host/credencial quando infra de produção existir)
docker compose exec db pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql
```
- Frequência recomendada: diária, no mínimo, até RPO formal ser definido.
- Backup deve ser copiado para **local diferente** de onde o banco roda — um backup no mesmo disco/servidor não protege contra falha de hardware ou comprometimento daquela máquina.
- `[DEFINIR]`: destino do backup (S3, outro provedor de storage, disco externo com rotação).

### Mídia
- `[DEFINIR]` — depende de onde a mídia vai ser hospedada em produção. Se for S3-compatível, versionamento nativo do bucket pode cobrir boa parte da necessidade; se for disco local, precisa de rotina de sincronização própria (ex: `rsync` para storage externo).

### Segredo/credencial
- Nunca versionar `.env` no Git (já é boa prática assumida, confirmar que `.gitignore` cobre isso).
- `[DEFINIR]` onde a cópia de segurança de credenciais de produção vive.

## Procedimento de restauração (rascunho — testar quando infra existir)

```bash
# Restaurar banco a partir de um dump
docker compose exec -T db psql -U postgres postgres < backup_YYYYMMDD.sql
```

Passos gerais:
1. Provisionar/levantar o ambiente de destino (novo servidor, ou o mesmo após incidente resolvido).
2. Restaurar o dump do Postgres mais recente.
3. Restaurar a mídia a partir do destino de backup definido.
4. Repor variável de ambiente/segredo a partir do gerenciador de segredo definido.
5. Rodar `python manage.py migrate` para garantir que o schema de código bate com o schema restaurado (proteção contra dessincronia entre versão de código e versão de dado no ponto do backup).
6. Validar manualmente: login de usuário administrador funciona, conteúdo abre, upload/player funciona.

## Teste de restauração — obrigação do ToR, ainda não agendado
O ToR exige "testes de recuperação periódicos (simulações de desastre)". Isso não pode ficar só no papel — **agendar pelo menos um teste de restauração completo, em ambiente separado de produção, antes do lançamento**, e depois periodicamente (frequência a definir, trimestral é ponto de partida razoável para um projeto deste porte). Um backup nunca testado é um backup de confiabilidade desconhecida.

## O que este documento NÃO resolve sozinho
- Não define provedor de hosting/infraestrutura — decisão de projeto ainda em aberto.
- Não define RTO/RPO com número formal — decisão de negócio pendente.
- Não substitui teste de restauração real — só o teste real valida que o procedimento funciona de verdade.

## Status
🔴 Esqueleto inicial. Múltiplos `[DEFINIR]` dependem da decisão de infraestrutura de produção, que ainda não foi tomada em nenhum `CLAUDE.md` existente — revisar este documento assim que essa decisão for fechada.
