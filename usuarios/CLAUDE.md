# usuarios/ — CLAUDE.md

## Papel deste app
`usuarios` modela autenticação, papéis (roles) e vínculo de usuário com canal. É onde a conformidade LGPD (RN11 do ToR, ver `docs/requisitos-vs-legado.md`) mais concentra trabalho, por lidar com dado pessoal.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`.

## Fase atual: transposição, com atenção a gap de segurança do legado (ver abaixo)

## Papéis reais — 5, não 4 (correção de suposição usada em documentos anteriores desta conversa)
Confirmado em `roles` (migration) + `Users/*.php` (cada subtipo com `role_id` fixo via global scope):

| id | role | nome usado no legado |
|---|---|---|
| 1 | `super-admin` | irrestrito |
| 2 | `admin` | quase irrestrito |
| 3 | `coordenador` | cria/edita/aprova conteúdo e aplicativo |
| 4 | `editor` | **Achado após busca exaustiva no repo**: a string `'editor'` aparece em **apenas dois lugares** em todo o código do legado — o comentário da migration de `roles` (listando o nome) e `Users/EditorUser.php` (o global scope que filtra `role_id = 4`). Nenhuma `Policy`, `Controller`, `Middleware` ou `Request` checa esse papel em lugar nenhum. Ou seja: o papel existe no banco e tem uma classe de conveniência, mas **não tem nenhuma permissão implementada de fato** no comportamento observável do sistema — não libera nada que os outros papéis não liberem por si só, nem é bloqueado especificamente em lugar nenhum (segue as regras padrão, que já excluem `create` de conteúdo/aplicativo por não estar na lista de papéis liberados). Pode ser papel reservado para uso futuro que nunca foi implementado, ou vestígio. Não presumir capacidade nenhuma para `editor` além do que as Policies já listadas concedem a "qualquer papel não citado". Se aparecer necessidade de dar propósito a esse papel na NOVA PAT, é decisão de produto nova, não achado do legado. |
| 5 | `convidado` | **papel padrão de novo cadastro** (`User::USER_DEFAULT_ROLE = 5`). Sem evidência de permissão de criação de conteúdo/aplicativo nas policies revisadas. |

**Não existe papel chamado "professor"** — isso foi terminologia errada usada em versões anteriores desta análise (documentos já corrigidos). Usar sempre os 5 nomes reais acima.

## Model `User` (ou model de usuário do Django/Wagtail estendido)
Campos confirmados no legado:
- `role` — FK para `Role`.
- `name`, `email` (único), `password`.
- `options` (jsonb) — metadados diversos, não detalhado ainda.
- `verified` (boolean) + `verification_token` — fluxo de verificação de e-mail no cadastro.
- Soft delete habilitado.

## Cadastro (self-registration) — aberto ao público
`RegisterAuthRequest`: qualquer pessoa pode se cadastrar sem estar logada (`authorize()` retorna `true` sempre). Validação: `name` obrigatório, `email` único e válido, `password` obrigatória, **mínimo 6 e máximo 15 caracteres**.

**Gap de segurança a resolver na NOVA PAT, não replicar**: mínimo de 6 caracteres e **máximo de 15** é política de senha fraca pelos padrões atuais, e contradiz diretamente o RNF de Segurança do próprio ToR ("política de senhas fortes" — ver `docs/requisitos-vs-legado.md`). Ao implementar cadastro na NOVA PAT: usar validação de senha forte (Django já tem validators padrão de força de senha) e **não replicar o teto de 15 caracteres** — não existe motivo técnico legítimo para limitar o tamanho máximo de senha, isso só reduz o espaço de senhas fortes possíveis. Fidelidade ao legado aqui seria um erro, não uma virtude.

Todo cadastro novo entra como `convidado` (role padrão) — replicar isso.

## Gestão de usuário — restrita
`UserPolicy`: listar, ver, criar, editar, deletar (e restaurar/apagar permanente) usuário de terceiros é ação de `super-admin`/`admin` apenas. Nenhum outro papel gerencia conta de outro usuário.

## Gestão de papel (role) — só super-admin
`RolePolicy`: criar, editar, deletar, listar papéis é ação exclusiva de `super-admin`. Nem `admin` mexe na estrutura de papéis em si (só nos usuários que os têm).

## Vínculo usuário-canal (`user_canal`)
Pivot simples (`user_id`, `canal_id`, chave composta) — liga um usuário a um ou mais canais específicos. **Semântica exata não confirmada**: pode ser "usuário só gerencia conteúdo dos canais a que está vinculado" (escopo de curadoria por canal), mas isso não foi visto em nenhuma Policy revisada até agora (as Policies checadas usam só `role`, não checam `user_canal`). Não presumir a regra — se for implementar essa restrição de escopo, confirmar o comportamento real em produção primeiro (criar um usuário `coordenador` vinculado a um canal só, tentar mexer em conteúdo de outro canal, ver se é bloqueado).

## O que NÃO fazer neste app
- Não usar "professor" como nome de papel — são `super-admin`, `admin`, `coordenador`, `editor`, `convidado`.
- Não presumir que `editor` tem alguma permissão especial — busca exaustiva no código confirma que esse papel não é checado em nenhuma Policy/Controller do legado.
- Não replicar o teto de 15 caracteres na senha — é falha de segurança do legado, não comportamento a preservar.
- Não presumir a semântica de `user_canal` como restrição de escopo sem confirmar em produção.
- Não deixar `admin` gerenciar a estrutura de papéis (`Role`) — só `super-admin` faz isso no legado.