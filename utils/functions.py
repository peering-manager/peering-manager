import hashlib
import hmac

from django_rq import get_queue, job


def call_function(name, instance=None, **params):
    """
    Makes a call to a function or a method of an instance. The name of the
    function/method to call must be provided, named parameters can also be provided.

    The name of the function to call must contain the full path to its module:

      call_function("foo.bar.baz", param1=1, param2="str")

    The previous example will make a call to the function named "baz" from the
    "foo.bar" module passing two named parameters to the function.
    """
    if instance is None:
        components = name.split(".")
        return getattr(".".join(components[:-1]), components[-1])(**params)
    else:
        return getattr(instance, name)(**params)


def enqueue_background_task(function_name, instance=None, **params):
    queue = get_queue("default")
    return queue.enqueue(
        "utils.functions.call_function", function_name, instance=instance, **params
    )


def get_background_task(job_id):
    queue = get_queue("default")
    return queue.fetch_job(job_id)


def generate_signature(data, secret):
    """
    Returns a signature that can be used to verify that the webhook data were not
    altered.
    """
    signature = hmac.new(key=secret.encode("utf8"), msg=data, digestmod=hashlib.sha512)
    return signature.hexdigest()


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
        raise Exception(
            f"Could not determine serializer for {app_name}.{model_name} with prefix '{prefix}' and suffix '{suffix}'"
        )
