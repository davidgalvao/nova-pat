from django.conf import settings
from django.test import TestCase


class RichTextEditorConfigTest(TestCase):
    """Test that WAGTAILADMIN_RICH_TEXT_EDITORS is configured with the allowed features."""

    def test_wagtail_rich_text_editors_default_features(self):
        """WAGTAILADMIN_RICH_TEXT_EDITORS['default'] exibe exatamente as features do card NOVAPAT-27.

        Escopo do card: configurar o editor RichText do admin (não o StreamField)
        com Headings (h2, h3, h4), Estilo (bold, italic), Listas (ol, ul),
        Links (link) e Utilidades (hr, blockquote).
        """
        editors = settings.WAGTAILADMIN_RICH_TEXT_EDITORS

        self.assertIn("default", editors, "WAGTAILADMIN_RICH_TEXT_EDITORS deve definir o editor 'default'")

        default = editors["default"]
        self.assertEqual(
            default["WIDGET"],
            "wagtail.admin.rich_text.DraftailRichTextArea",
            "O editor padrão do Wagtail admin deve usar DraftailRichTextArea",
        )

        features = sorted(default["OPTIONS"]["features"])
        expected = sorted([
            "h2", "h3", "h4",   # Headings
            "bold", "italic",   # Estilo
            "ol", "ul",         # Listas
            "link",             # Links
            "hr", "blockquote", # Utilidades
        ])
        self.assertEqual(features, expected)
        self.assertEqual(len(features), 10, "Não devem existir features além das definidas no card")
