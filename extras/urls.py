from django.urls import path

from . import views

app_name = "extras"

urlpatterns = [
    path("job-results/", views.JobResultListView.as_view(), name="jobresult_list"),
    path(
        "job-results/<int:pk>/",
        views.JobResultView.as_view(),
        name="jobresult_details",
    ),
    path(
        "job-results/delete/",
        views.JobResultBulkDeleteView.as_view(),
        name="jobresult_bulk_delete",
    ),
    path(
        "job-results/<int:pk>/delete/",
        views.JobResultDeleteView.as_view(),
        name="job_result_delete",
    ),
]
