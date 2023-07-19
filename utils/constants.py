FILTER_CHAR_BASED_LOOKUP_MAP = dict(
    n="exact",
    ic="icontains",
    nic="icontains",
    iew="iendswith",
    niew="iendswith",
    isw="istartswith",
    nisw="istartswith",
    ie="iexact",
    nie="iexact",
    empty="empty",
)

FILTER_NUMERIC_BASED_LOOKUP_MAP = dict(
    n="exact", lte="lte", lt="lt", gte="gte", gt="gt"
)

FILTER_NEGATION_LOOKUP_MAP = dict(n="exact")
