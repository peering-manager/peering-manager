# Miscellaneous Parameters

## ADMINS

Peering Manager will email details about critical errors to the administrators
listed here. This should be a list of (name, email) tuples. For example:

```python
ADMINS = [
    ['Tony Stark', 'ironman@example.com'],
    ['Steve Rogers', 'captain@example.com'],
]
```

---

## BANNER_LOGIN

This defines custom content to be displayed on the login page above the login
form. HTML is allowed.

---

### CENSUS_REPORTING_ENABLED

Default: `True`

Enables anonymous census reporting. To opt out, set this to `False`.

This data enables the project maintainer to estimate how many Peering Manager
deployments exist and track adoption of new versions over times.

Census reporting performs a single HTTP POST request each time a worker
starts.

The reported data includes:

* Pseudorandom unique identifier
* Peering Manager version
* Python version

---

## CHANGELOG_RETENTION

Default: `90`

The number of days to retain logged changes (object creations, updates, and
deletions). Set this to `0` to retain changes in the database indefinitely.

!!! warning
    If enabling indefinite changelog retention, it is recommended to
    periodically delete old entries. Otherwise, the database may eventually
    exceed capacity.

---

## JOB_RETENTION

!!! note
    This parameter was renamed from `JOBRESULT_RETENTION` in Peering Manager
    v1.8.

Default: `90`

The number of days to retain job results. Set this to `0` to retain job
results in the database indefinitely.

!!! warning
    If enabling indefinite job results retention, it is recommended to
    periodically delete old entries. Otherwise, the database may eventually
    exceed capacity.

---

## MAX_PAGE_SIZE

Default: `1000`

A web user or API consumer can request an arbitrary number of objects by
appending the "limit" parameter to the URL (e.g. `?limit=1000`). This
parameter defines the maximum acceptable limit. Setting this to `0` or `None`
will allow a client to retrieve _all_ matching objects at once with no limit
by specifying `?limit=0`.

---

## PAGINATE_COUNT

Default: `20`

Determine how many objects to display per page within each list of objects.

---

## METRICS_ENABLED

Default: `False`

Toggle the availability Prometheus-compatible metrics at `/metrics`. See the
[Prometheus Metrics](../integrations/prometheus-metrics.md) documentation for
more details.

---

## RELEASE_CHECK_URL

Default: official Peering Manager URL

This parameter defines the URL of the repository that will be checked for new
Peering Manager releases. When a new release is detected, a message will be
displayed to administrative users on the home page. This can be set to the
official repository
(`'https://api.github.com/repos/peering-manager/peering-manager/releases'`) or
a custom fork. Set this to `None` to disable automatic update checks.

!!! note
    The URL provided **must** be compatible with the
    [GitHub REST API](https://docs.github.com/en/rest).

---

## RQ_DEFAULT_TIMEOUT

Default: `300`

The maximum execution time of a background task (such as running a PeeringDB
synchronisation), in seconds.

---

## GIT_COMMIT_AUTHOR

Default: `"Peering Manager <no-reply@peering-manager.net>"`

Git commit author that will be used when committing changes in Git
repositories when used as data sources. It must be compliant with the Git
format.

---

## GIT_COMMIT_MESSAGE

Default: `"Committed using Peering Manager"`

Message to log in commits that will be performed using Peering Manager in Git
repositories when used as data sources.

---

## VALIDATE_BGP_COMMUNITY_VALUE

Default: `True`

Perform validation for of the value when creating or updating a BGP community.
This ensures that a value is a valid standard, extended or large community.
This validation can be disabled if Peering Manager enforced notations do not
fit the user needs.
