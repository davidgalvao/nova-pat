/**
 * Toolbar settings page chooser integration.
 *
 * Quando uma página é selecionada no PageChooserWidget ao lado de um campo
 * "Página (…)", o caminho da página é copiado automaticamente para o campo
 * "URL" correspondente, facilitando a configuração de links internos sem
 * digitar o caminho manualmente.
 *
 * Mapeamento: campo de página → campo de URL
 *   link_acessibilidade_page        → link_acessibilidade_url
 *   link_privacidade_page           → link_privacidade_url
 *   link_acesso_informacao_page     → link_acesso_informacao_url
 */

(function () {
    const PAGE_TO_URL_MAP = {
        "link_acessibilidade_page": "link_acessibilidade_url",
        "link_privacidade_page": "link_privacidade_url",
        "link_acesso_informacao_page": "link_acesso_informacao_url",
    };

    function preencherUrl(pageId, campoUrl) {
        if (!pageId) {
            return;
        }

        // O Wagtail expõe o endpoint de API do chooser para buscar dados da página.
        // Usamos o endpoint interno do admin para obter o caminho (url) da página.
        fetch("/admin/api/pages/" + pageId + "/", {
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then((data) => {
                if (!data || !data.url) {
                    return;
                }
                const input = document.querySelector(
                    'input[name="' + campoUrl + '"], [id="' + campoUrl + '"]'
                );
                if (input) {
                    input.value = data.url;
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }
            })
            .catch(() => {
                // Silenciosamente ignora erros — o usuário ainda pode digitar a URL manualmente.
            });
    }

    function inicializar() {
        Object.keys(PAGE_TO_URL_MAP).forEach(function (campoPage) {
            const campoUrl = PAGE_TO_URL_MAP[campoPage];
            const inputPage = document.querySelector(
                'input[id="' + campoPage + '"], [name="' + campoPage + '"]'
            );
            if (!inputPage) {
                return;
            }

            // O PageChooserWidget do Wagtail dispara o evento 'pageChosen' quando
            // uma página é selecionada pelo chooser.
            inputPage.addEventListener("pageChosen", function (event) {
                const pageId = event.detail && event.detail.id ? event.detail.id : inputPage.value;
                preencherUrl(pageId, campoUrl);
            });

            // Fallback: se o valor do campo page mudar por qualquer outro meio,
            // tenta preencher a URL após um pequeno atraso.
            inputPage.addEventListener("change", function () {
                setTimeout(function () {
                    preencherUrl(inputPage.value, campoUrl);
                }, 100);
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }
})();
