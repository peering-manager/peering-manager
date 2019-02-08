from rest_framework.viewsets import ModelViewSet as __ModelViewSet


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
