from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.problems.views import ProblemViewSet

app_name = "problems"

router = DefaultRouter()
router.register("", ProblemViewSet, basename="problem")

urlpatterns = [
    path("", include(router.urls)),
]
