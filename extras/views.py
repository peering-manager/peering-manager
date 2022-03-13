from peering.models.models import InternetExchange
from peering_manager.views.generics import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from .filters import IXAPIFilterSet, JobResultFilterSet
from .forms import IXAPIFilterForm, IXAPIForm, JobResultFilterForm
from .models import IXAPI, JobResult
from .tables import IXAPITable, JobResultTable


class IXAPIListView(ObjectListView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()
    filterset = IXAPIFilterSet
    filterset_form = IXAPIFilterForm
    table = IXAPITable
    template_name = "extras/ixapi/list.html"


class IXAPIView(ObjectView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "internet_exchange_points": InternetExchange.objects.filter(
                ixapi_endpoint=instance
            ),
            "active_tab": "main",
        }


class IXAPIAddView(ObjectEditView):
    permission_required = "extras.add_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIEditView(ObjectEditView):
    permission_required = "extras.change_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ixapi"
    queryset = IXAPI.objects.all()


class JobResultListView(ObjectListView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
    filterset = JobResultFilterSet
    filterset_form = JobResultFilterForm
    table = JobResultTable
    template_name = "extras/jobresult/list.html"


class JobResultDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_jobresult"
    queryset = JobResult.objects.all()


class JobResultBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_jobresult"
    queryset = JobResult.objects.all()
    filterset = JobResultFilterSet
    table = JobResultTable


class JobResultView(ObjectView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
