from django.conf import settings
from django.urls import resolve


class LastSearchMiddleware(object):
    """
    Registers the last search done by a user in a session variable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set last search path if the user just performed a search (query string not
        # empty), this variable will last all the session life time
        if (request.path_info != settings.LOGIN_URL) and request.META["QUERY_STRING"]:
            request.session["last_search"] = "{}?{}".format(
                request.path_info, request.META["QUERY_STRING"]
            )

        return self.get_response(request)
