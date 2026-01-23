from django.urls import path
from . import views
urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("importar_raas/", views.importar_raas, name="importar_raas"),
        ]