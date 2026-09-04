# Plano: Atualizar/Criar Arquivos de Arquitetura dos Apps

## Objetivo

Renomear os arquivos de arquitetura de `ARCHITECTURE.md` para `ARCHITECTURE.md` (padrão da indústria) e garantir que todos os apps Django tenham um arquivo de arquitetura **atualizado** e **fiel ao código real**.

## Padrão de nomenclatura

- Nome do arquivo: **`ARCHITECTURE.md`** (substitui `ARCHITECTURE.md`).
- Localização: na raiz de cada app (ex: `conteudos/ARCHITECTURE.md`).
- Conteúdo mínimo esperado por arquivo:
  1. **Papel do app** (responsabilidade no domínio).
  2. **Models** (lista com campos e relações reais, extraídos do `models.py`).
  3. **Regras de negócio / decisões fechadas** (RNs, ADRs).
  4. **Dependências entre apps** (direção das FKs/M2M).
  5. **O que NÃO fazer neste app** (guardrails).

## Inventário dos apps

| App | ARCHITECTURE.md atual | Ação necessária |
|-----|-----------------|-----------------|
| `core` | existe, desatualizado | renomear + atualizar |
| `home` | **não existe** | criar |
| `search` | **não existe** | criar |
| `conteudos` | existe, desatualizado | renomear + atualizar |
| `canais` | existe, desatualizado | renomear + atualizar |
| `curriculo` | existe, desatualizado | renomear + atualizar |
| `series` | existe, desatualizado | renomear + atualizar |
| `aplicativos` | existe, parcialmente desatualizado | renomear + atualizar |
| `interacoes` | existe, atualizado | renomear (conteúdo ok) |
| `usuarios` | existe, parcialmente desatualizado | renomear + atualizar |
| `importador` | existe, sem código | renomear (conteúdo ok) |
| `analytics` | existe, sem código | renomear (conteúdo ok) |
| `mysite` | **não existe** | criar (config do projeto) |

## Tarefas detalhadas

### 1. Renomear todos os ARCHITECTURE.md existentes para ARCHITECTURE.md

Renomear (git mv) os 10 arquivos:
- `core/ARCHITECTURE.md` → `core/ARCHITECTURE.md`
- `conteudos/ARCHITECTURE.md` → `conteudos/ARCHITECTURE.md`
- `canais/ARCHITECTURE.md` → `canais/ARCHITECTURE.md`
- `curriculo/ARCHITECTURE.md` → `curriculo/ARCHITECTURE.md`
- `series/ARCHITECTURE.md` → `series/ARCHITECTURE.md`
- `aplicativos/ARCHITECTURE.md` → `aplicativos/ARCHITECTURE.md`
- `interacoes/ARCHITECTURE.md` → `interacoes/ARCHITECTURE.md`
- `usuarios/ARCHITECTURE.md` → `usuarios/ARCHITECTURE.md`
- `importador/ARCHITECTURE.md` → `importador/ARCHITECTURE.md`
- `analytics/ARCHITECTURE.md` → `analytics/ARCHITECTURE.md`

### 2. Atualizar referências cruzadas

Os arquivos de arquitetura referenciam uns aos outros por nome (ex: "ver `core/ARCHITECTURE.md`"). Após renomear, atualizar todas as referências internas de `ARCHITECTURE.md` para `ARCHITECTURE.md` dentro dos próprios arquivos de arquitetura.

Também atualizar referências em:
- `CONTEXT.MD` (seção 2 menciona "arquivos `.md` de arquitetura e guardrails").
- `core/blocks.py` (docstring menciona "Segue `core/ARCHITECTURE.md`").
- `core/models.py` (docstring do `FlexLayoutMixin` menciona "Ver `core/ARCHITECTURE.md`").
- Qualquer outro arquivo `.py`/`.md` que cite `ARCHITECTURE.md`.

### 3. Criar arquivos de arquitetura ausentes

#### 3a. `home/ARCHITECTURE.md`
Documentar:
- `HomePage(BasePage)` — página inicial, `root_page` do site.
- `body` = `StreamField(HomeStreamBlock())`, modular, opcional.
- `template = "home/home_page.html"` (fixo, não dinâmico).
- Herda SEO/Open Graph de `BasePage`.
- Dependência: `core.blocks.HomeStreamBlock`, `core.models.BasePage`.
- Guardrails: não sobrescrever `get_template()` (template fixo); não adicionar campos de layout em `BasePage`.

#### 3b. `search/ARCHITECTURE.md`
Documentar:
- `search/views.py` — view `search()` (RF001), inferência de tipo via `resolver_tipo_busca`.
- `search/services.py` — `resolver_tipo_busca` (Literal `conteudo`/`aplicativo`/`ambos`), `get_selected_filter_values`.
- `search/filters.py` — `SafeModelChoiceFilter`, `BaseSearchFilterSet`, `ConteudoSearchFilterSet`, `AplicativoSearchFilterSet`.
- Decisão ADR-003: modo "ambos" combina por IDs, não `union()`.
- Paginação: 12 por página.
- Guardrails: inferência de tipo NÃO depende de lookup de ID; não usar `media_avaliacao` em filtro/ordenação.

#### 3c. `mysite/ARCHITECTURE.md`
Documentar:
- Configuração do projeto Django (settings em `mysite/settings/`: `base.py`, `dev.py`, `production.py`).
- `urls.py`, `wsgi.py`.
- Templates globais: `base.html`, `header.html`, `footer.html`, `404.html`, `500.html`.
- `INSTALLED_APPS` (lista dos 10 apps locais + dependências).
- Guardrails: não adicionar app sem registrar em `INSTALLED_APPS`; usar serviço `web` no Docker.

### 4. Atualizar arquivos de arquitetura desatualizados

#### 4a. `conteudos/ARCHITECTURE.md` (prioridade alta)
Corrigir:
- **Player por mecanismo de exibição, não por `tipo.slug`**: o código usa `mecanismo_exibicao` (campo `CharField` com 7 choices: `video`, `audio`, `documento_pdf`, `apresentacao`, `download_binario`, `link_externo`, `animacao_externa`). `get_template()` escolhe `conteudo_page_<mecanismo>.html`.
- Documentar a distinção **taxonomia pedagógica (`tipo`) vs formato técnico (`mecanismo_exibicao`)** (decisão em `CONTEXT.MD` seção 3).
- Renomear `Categoria` → `CategoriaConteudo` (o model foi renomeado na migration 0002).
- Documentar `mecanismo_exibicao` no `search_fields` (FilterField).
- Manter RN-L1 a RN-L6 (ainda válidas).

#### 4b. `core/ARCHITECTURE.md`
Adicionar:
- `FlexLayoutMixin` (abstrato, decisão D5 fechada — mantido sem uso atual, não aplicar em conteúdo).
- `NavigationItem` (snippet com `position` header/footer, `page` vs `link_url`, `sort_order`).
- Blocos StreamField em `core/blocks.py`: `HeroBlock`, `FullBannerBlock`, `CarrosselCategoriaBlock`, `DestaquesManuaisBlock`, `FeatureGridBlock`, `HomeStreamBlock`.
- `BasePage` (SEO/Open Graph) e `RecursoBasePage` (canal, autor, tags) — já documentados, manter.

#### 4c. `canais/ARCHITECTURE.md`
Adicionar:
- `tipos_permitidos` (M2M para `conteudos.Tipo`) — já implementado, não mais "avaliar".
- `categorias_componente_permitidas` (M2M para `curriculo.CurricularComponentCategory`) — já implementado.
- `token` (campo, oculto em API), `options` (JSONField).
- `parent_page_types = ["wagtailcore.Page"]`, `subpage_types` (ConteudoPage, AplicativoEducacionalPage).

#### 4d. `curriculo/ARCHITECTURE.md`
Adicionar:
- `CurricularComponentCategory.parent` (árvore, já implementado).
- M2M `categorias_componente_permitidas` (resolvida, direção em `canais.CanalPage`).
- `search_fields` dos snippets.

#### 4e. `series/ARCHITECTURE.md`
Adicionar:
- `Serie` sobrescreve `canal` para nullable (`null=True`, `blank=True`, `on_delete=SET_NULL`) — independente de canal.
- `Temporada` com `numero`, `sinopse`, `capa`; `parent_page_types = ["series.Serie"]`, `subpage_types = ["conteudos.ConteudoPage"]`.
- Validação de `numero` único por série no `clean()`.

#### 4f. `aplicativos/ARCHITECTURE.md`
Corrigir:
- Remover texto de "decisão em aberto" sobre herdar `RecursoBasePage` — já resolvido (herda `RecursoBasePage`).
- Documentar `CANAL_ID = 9` e `CANAL_SLUG_FALLBACK` (ADR-002) — já parcialmente documentado, confirmar.
- Documentar validações reais: descrição mín. 140 chars, tags 3–15, URL ativa (DNS/HTTP), imagem jpeg/png/jpg/svg até 1MB.

#### 4g. `usuarios/ARCHITECTURE.md`
Adicionar:
- Soft delete: `deleted_at`, `deleted_by` (FK self).
- `verification_token_created_at` (expiração de token).
- `Role.get_default_role()` e `Role.get_privileged_roles()` (classmethods).
- Override de `groups`/`user_permissions` (related_name `usuarios_user_set`).

### 5. Apps sem código (apenas renomear, conteúdo ok)

- `importador/ARCHITECTURE.md` — renomear, conteúdo já correto (app descartável, management commands).
- `analytics/ARCHITECTURE.md` — renomear, conteúdo já correto (RF006, dashboard admin).

### 6. Verificação final

- Rodar `grep -r "ARCHITECTURE.md" .` para garantir que nenhuma referência antiga permaneceu.
- Confirmar que todos os 13 apps têm `ARCHITECTURE.md`.
- Rodar a suíte de testes (`docker compose exec web pytest`) para garantir que nenhuma docstring/import quebrou.

## Ordem de execução sugerida

1. Renomear os 10 arquivos (git mv).
2. Atualizar referências cruzadas (`ARCHITECTURE.md` → `ARCHITECTURE.md`).
3. Criar os 3 arquivos ausentes (`home`, `search`, `mysite`).
4. Atualizar os 7 arquivos desatualizados (prioridade: `conteudos` primeiro).
5. Verificação final (grep + pytest).