from django.urls import path
from . import views
urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path('mapa/', views.mapa_calor_view, name='mapa_calor'),
    path("importar_raas/", views.importar_raas, name="importar_raas"),
    path("procedimentos/", views.lista_procedimentos, name="lista_procedimentos"),
        ]