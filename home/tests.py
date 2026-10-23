from home.models import HomePage

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.template.loader import get_template
from django.test import SimpleTestCase
from django.test import TestCase

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")


class ToolbarAcessibilidadeTests(TestCase):
    """
    Testes da toolbar de acessibilidade (JS/CSS) e regressão dos botões.

    Não há suíte de JS no projeto (os testes são Django/pytest), então a
    validação do JavaScript é feita por inspeção dos arquivos estáticos
    (mysite.js / mysite.css), que é o artefato entregue ao navegador.
    """

    def _ler_static(self, caminho):
        """
        Lê o conteúdo de um arquivo estático em mysite/static/<caminho>.
        Retorna None quando o arquivo não é encontrado pelos finders.
        """
        caminho_arquivo = find(caminho)
        if not caminho_arquivo:
            return None
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return f.read()

    def test_mysite_js_aplica_rem_e_expoe_funcoes_globais(self):
        """
        O mysite.js deve definir --fonte-base com unidade rem (sem
        compociação entre body e #main-content), aplicar o tamanho em
        #main-content e body e expor aumentar/diminuir/resetar no window.
        A persistência em localStorage (novapat_fator_fonte) deve estar presente.
        """
        js = self._ler_static("js/mysite.js")
        self.assertIsNotNone(js, "mysite/static/js/mysite.js não encontrado")
        self.assertIn("--fonte-base", js)
        self.assertIn("'rem'", js)  # unidade rem, sem compociação
        self.assertIn("window.aumentarFonte", js)
        self.assertIn("window.diminuirFonte", js)
        self.assertIn("window.resetarFonte", js)
        self.assertIn("novapat_fator_fonte", js)  # persistência localStorage

    def test_mysite_css_escala_titulos_via_fonte_base(self):
        """
        O mysite.css deve aplicar --fonte-base a #main-content e body e
        definir uma escala de títulos (h1-h6) relativa a --fonte-base,
        para que aumentar/diminuir/resetar a fonte alcance os títulos.
        """
        css = self._ler_static("css/mysite.css")
        self.assertIsNotNone(css, "mysite/static/css/mysite.css não encontrado")
        self.assertIn("font-size: var(--fonte-base);", css)
        for nivel in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.assertIn(f"#main-content {nivel}", css)

    def test_toolbar_botoes_fonte_estao_presentes_regressao(self):
        """
        Regressão: o template da toolbar deve continuar renderizando os
        botões de fonte (Diminuir/Aumentar/Voltar Fonte).
        """
        from django.template.loader import get_template

        conteudo = get_template("includes/toolbar.html").template.source
        self.assertIn('title="Diminuir Fonte"', conteudo)
        self.assertIn('title="Aumentar Fonte"', conteudo)
        self.assertIn('title="Voltar Fonte Inicial"', conteudo)


class ContrasteAltoContratoTestes(SimpleTestCase):
    """
    Contrato de templates/estáticos da alternância de alto contraste.

    Verifica que as peças necessárias para o modo de alto contraste
    estão corretamente wireadas:
    - base.html inclui a toolbar e linka mysite.css / mysite.js;
    - toolbar.html expõe o botão "Contraste";
    - mysite.css define a classe .contraste-alto e suas variáveis de cor.

    São testes de contrato (sem banco de dados) — não validam seletores CSS
    nem comportamento de navegador (coberto por mysite/static/js/tests/test_contraste.js).
    """

    def _ler_arquivo_estatico(self, caminho_relativo):
        return (settings.BASE_DIR / caminho_relativo).read_text(encoding="utf-8")

    def test_base_inclui_toolbar(self):
        conteudo = get_template("base.html").template.source
        self.assertIn('includes/toolbar.html', conteudo)

    def test_base_linka_mysite_css(self):
        conteudo = get_template("base.html").template.source
        self.assertIn("css/mysite.css", conteudo)

    def test_base_linka_mysite_js(self):
        conteudo = get_template("base.html").template.source
        self.assertIn("js/mysite.js", conteudo)

    def test_toolbar_tem_botao_contraste(self):
        conteudo = get_template("includes/toolbar.html").template.source
        self.assertIn('title="Contraste"', conteudo)

    def test_css_tem_classe_contraste_alto(self):
        css = self._ler_arquivo_estatico("mysite/static/css/mysite.css")
        self.assertIn(".contraste-alto", css)

    def test_css_tem_variaveis_contraste(self):
        css = self._ler_arquivo_estatico("mysite/static/css/mysite.css")
        self.assertIn("--cor-fundo-contraste", css)
        self.assertIn("--cor-texto-contraste", css)
        self.assertIn("--cor-link-contraste", css)

    def test_css_cobre_titulos_em_contraste(self):
        css = self._ler_arquivo_estatico("mysite/static/css/mysite.css")
        for seletor in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.assertIn(f".contraste-alto {seletor}", css)

    def test_css_cobre_fundos_em_contraste(self):
        css = self._ler_arquivo_estatico("mysite/static/css/mysite.css")
        for classe in (".bg-white", ".bg-gray-50", ".bg-gray-100", ".bg-black"):
            self.assertIn(f".contraste-alto {classe}", css)

    def test_css_cobre_links_em_contraste(self):
        css = self._ler_arquivo_estatico("mysite/static/css/mysite.css")
        self.assertIn(".contraste-alto a", css)
