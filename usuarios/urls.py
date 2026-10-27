from django.urls import path

from . import admin_views

app_name = "usuarios"

urlpatterns = [
    path(
        "expurgar-inativos/",
        admin_views.RetencaoUsuariosView.as_view(),
        name="expurgar_inativos",
    ),
]
