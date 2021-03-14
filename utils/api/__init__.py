from collections import OrderedDict

from django.db.models import ManyToManyField
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework.fields import ListField
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet as __ModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet as __ReadOnlyModelViewSet
from rest_framework.viewsets import ViewSet

from utils.functions import get_serializer_for_model


class InetAddressArrayField(ListField):
    """
    Converts an array of InetAddressField to something usable in an API.
    """

    def to_representation(self, data):
        inet_addresses = super().to_representation(data)
        if not inet_addresses:
            return []

        return [str(inet_address) for inet_address in inet_addresses]


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

    def get_serializer_class(self):
        request = self.get_serializer_context()["request"]
        if request.query_params.get("brief"):
            try:
                return get_serializer_for_model(self.queryset.model, suffix="Nested")
            except Exception:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def list(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().retrieve(*args, **kwargs)


class ReadOnlyModelViewSet(__ReadOnlyModelViewSet):
    """
    Custom ReadOnlyModelViewSet capable of using nested serializers.
    """

    def get_serializer(self, *args, **kwargs):
        # A list is given so use many=True
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        request = self.get_serializer_context()["request"]
        if request.query_params.get("brief"):
            try:
                return get_serializer_for_model(self.queryset.model, suffix="Nested")
            except Exception:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def list(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().retrieve(*args, **kwargs)


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


class WriteEnabledNestedSerializer(ModelSerializer):
    """
    Allow write operations on create and on update for nested serializers.
    """

    def create_or_update(self, instance=None, validated_data={}):
        """
        Create or update an object also setting the values of nested fields. The
        object will only be created if no instance of it already exist (on update).
        """
        nested = {}
        final_save = False

        # Retrieve the nested field values to create the instance before assigning
        # these values to the instance's field
        for field in self.Meta.nested_fields:
            if field in validated_data:
                nested[field] = validated_data.pop(field)

        if instance is None:
            # Create the instance and set nested field values
            instance = self.Meta.model.objects.create(**validated_data)
        else:
            # Update the instance
            for field_name, value in validated_data.items():
                setattr(instance, field_name, value)
                final_save = True

        for field_name, value in nested.items():
            # Special case for many-to-many fields that require to use set()
            # Direct assignment won't work for those fields
            if isinstance(instance._meta.get_field(field_name), ManyToManyField):
                getattr(instance, field_name).set(value)
            else:
                setattr(instance, field_name, value)
            final_save = True

        if final_save:
            instance.save()
        return instance

    def create(self, validated_data):
        return self.create_or_update(validated_data=validated_data)

    def update(self, instance, validated_data):
        return self.create_or_update(instance=instance, validated_data=validated_data)
