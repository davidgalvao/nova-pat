from django.db import migrations


def set_site_name(apps, schema_editor):
    """
    Set the site name to "Nova PAT" for the default site.
    """
    Site = apps.get_model('wagtailcore', 'Site')
    # Update the default site (localhost:80) to have site_name = "Nova PAT"
    Site.objects.filter(is_default_site=True).update(site_name="Nova PAT")


def unset_site_name(apps, schema_editor):
    """
    Revert site name to empty string.
    """
    Site = apps.get_model('wagtailcore', 'Site')
    Site.objects.filter(is_default_site=True).update(site_name="")


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_alter_homepage_body'),
        ('wagtailcore', '0053_locale_model'),  # Ensure wagtailcore Site field exists
    ]

    operations = [
        migrations.RunPython(set_site_name, unset_site_name),
    ]