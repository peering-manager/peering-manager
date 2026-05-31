from urllib.parse import urlsplit

from django.http import HttpResponse
from django.urls import reverse

__all__ = (
    "htmx_current_url",
    "htmx_maybe_redirect_current_page",
    "htmx_partial",
)


def htmx_partial(request) -> bool:
    """
    Return `True` when the request is an htmx request that is not a boosted page
    navigation. Use this to decide between rendering a partial fragment and a full
    page.
    """
    return bool(request.htmx) and not request.htmx.boosted


def htmx_current_url(request) -> str:
    """
    Return the URL of the page that initiated the htmx request, as carried by the
    `HX-Current-URL` header. Returns an empty string when absent.
    """
    return (
        request.headers.get("HX-Current-URL")
        or request.META.get("HTTP_HX_CURRENT_URL", "")
        or ""
    )


def htmx_maybe_redirect_current_page(
    request, url_name: str, *, preserve_query: bool = True, status: int = 200
) -> HttpResponse | None:
    """
    If the request is an htmx partial whose current URL matches the path of the named
    view, return an `HX-Redirect` response that sends the browser back to that page
    (preserving its query string by default). Otherwise return `None` so the caller
    can render its own response.
    """
    if not htmx_partial(request):
        return None

    current = urlsplit(htmx_current_url(request))
    target_path = reverse(url_name)

    if current.path.rstrip("/") != target_path.rstrip("/"):
        return None

    redirect_to = target_path
    if preserve_query and current.query:
        redirect_to = f"{target_path}?{current.query}"

    response = HttpResponse(status=status)
    response["HX-Redirect"] = redirect_to
    return response
