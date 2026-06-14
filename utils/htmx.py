__all__ = ("htmx_partial",)


def htmx_partial(request) -> bool:
    """
    Return `True` when the request is an htmx request that is not a boosted page
    navigation. Use this to decide between rendering a partial fragment and a full
    page.
    """
    return bool(request.htmx) and not request.htmx.boosted
