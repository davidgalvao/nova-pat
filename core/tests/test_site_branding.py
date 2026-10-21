from django.test import TestCase
from django.conf import settings
from wagtail.models import Site


class SiteBrandingTest(TestCase):
    """Test that the site name and Wagtail admin branding are correctly configured."""

    def test_wagtail_site_name_setting(self):
        """WAGTAIL_SITE_NAME should be set to 'Nova PAT'."""
        self.assertEqual(settings.WAGTAIL_SITE_NAME, "Nova PAT")

    def test_default_site_has_site_name(self):
        """The default Wagtail Site should have site_name = 'Nova PAT'."""
        # Get the default site
        default_site = Site.objects.get(is_default_site=True)
        self.assertEqual(default_site.site_name, "Nova PAT")

    def test_wagtail_admin_is_configured(self):
        """WAGTAIL_ADMIN should be a dict with branding settings."""
        self.assertIsInstance(settings.WAGTAIL_ADMIN, dict)

    def test_wagtail_admin_colors(self):
        """WAGTAIL_ADMIN COLORS should use the brand palette (primary + secondary)."""
        colors = settings.WAGTAIL_ADMIN.get("COLORS", {})
        self.assertEqual(colors.get("primary"), "#1d4ed8")      # brand-500
        self.assertEqual(colors.get("secondary"), "#1e3a8a")    # brand-700

    def test_wagtail_admin_login_logo(self):
        """WAGTAIL_ADMIN LOGIN_LOGO should point to the institution logo."""
        self.assertEqual(
            settings.WAGTAIL_ADMIN.get("LOGIN_LOGO"),
            "images/logo-nova-pat.svg",
        )

    def test_wagtail_admin_site_name(self):
        """WAGTAIL_ADMIN SITE_NAME should match WAGTAIL_SITE_NAME."""
        self.assertEqual(
            settings.WAGTAIL_ADMIN.get("SITE_NAME"), settings.WAGTAIL_SITE_NAME
        )