import logging

import requests
from django.conf import settings
from django_rq import job

from utils.functions import generate_signature

logger = logging.getLogger("peering.manager.extras")


@job("default")
def process_webhook(
    webhook, model_name, event, data, snapshots, timestamp, username, request_id
):
    """
    Makes a request to the defined Webhook endpoint.
    """
    headers = {
        "User-Agent": settings.REQUESTS_USER_AGENT,
        "Content-Type": webhook.http_content_type,
    }
    context = {
        "event": event.lower(),
        "timestamp": timestamp,
        "model": model_name,
        "username": username,
        "request_id": request_id,
        "data": data,
        "snapshots": snapshots,
    }
    params = {
        "method": webhook.http_method,
        "url": webhook.url,
        "headers": headers,
        "data": webhook.render_body(context).encode("utf8"),
    }

    logger.info(
        f"Sending {params['method']} request to {params['url']} ({model_name} {event})"
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

    if response.status_code == requests.codes.ok:
        logger.info(f"Request succeeded; response status {response.status_code}")
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
