from utils.enums import ChoiceSet

WEBHOOK_HTTP_CONTENT_TYPE_JSON = "application/json"

EXTRAS_FEATURES = (
    "config-contexts",
    "export-templates",
    "jobs",
    "journaling",
    "synchronised_data",
    "tags",
    "webhooks",
)


class HttpMethod(ChoiceSet):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

    CHOICES = (
        (GET, "GET"),
        (POST, "POST"),
        (PUT, "PUT"),
        (PATCH, "PATCH"),
        (DELETE, "DELETE"),
    )


class JournalEntryKind(ChoiceSet):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"

    CHOICES = [
        (INFO, "Info"),
        (SUCCESS, "Success"),
        (WARNING, "Warning"),
        (DANGER, "Danger"),
    ]
