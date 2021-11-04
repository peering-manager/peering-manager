import logging

import requests
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from django_rq import get_queue, job

from utils.api import get_serializer_for_model
from utils.enums import ObjectChangeAction
from utils.functions import generate_signature
from utils.models import ObjectChange

from .models import Webhook

logger = logging.getLogger("peering.manager.extras")


@job("default")
def process_webhook(webhook, data, model_name, event, timestamp, username, request_id):
    """
    Makes a request to the defined Webhook endpoint.
    """
    headers = {"Content-Type": webhook.http_content_type}
    context = {
        "event": event,
        "timestamp": timestamp,
        "model": model_name,
        "username": username,
        "request_id": request_id,
        "data": data,
    }
    params = {
        "method": webhook.http_method,
        "url": webhook.url,
        "headers": headers,
        "data": webhook.render_body(context).encode("utf8"),
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


def enqueue_webhooks(instance, user, request_id, action):
    """
    Enqueues webhooks so they can be processed.
    """
    # Ignore object changes as a webhook is about informing of a change
    if isinstance(instance, ObjectChange) or isinstance(instance, LogEntry):
        return

    # Finds usable webhooks
    action_flag = {
        ObjectChangeAction.CREATE: "type_create",
        ObjectChangeAction.UPDATE: "type_update",
        ObjectChangeAction.DELETE: "type_delete",
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
                "extras.workers.process_webhook",
                webhook,
                serializer.data,
                instance._meta.model_name,
                action,
                str(timezone.now()),
                user.username,
                request_id,
            )
