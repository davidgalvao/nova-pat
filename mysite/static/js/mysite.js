/**
 * mysite.js — Funcionalidades de acessibilidade do site Nova PAT.
 *
 * Fornece controle de tamanho de fonte e alternância de contraste alto,
 * com persistência em localStorage para manter as preferências entre
 * navegações. Código vanilla JS, sem dependências externas.
 */

(function () {
    'use strict';

    // ------------------------------------------------------------------
    // Constantes de configuração
    // ------------------------------------------------------------------

    // Chaves usadas no localStorage
    var LS_FATOR_FONTE = 'novapat_fator_fonte';
    var LS_CONTRASTE = 'novapat_contraste_alto';

    // Steps de escala de fonte e limites
    var FONTE_PADRAO = 1.0;      // 100% (tamanho padrão)
    var FONTE_MIN = 0.4;         // 40% do tamanho padrão
    var FONTE_MAX = 1.6;         // 160% do tamanho padrão
    var FONTE_STEP = 0.2;        // passo de 20% por clique

    // Seletores dos elementos alvo
    var SELETOR_MAIN_CONTENT = '#main-content';
    var SELETOR_BODY = 'body';
    var SELETOR_HTML = 'html';

    // Classe CSS aplicada no <html> para alto contraste
    var CLASSE_CONTRASTE_ALTO = 'contraste-alto';

    // ------------------------------------------------------------------
    // Helpers de localStorage
    // ------------------------------------------------------------------

    /**
     * Lê um valor do localStorage com fallback para um valor padrão.
     * Nunca lança exceção se o localStorage estiver indisponível.
     */
    function lerLocalStorage(chave, valorPadrao) {
        try {
            var valor = window.localStorage.getItem(chave);
            return valor === null ? valorPadrao : valor;
        } catch (e) {
            return valorPadrao;
        }
    }

    /**
     * Grava um valor no localStorage. Nunca lança exceção se
     * o localStorage estiver indisponível.
     */
    function gravarLocalStorage(chave, valor) {
        try {
            window.localStorage.setItem(chave, valor);
        } catch (e) {
            // Ignora falha silenciosamente (ex: modo privado/cookies desativados)
        }
    }

    // ------------------------------------------------------------------
    // Controle de tamanho de fonte
    // ------------------------------------------------------------------

    /**
     * Aplica o fator de escala de fonte ao documento usando a custom
     * property CSS --fonte-base (definida em :root via mysite.css) e,
     * como fallback, define o fontSize inline em #main-content e body.
     *
     * @param {number} fator Fator de escala (ex: 1.0, 1.2, 0.8).
     */
    function aplicarFonte(fator) {
        var fatorArredondado = Math.round(fator * 100) / 100;
        var tamanhoCss = fatorArredondado + 'em';

        // Define a custom property na raiz do documento (mesma definida em mysite.css)
        document.documentElement.style.setProperty('--fonte-base', tamanhoCss);

        // Fallback direto para os elementos de conteúdo principal
        var mainContent = document.querySelector(SELETOR_MAIN_CONTENT);
        if (mainContent) {
            mainContent.style.fontSize = tamanhoCss;
        }

        var body = document.querySelector(SELETOR_BODY);
        if (body) {
            body.style.fontSize = tamanhoCss;
        }

        // Persiste a escolha para manter entre navegações
        gravarLocalStorage(LS_FATOR_FONTE, String(fatorArredondado));
    }

    /**
     * Diminui o tamanho da fonte em um step, respeitando o limite mínimo.
     */
    function diminuirFonte() {
        var fatorAtual = parseFloat(lerLocalStorage(LS_FATOR_FONTE, String(FONTE_PADRAO)));
        var novoFator = Math.max(FONTE_MIN, fatorAtual - FONTE_STEP);
        aplicarFonte(novoFator);
    }

    /**
     * Aumenta o tamanho da fonte em um step, respeitando o limite máximo.
     */
    function aumentarFonte() {
        var fatorAtual = parseFloat(lerLocalStorage(LS_FATOR_FONTE, String(FONTE_PADRAO)));
        var novoFator = Math.min(FONTE_MAX, fatorAtual + FONTE_STEP);
        aplicarFonte(novoFator);
    }

    /**
     * Restaura o tamanho de fonte ao padrão.
     */
    function resetarFonte() {
        aplicarFonte(FONTE_PADRAO);
    }

    // Expondo funções globalmente para uso em atributos onclick / inline, se necessário
    window.diminuirFonte = diminuirFonte;
    window.aumentarFonte = aumentarFonte;
    window.resetarFonte = resetarFonte;

    // ------------------------------------------------------------------
    // Controle de contraste
    // ------------------------------------------------------------------

    /**
     * Alterna entre tema normal e alto contraste, adicionando/removendo
     * a classe CSS .contraste-alto no <html> e persistindo a escolha.
     */
    function alternarContraste() {
        var html = document.documentElement;
        var jaEstaAtivo = html.classList.contains(CLASSE_CONTRASTE_ALTO);

        if (jaEstaAtivo) {
            html.classList.remove(CLASSE_CONTRASTE_ALTO);
            gravarLocalStorage(LS_CONTRASTE, '0');
        } else {
            html.classList.add(CLASSE_CONTRASTE_ALTO);
            gravarLocalStorage(LS_CONTRASTE, '1');
        }
    }

    window.alternarContraste = alternarContraste;

    // ------------------------------------------------------------------
    // Inicialização
    // ------------------------------------------------------------------

    /**
     * Lê as preferências salvas no localStorage e as aplica ao documento.
     * Executado no DOMContentLoaded.
     */
    function inicializarAcessibilidade() {
        // Aplica o tamanho de fonte salvo (ou padrão)
        var fatorSalvo = parseFloat(lerLocalStorage(LS_FATOR_FONTE, String(FONTE_PADRAO)));
        var fatorValido = isNaN(fatorSalvo)
            ? FONTE_PADRAO
            : Math.min(Math.max(fatorSalvo, FONTE_MIN), FONTE_MAX);
        aplicarFonte(fatorValido);

        // Aplica o contraste salvo, se houver
        var contrasteSalvo = lerLocalStorage(LS_CONTRASTE, '0');
        if (contrasteSalvo === '1') {
            document.documentElement.classList.add(CLASSE_CONTRASTE_ALTO);
        }

        // Vincula os event listeners aos botões da toolbar de acessibilidade
        vincularBotoesToolbar();
    }

    /**
     * Vincula os event listeners aos botões da toolbar, identificados pelo
     * atributo title (mais robusto que depender de IDs únicos em cada botão).
     */
    function vincularBotoesToolbar() {
        var botoes = document.querySelectorAll('button[title]');
        botoes.forEach(function (botao) {
            var title = botao.getAttribute('title');

            switch (title) {
                case 'Diminuir Fonte':
                    botao.addEventListener('click', diminuirFonte);
                    break;
                case 'Aumentar Fonte':
                    botao.addEventListener('click', aumentarFonte);
                    break;
                case 'Voltar Fonte Inicial':
                    botao.addEventListener('click', resetarFonte);
                    break;
                case 'Contraste':
                    botao.addEventListener('click', alternarContraste);
                    break;
                default:
                    // Outros botões/links da toolbar não são controlados aqui
                    break;
            }
        });
    }

    // Dispara a inicialização assim que o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarAcessibilidade);
    } else {
        // DOM já carregado (ex: script executado com defer)
        inicializarAcessibilidade();
    }

})();
