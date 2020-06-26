import hashlib
import hmac
import logging
import requests

from django.utils import timezone
from django_rq import job, get_queue

from .models import Webhook
from utils.constants import *
from utils.models import ObjectChange


logger = logging.getLogger("peering.manager.webhooks")


def generate_signature(request_body, secret):
    """
    Returns a signature that can be used to verify that the webhook data were not
    altered.
    """
    signature = hmac.new(
        key=secret.encode("utf8"), msg=request_body, digestmod=hashlib.sha512
    )
    return signature.hexdigest()


@job("default")
def process_webhook(webhook, data, model_name, event, timestamp, username, request_id):
    """
    Makes a request to the defined Webhook endpoint.
    """
    headers = {"Content-Type": webhook.http_content_type}
    params = {
        "method": webhook.http_method,
        "url": webhook.url,
        "headers": headers,
        "data": webhook.render_body(data).encode("utf8"),
    }

    logger.info(
        "Sending %s request to %s (%s %s)",
        params["method"],
        params["url"],
        model_name,
        event,
    )
    logger.debug(params)
    try:
        prepared_request = requests.Request(**params).prepare()
    except requests.exceptions.RequestException as e:
        logger.error("Error forming HTTP request: %s", e)
        raise e

    # If a secret key is defined, sign the request with a hash (key + content)
    if webhook.secret != "":
        prepared_request.headers["X-Hook-Signature"] = generate_signature(
            prepared_request.body, webhook.secret
        )

    # Send the request
    with requests.Session() as session:
        session.verify = webhook.ssl_verification
        if webhook.ca_file_path:
            session.verify = webhook.ca_file_path
        response = session.send(prepared_request)

    if 200 <= response.status_code <= 299:
        logger.info("Request succeeded; response status %s", response.status_code)
        return f"Status {response.status_code} returned, webhook successfully processed"
    else:
        logger.warning(
            "Request failed; response status %s: %s",
            response.status_code,
            response.content,
        )
        raise requests.exceptions.RequestException(
            f"Status {response.status_code} returned with content '{response.content}', webhook FAILED to process"
        )


def get_serializer_for_model(model, prefix=""):
    """
    Returns the appropriate API serializer for a model.
    """
    app_name, model_name = model._meta.label.split(".")
    serializer_name = f"{app_name}.api.serializers.{prefix}{model_name}Serializer"
    try:
        # Try importing the serializer class
        components = serializer_name.split(".")
        mod = __import__(components[0])
        for c in components[1:]:
            mod = getattr(mod, c)
        return mod
    except AttributeError:
        raise Exception(
            f"Could not determine serializer for {app_name}.{model_name} with prefix '{prefix}'"
        )


def enqueue_webhooks(instance, user, request_id, action):
    """
    Enqueues webhooks so they can be processed.
    """
    # Ignore object changes as a webhook is about informing of a change
    if isinstance(instance, ObjectChange):
        return

    # Finds usable webhooks
    action_flag = {
        OBJECT_CHANGE_ACTION_CREATE: "type_create",
        OBJECT_CHANGE_ACTION_UPDATE: "type_update",
        OBJECT_CHANGE_ACTION_DELETE: "type_delete",
    }[action]
    webhooks = Webhook.objects.filter(enabled=True, **{action_flag: True})

    if webhooks.exists():
        # Get the Model's API serializer class and serialize the object
        serializer_class = get_serializer_for_model(instance.__class__)
        serializer_context = {"request": None}
        serializer = serializer_class(instance, context=serializer_context)

        # Enqueue the webhooks
        webhook_queue = get_queue("default")
        for webhook in webhooks:
            webhook_queue.enqueue(
                "webhooks.workers.process_webhook",
                webhook,
                serializer.data,
                instance._meta.model_name,
                action,
                str(timezone.now()),
                user.username,
                request_id,
            )
