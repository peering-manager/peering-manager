from peering_manager.api.exceptions import SerializerNotFound


def get_serializer_for_model(model, prefix="", suffix=""):
    """
    Returns the appropriate API serializer for a model.
    """
    app_name, model_name = model._meta.label.split(".")
    if app_name == "auth":
        app_name = "users"
    serializer_name = (
        f"{app_name}.api.serializers.{prefix}{model_name}{suffix}Serializer"
    )
    try:
        # Try importing the serializer class
        components = serializer_name.split(".")
        mod = __import__(components[0])
        for c in components[1:]:
            mod = getattr(mod, c)
        return mod
    except AttributeError:
        raise SerializerNotFound(
            f"Could not determine serializer for {app_name}.{model_name} with prefix '{prefix}' and suffix '{suffix}'"
        )
