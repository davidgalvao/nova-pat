# Migração para o model SiteSettings (NOVAPAT-60).
# Configurações editáveis do site (nome e logotipo) via BaseSiteSetting do Wagtail.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_navigationitem_parent"),
        ("wagtailcore", "0001_initial"),
        ("wagtailimages", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site",
                    models.OneToOneField(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="wagtailcore.site",
                        unique=True,
                    ),
                ),
                (
                    "site_name",
                    models.CharField(
                        blank=True,
                        help_text="Nome exibido no cabeçalho e no título do navegador.",
                        max_length=255,
                        verbose_name="Nome do site",
                    ),
                ),
                (
                    "logo",
                    models.ForeignKey(
                        blank=True,
                        help_text="Imagem de logotipo exibida no cabeçalho do site.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                        verbose_name="Logotipo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Configurações do site",
                "verbose_name_plural": "Configurações do site",
            },
        ),
    ]
