from __future__ import unicode_literals

from django.conf import settings
from django.http import HttpResponseRedirect


class RequireLoginMiddleware(object):
    """
    Redirect all non-authenticated user to the login page if the LOGIN_REQUIRED
    setting has been set to true.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            if request.path_info != settings.LOGIN_URL:
                return HttpResponseRedirect(
                    '{}?next={}'.format(settings.LOGIN_URL, request.path_info))

        return self.get_response(request)
