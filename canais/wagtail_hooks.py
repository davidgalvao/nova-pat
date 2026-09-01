from django.utils.translation import gettext_lazy as _

from .models import CanalPage


# CanalPage é uma Page (`canais.CanalPage`) e registra-se automaticamente no admin
# do Wagtail por herdar de `wagtail.models.Page`. O antigo `ModelAdmin` de Canais foi
# removido na migração para Wagtail 8 (o `wagtail_modeladmin` foi descontinuado).
#
# Este módulo é mantido apenas para documentar a decisão e para que o app `canais`
# continue importável via `ready()` em `apps.py`.