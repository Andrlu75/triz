from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/problems/", include("apps.problems.urls")),
    path("api/v1/sessions/", include("apps.ariz_engine.urls")),
    path("api/v1/knowledge/", include("apps.knowledge_base.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
]
