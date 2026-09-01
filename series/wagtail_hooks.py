from django.utils.translation import gettext_lazy as _

from .models import Serie, Temporada


# `Serie` e `Temporada` são Pages (`series.Serie`, `series.Temporada`) e registram-se
# automaticamente no admin do Wagtail por herdarem de `wagtail.models.Page`.
# O antigo `SeriesModelAdminGroup` (wagtail_modeladmin) foi removido na migração para
# Wagtail 8 (a lib foi descontinuada no Wagtail 8).
#
# Este módulo é mantido apenas para documentar a decisão.