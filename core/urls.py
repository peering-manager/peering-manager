from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Jobs
    path("jobs/", views.JobListView.as_view(), name="job_list"),
    path("jobs/delete/", views.JobBulkDeleteView.as_view(), name="job_bulk_delete"),
    path("jobs/<int:pk>/", views.JobView.as_view(), name="job_view"),
    path("jobs/<int:pk>/delete/", views.JobDeleteView.as_view(), name="job_delete"),
]
