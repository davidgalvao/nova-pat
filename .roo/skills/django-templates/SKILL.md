---
name: django-templates
description: Ative esta skill sempre que for criar ou editar um arquivo de template Django (.html com tags {% %} ou {{ }}) — antes de considerar a edição concluída, e obrigatoriamente antes de rodar qualquer teste que dependa da renderização desse template.
---

# Django Templates

## Instructions

# Django Templates

## Instruções

### 1. Valide a sintaxe antes de rodar testes
Depois de editar qualquer template, rode `python manage.py check` antes de rodar a suíte de testes. Isso pega erros de sintaxe de template (tags não fechadas, mal aninhadas) sem gastar tempo com o ciclo completo de testes até descobrir o mesmo erro.

### 2. Balanceie tags manualmente em templates grandes
Ao adicionar ou remover um bloco `{% if %}`, `{% for %}`, `{% block %}` em um template com muitos blocos aninhados, confira explicitamente que cada tag de abertura tem seu par de fechamento correspondente (`{% endif %}`, `{% endfor %}`, `{% endblock %}`) antes de seguir para a próxima alteração. Lembre-se: `{% for %}` só aceita `{% empty %}` ou `{% endfor %}` como continuação — nunca `{% else %}`. Um `{% else %}` solto nesse contexto é sinal de que um `{% for %}` anterior não foi fechado corretamente.

### 3. Não renderize variável que a view não envia
Antes de usar `{{ variavel }}` ou `{% if variavel %}` no template, confirme que a view correspondente realmente inclui essa chave no `context` passado para `render()`. Django não avisa sobre variável ausente — ela silenciosamente vira string vazia, o que mascara bugs de lógica (campo nunca aparece selecionado, condicional nunca é verdadeira) sem gerar erro visível.

### 4. Não misture dois modos de renderização no mesmo bloco
Evite escrever um template que tenta suportar dois contextos diferentes ao mesmo tempo (ex: "se existe X, renderiza de um jeito; senão, renderiza de outro jeito completamente distinto") a menos que isso tenha sido pedido explicitamente. Templates com múltiplos caminhos condicionais grandes são a fonte mais comum de tags desbalanceadas — prefira um único caminho de renderização sempre que a lógica de negócio permitir.