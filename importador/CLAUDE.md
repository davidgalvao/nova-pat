# importador/ — CLAUDE.md

## Papel deste app
`importador` migra dado do Postgres do sistema legado (Laravel) pro schema novo (Django/Wagtail). É **isolado e descartável** — depois que a migração de produção rodar com sucesso e for validada, este app pode sair do `INSTALLED_APPS` e do repositório. Nenhum outro app deve depender de nada daqui.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`, e o `CLAUDE.md` de cada app de destino (`core`, `canais`, `conteudos`, `series`, `curriculo`, `interacoes`, `aplicativos`, `usuarios`, `analytics`).

## Pré-requisito antes de rodar isto de verdade
Todos os 9 apps de destino precisam estar com os models finais migrados (`makemigrations`/`migrate` aplicados) antes de importar dado real — este app não é hora de descobrir schema, é hora de preencher schema já decidido.

## Estrutura recomendada
Não modelar como app com models próprios expostos — usar **management commands** (`python manage.py importar_x`), um por entidade/grupo, idempotentes (seguro rodar de novo sem duplicar). Conexão com o Postgres legado via uma segunda entrada em `DATABASES` (ex: alias `legado`, **somente leitura**), não via ORM do Laravel.

## Ordem de execução — dependência importa
A ordem abaixo respeita FK: nada pode ser criado antes do que ele referencia.

1. **`usuarios`**: `roles` → `users` (independentes entre si, mas antes de tudo que referencia autor/aprovador).
2. **`curriculo`**: `niveis_ensino`, `curricular_components_categories`, `curricular_components` (independentes).
3. **`canais`**: `canais` → `CanalPage` (raiz da árvore Wagtail — precisa existir antes de qualquer conteúdo/aplicativo).
4. **Taxonomias de `conteudos`**: `tipos`, `licenses`, `categories` (esta última depende de `canal` já migrado, é escopada por canal).
5. **Taxonomia de `aplicativos`**: `aplicativo_categories` — **confirmar durante implementação** se também é escopada por canal como `categories`, isso não foi verificado com certeza no schema legado.
6. **`conteudos`**: `conteudos` → `ConteudoPage`, filha do `CanalPage` correspondente. Nesta etapa também popular M2M: `conteudo_tag` → tags, `conteudo_curricular_component` → componentes curriculares.
7. **`aplicativos`**: `aplicativos` → `AplicativoEducacionalPage`. Canal sempre o mesmo (fixo por constante no legado, `CANAL_ID=9` — **confirmar no admin de produção qual canal real é esse antes de rodar**, ver `canais/CLAUDE.md`). M2M `aplicativo_tag` → tags.
8. **`interacoes`**: `comentarios` → `Comentario` (polimórfico conteúdo/aplicativo, ver decisão de login+aprovação em `interacoes/CLAUDE.md` — dado histórico migrado não precisa passar pela regra de aprovação nova, só marcar `is_approved=True` para tudo que já era público antes). `conteudos_likes` → `Like`, migrando **só como like simples** (decisão fechada): migrar apenas as linhas onde o registro representa "curtiu" de fato; se o campo `like` (boolean nullable) do legado tiver valor `false` ou `null`, **não criar linha** (existência da linha já significa curtida, não precisa do booleano).
9. **Playlist**: extrair de `documents` as linhas que seguem o padrão de playlist (legado não tem coluna discriminadora — usar a convenção observada, ex: prefixo `pl-` no `name`, ver `docs/requisitos-vs-legado.md`). Reconstruir a lista de conteúdos do array jsonb `document.ids` como M2M real (through-model com campo de ordem, replicando a ordem original do array) — **não copiar o padrão jsonb do legado pro novo schema**.
10. **`Document` genérico** (linhas de `documents` que não são playlist): confirmar com o cliente se ainda estão em uso antes de migrar — pode ser dado morto.
11. **`Options`**: migrar para o padrão nativo do Wagtail (`BaseSiteSetting`), não como app próprio.
12. **`Contato`**: baixa prioridade — avaliar se migra como histórico somente-leitura ou se começa vazio na NOVA PAT.
13. **`series` (Serie/Temporada)**: **nada a migrar automaticamente** — é entidade nova sem fonte no legado. Ficam vazias após a importação; organização de conteúdo existente em série é trabalho manual de curadoria posterior, fora do escopo deste ETL.
14. **`FavoritoConteudo`, `AvaliacaoConteudo`**: nada a migrar — são novas, sem fonte no legado, começam vazias.

## Migração de senha — compatibilidade Laravel → Django
Laravel usa bcrypt (hash geralmente com prefixo `$2y$`). Django, por padrão, usa PBKDF2, mas tem um hasher nativo pra isso — `django.contrib.auth.hashers.BCryptSHA256PasswordHasher`. Adicionar esse hasher em `PASSWORD_HASHERS` (não como único, mas na lista, geralmente no fim como fallback de verificação) permite que a senha migrada continue funcionando sem forçar reset de senha de todo mundo. Django re-hasheia automaticamente pro hasher padrão no próximo login bem-sucedido — comportamento nativo, não precisa de lógica extra.

## Atenção: validação de model é para dado NOVO, não para migração
As regras de `conteudos` (RN-L5: mínimo 3 tags, mínimo 1 componente curricular, descrição 100–5012 caracteres) e outras validações formais valem para **criação/edição via formulário/API dali em diante** — não para o dado histórico migrado. É esperado que registros antigos violem esses mínimos (ex: conteúdo legado com só 1 tag). **Migração deve usar `save()`/`bulk_create()` direto, sem passar por `full_clean()`/validação de formulário**, para não rejeitar dado histórico legítimo só porque não atende a um padrão que só passou a valer depois.

## O que NÃO fazer neste app
- Não deixar nenhum outro app importar model daqui — é rua de mão única e descartável.
- Não rodar a importação de `conteudos`/`aplicativos` antes de `canais` existir — quebra FK de página pai no Wagtail.
- Não aplicar as regras de validação de formulário (RN-L5 e afins) durante a migração — são regras pra dado novo, não pra dado histórico.
- Não copiar o padrão de playlist como array jsonb — reconstruir como M2M real.
- Não presumir que `aplicativo_categories` é escopada por canal sem confirmar — verificar antes de escrever o command 5.
- Não forçar reset de senha de todo usuário migrado — usar o hasher de compatibilidade bcrypt.