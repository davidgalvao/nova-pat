"""
Configuração de rotas (URLconf) do projeto Nova PAT.

Ordem das rotas (importante — o Django processa na ordem):

1. `django-admin/` — admin nativo do Django (não Wagtail).
2. `admin/` — admin do Wagtail (interface de gestão de conteúdo).
3. `documents/` — biblioteca de documentos do Wagtail.
4. `search/` — busca avançada customizada (RF001, ver `search/views.py`).
5. `__reload__/` — django-browser-reload para hot-reload em desenvolvimento.
6. (DEBUG) static/media — servidos pelo runserver em desenvolvimento.
7. `""` (catch-all) — **deve ser a última rota**: delega ao mecanismo de
   serving de páginas do Wagtail (`wagtail_urls`). Qualquer rota não capturada
   acima vira uma Page do Wagtail.

Não alterar a ordem sem entender as implicações — o catch-all do Wagtail
precisa ficar por último.
"""

from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("__reload__/", include("django_browser_reload.urls")),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
