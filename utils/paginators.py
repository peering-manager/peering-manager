from itertools import pairwise

from django.conf import settings
from django.core.paginator import Page, Paginator

__all__ = ("EnhancedPaginator", "get_paginate_count")


class EnhancedPaginator(Paginator):
    default_page_lengths = (25, 50, 100, 250, 500, 1000)

    def __init__(self, object_list, per_page, orphans=None, **kwargs):
        try:
            per_page = int(per_page)
            if per_page < 1:
                per_page = settings.PAGINATE_COUNT
        except ValueError:
            per_page = settings.PAGINATE_COUNT

        # Set orphans count based on page size
        if orphans is None:
            orphans = 5 if per_page <= 50 else 10

        super().__init__(object_list, per_page, orphans=orphans, **kwargs)

    def _get_page(self, *args, **kwargs):
        return EnhancedPage(*args, **kwargs)

    def get_page_lengths(self):
        if self.per_page not in self.default_page_lengths:
            return sorted([*self.default_page_lengths, self.per_page])
        return self.default_page_lengths


class EnhancedPage(Page):
    def smart_pages(self):
        # If less or 5 pages just display each page link
        if self.paginator.num_pages <= 5:
            return self.paginator.page_range

        # Show first page, last page, next/previous two pages, and current page
        n = self.number
        pages_wanted = [1, n - 2, n - 1, n, n + 1, n + 2, self.paginator.num_pages]
        pages_list = sorted(set(self.paginator.page_range).intersection(pages_wanted))

        # Skip markers
        skip_pages = [x[1] for x in pairwise(pages_list) if (x[1] - x[0] != 1)]
        for i in skip_pages:
            pages_list.insert(pages_list.index(i), False)

        return pages_list


def get_paginate_count(request):
    """
    Determines the number of items to display in one page, based on the following in
    order:
      1. `per_page` URL query parameter (saving it as user preference in the process)
      2. user preference
      3. `PAGINATE_COUNT` setting
    """
    if not request.user.is_authenticated:
        return (
            int(request.GET.get("per_page"))
            if "per_page" in request.GET
            else settings.PAGINATE_COUNT
        )

    if "per_page" in request.GET:
        try:
            per_page = int(request.GET.get("per_page"))
            request.user.preferences.set("pagination.per_page", per_page, commit=True)
            return per_page
        except ValueError:
            pass

    return request.user.preferences.get("pagination.per_page", settings.PAGINATE_COUNT)
