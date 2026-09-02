# CONTEXT.md - Nova PAT (Plataforma Anísio Teixeira)

## 1. Stack Tecnológica e Infraestrutura
* **Backend:** Django 6.0.8, Wagtail 8.0.
* **Front-end:** Tailwind CSS (via CDN), templates semânticos em conformidade com WCAG 2.1 AA.
* **Qualidade e Testes:** Suíte estável com 176 testes automatizados aprovados (`pytest`).
* **Ambiente:** Execução containerizada via Docker / WSL 2.

## 2. Governança e Documentação
* **Arquivos Guardrails:** É obrigatório consultar e atualizar os arquivos `.md` de arquitetura e *guardrails* de cada app do projeto antes de implementar modificações estruturais ou novas funcionalidades.

## 3. Decisão Arquitetural: Taxonomia Pedagógica vs. Formato Técnico
Para corrigir o descasamento herdado do portal legado, a arquitetura distingue rigidamente:
* **Taxonomia Pedagógica (Filtros de Busca e Currículo):** Categorias usadas na navegação e filtragem educacional (ex: *Animação, Apresentação, Sequência Didática, Vídeo, Jogo*).
* **Formato Técnico / Mecanismo de Exibição:** Atributo em `ConteudoPage` responsável por determinar a view de renderização:
  * `video`: Player responsivo 16:9.
  * `audio`: Player de áudio nativo estilizado.
  * `documento_pdf` / `apresentacao`: Visualizador embutido ou download seguro.
  * `download_binario` (.zip, .rar, .exe): Botões dedicados de download com avisos de segurança/tamanho.
  * `link_externo` / `animacao_externa`: iframes protegidos ou links externos (`noopener noreferrer`).

## 4. Gestão Administrativa e Controle de Acesso
* **Modelo:** `NavigationItem` gerenciado via Snippets no painel do Wagtail.
* **Interface:** Registrado por meio de `SnippetViewSet` com o rótulo "Menus" fixado na raiz da barra lateral esquerda do admin.
* **Restrição de Visibilidade:** Acesso restrito exclusivamente a superusuários (`is_superuser`) ou a membros de grupos com privilégios administrativos.

## 5. Frentes de Front-End em Andamento
1. **Home Estilo Streaming (`home_page.html`):** Desenvolvida do zero com Tailwind CSS, estruturada com carrosséis horizontais responsivos segmentados por canais, tipos de mídia e trilhas curriculares consultadas diretamente do banco.
2. **Páginas de Consumo e Players (`conteudo_page.html`):** Renderização condicional por blocos baseada no formato técnico do recurso, exibindo metadados editoriais e licença Creative Commons.
3. **Busca Avançada (`search/search.html`):** Interface acoplada à view do Django contendo uma barra lateral com filtros multicritério (componentes curriculares, tipos de mídia, níveis de ensino e licenças) alimentados estritamente por consultas dinâmicas ao banco de dados.