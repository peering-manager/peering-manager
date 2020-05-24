from django.conf import settings
from django.core.paginator import Paginator, Page


class EnhancedPaginator(Paginator):
    def __init__(self, object_list, per_page, **kwargs):
        if not isinstance(per_page, int) or per_page < 1:
            per_page = settings.PAGINATE_COUNT
        super().__init__(object_list, per_page, **kwargs)

    def _get_page(self, *args, **kwargs):
        return EnhancedPage(*args, **kwargs)


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
        skip_pages = [
            x[1] for x in zip(pages_list[:-1], pages_list[1:]) if (x[1] - x[0] != 1)
        ]
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
    if "per_page" in request.GET:
        try:
            per_page = int(request.GET.get("per_page"))
            request.user.preferences.set("pagination.per_page", per_page, commit=True)
            return per_page
        except ValueError:
            pass

    return request.user.preferences.get("pagination.per_page", settings.PAGINATE_COUNT)
