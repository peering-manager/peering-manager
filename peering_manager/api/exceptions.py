from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, please try again later."


class UnprocessableRequest(APIException):
    status_code = 422
    default_detail = "The request cannot be processed in the current state."


class SerializerNotFoundError(Exception):
    pass
