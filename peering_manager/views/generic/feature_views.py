from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from core.models import Job, ObjectChange
from core.tables import JobTable, ObjectChangeTable

__all__ = ("ObjectChangeLogView", "ObjectJobsView")


class ObjectChangeLogView(View):
    """
    Present a history of changes made to a particular object. The model class must be
    passed as a keyword argument when referencing this view in a URL path. For
    example:

        path(
            'autonomous-systems/<int:pk>/changelog/',
            ObjectChangeLogView.as_view(),
            name='autonomoussystem_changelog',
            kwargs={'model': AutonomousSystem},
        ),

    The `base_template` parameter is the name of the template to extend.
    """

    tab = "changelog"

    def get(self, request, model, **kwargs):
        obj = get_object_or_404(model, **kwargs)

        # Gather all changes for this object (and its related objects)
        content_type = ContentType.objects.get_for_model(model)
        objectchanges = ObjectChange.objects.prefetch_related(
            "user", "changed_object_type"
        ).filter(
            Q(changed_object_type=content_type, changed_object_id=obj.pk)
            | Q(related_object_type=content_type, related_object_id=obj.pk)
        )
        objectchanges_table = ObjectChangeTable(
            data=objectchanges, orderable=False, user=request.user
        )
        objectchanges_table.configure(request)

        # Check whether a header template exists for this model
        base_template = f"{model._meta.app_label}/{model._meta.model_name}/_base.html"
        try:
            template.loader.get_template(base_template)
        except template.TemplateDoesNotExist:
            base_template = "_base.html"

        return render(
            request,
            "extras/object_changelog.html",
            {
                "instance": obj,
                "table": objectchanges_table,
                "base_template": base_template,
                "tab": self.tab,
            },
        )


class ObjectJobsView(View):
    """
    Render a list of all Jobs assigned to an object. For example:

        path(
            'routers/<int:pk>/jobs/',
            ObjectJobsView.as_view(),
            name='router_jobs',
            kwargs={'model': Router}
        ),

    The `base_template` parameter is the name of the template to extend.
    """

    tab = "jobs"

    def get_object(self, request, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def get_jobs(self, instance):
        object_type = ContentType.objects.get_for_model(instance)
        return Job.objects.filter(object_type=object_type, object_id=instance.id)

    def get(self, request, model, **kwargs):
        self.model = model
        obj = self.get_object(request, **kwargs)

        # Gather all Jobs for this object
        jobs = self.get_jobs(obj)
        jobs_table = JobTable(data=jobs, orderable=False, user=request.user)
        jobs_table.configure(request)

        # Check whether a header template exists for this model
        base_template = f"{model._meta.app_label}/{model._meta.model_name}/_base.html"
        try:
            template.loader.get_template(base_template)
        except template.TemplateDoesNotExist:
            base_template = "_base.html"

        return render(
            request,
            "core/object_jobs.html",
            {
                "instance": obj,
                "table": jobs_table,
                "base_template": base_template,
                "tab": self.tab,
            },
        )
