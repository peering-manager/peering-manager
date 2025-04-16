from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from core.models import Job, ObjectChange
from core.tables import JobTable, ObjectChangeTable
from extras.forms import JournalEntryForm
from extras.models import JournalEntry
from extras.tables import JournalEntryTable

__all__ = ("ObjectChangeLogView", "ObjectJobsView", "ObjectJournalView")


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
    """

    tab = "changelog"

    def get(self, request, model, **kwargs):
        instance = get_object_or_404(model, **kwargs)

        # Gather all changes for this object (and its related objects)
        content_type = ContentType.objects.get_for_model(model)
        objectchanges = ObjectChange.objects.prefetch_related(
            "user", "changed_object_type"
        ).filter(
            Q(changed_object_type=content_type, changed_object_id=instance.pk)
            | Q(related_object_type=content_type, related_object_id=instance.pk)
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
                "instance": instance,
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
    """

    tab = "jobs"

    def get_object(self, request, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def get_jobs(self, instance):
        object_type = ContentType.objects.get_for_model(instance)
        return Job.objects.filter(object_type=object_type, object_id=instance.id)

    def get(self, request, model, **kwargs):
        self.model = model
        instance = self.get_object(request, **kwargs)

        # Gather all Jobs for this object
        jobs = self.get_jobs(instance)
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
                "instance": instance,
                "table": jobs_table,
                "base_template": base_template,
                "tab": self.tab,
            },
        )


class ObjectJournalView(View):
    """
    Show all journal entries for an object. The model class must be passed as
    a keyword argument when referencing this view in a URL path. For example:

        path(
            'autonomous-systems/<int:pk>/journal/',
            ObjectJournalView.as_view(),
            name='autonomoussystem_journal',
            kwargs={'model': AutonomousSystem}
        ),
    """

    tab = "journal"

    def get(self, request, model, **kwargs):
        instance = get_object_or_404(model, **kwargs)

        # Gather all journal entries for this object
        content_type = ContentType.objects.get_for_model(model)
        journalentries = JournalEntry.objects.prefetch_related("created_by").filter(
            assigned_object_type=content_type, assigned_object_id=instance.pk
        )
        journalentry_table = JournalEntryTable(journalentries, user=request.user)
        journalentry_table.configure(request)
        journalentry_table.columns.hide("assigned_object_type")
        journalentry_table.columns.hide("assigned_object")

        if request.user.has_perm("extras.add_journalentry"):
            form = JournalEntryForm(
                initial={
                    "assigned_object_type": ContentType.objects.get_for_model(instance),
                    "assigned_object_id": instance.pk,
                }
            )
        else:
            form = None

        # Check whether a header template exists for this model
        base_template = f"{model._meta.app_label}/{model._meta.model_name}/_base.html"
        try:
            template.loader.get_template(base_template)
        except template.TemplateDoesNotExist:
            base_template = "_base.html"

        return render(
            request,
            "extras/object_journal.html",
            {
                "instance": instance,
                "form": form,
                "table": journalentry_table,
                "base_template": base_template,
                "tab": self.tab,
            },
        )
