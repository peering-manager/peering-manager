from utils.enums import ChoiceSet

WEBHOOK_HTTP_CONTENT_TYPE_JSON = "application/json"

EXTRAS_FEATURES = ("config-contexts", "export-templates", "tags")


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
