from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ariz_engine.views import SessionViewSet

app_name = "ariz_engine"

router = DefaultRouter()
router.register("", SessionViewSet, basename="session")

urlpatterns = [
    path("", include(router.urls)),
]
