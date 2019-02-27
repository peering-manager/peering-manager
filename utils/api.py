from collections import OrderedDict

from django.http import Http404

from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet as __ModelViewSet, ViewSet


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"


class ModelViewSet(__ModelViewSet):
    """
    Custom ModelViewSet capable of handling either a single object or a list of objects
    to create.
    """

    def get_serializer(self, *args, **kwargs):
        # A list is given so use many=True
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)


class StaticChoicesViewSet(ViewSet):
    """
    Expose values representing static choices for model fields.
    """

    permission_classes = [AllowAny]
    fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields = OrderedDict()

        for model, field_list in self.fields:
            for field_name in field_list:
                model_name = model._meta.verbose_name.lower().replace(" ", "-")
                key = ":".join([model_name, field_name])
                choices = []
                for k, v in model._meta.get_field(field_name).choices:
                    if type(v) in [list, tuple]:
                        for k2, v2 in v:
                            choices.append({"value": k2, "label": v2})
                    else:
                        choices.append({"value": k, "label": v})
                self._fields[key] = choices

    def list(self, request):
        return Response(self._fields)

    def retrieve(self, request, pk):
        if pk not in self._fields:
            raise Http404
        return Response(self._fields[pk])

    def get_view_name(self):
        return "Static Choices"


class WritableNestedSerializer(ModelSerializer):
    """
    Accept only ID on write while still giving a nested representation on read.
    """

    def run_validators(self, value):
        return

    def to_internal_value(self, data):
        if data is None:
            return None

        try:
            return self.Meta.model.objects.get(pk=int(data))
        except (TypeError, ValueError):
            raise ValidationError("Primary key must be an integer")
        except ObjectDoesNotExist:
            raise ValidationError("Invalid ID")
