from django.urls import path

from .views import DownloadDOCXView, DownloadPDFView, ReportListView

app_name = "reports"

urlpatterns = [
    path(
        "",
        ReportListView.as_view(),
        name="report-list",
    ),
    path(
        "<int:session_id>/download/pdf/",
        DownloadPDFView.as_view(),
        name="download-pdf",
    ),
    path(
        "<int:session_id>/download/docx/",
        DownloadDOCXView.as_view(),
        name="download-docx",
    ),
]
