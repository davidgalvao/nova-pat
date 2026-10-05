from django.test import TestCase
from django.conf import settings
from wagtail.models import Site


class SiteBrandingTest(TestCase):
    """Test that the site name is correctly configured."""

    def test_wagtail_site_name_setting(self):
        """WAGTAIL_SITE_NAME should be set to 'Nova PAT'."""
        self.assertEqual(settings.WAGTAIL_SITE_NAME, "Nova PAT")

    def test_default_site_has_site_name(self):
        """The default Wagtail Site should have site_name = 'Nova PAT'."""
        # Get the default site
        default_site = Site.objects.get(is_default_site=True)
        self.assertEqual(default_site.site_name, "Nova PAT")