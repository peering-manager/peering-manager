# System Parameters

## BASE_PATH

Default: `None`

The base URL path to use when accessing Peering Manager. Do not include the
scheme or domain name. For example, if installed at
`https://example.com/peering/`, set:

```python
BASE_PATH = 'peering/'
```

---

## EMAIL

In order to send email, Peering Manager needs an email server configured. The
following items can be defined within the `EMAIL` configuration parameter:

* `SERVER` - Hostname or IP address of the email server
  (use `localhost` if running locally)
* `PORT` - TCP port to use for the connection (default: `25`)
* `USERNAME` - Username with which to authenticate
* `PASSWORD` - Password with which to authenticate
* `USE_SSL` - Use SSL when connecting to the server (default: `False`)
* `USE_TLS` - Use TLS when connecting to the server (default: `False`)
* `SSL_CERTFILE` - Path to the PEM-formatted SSL certificate file (optional)
* `SSL_KEYFILE` - Path to the PEM-formatted SSL private key file (optional)
* `TIMEOUT` - Amount of time to wait for a connection, in seconds
  (default: `10`)
* `FROM_ADDRESS` - Sender address for emails sent by Peering Manager
* `CC_CONTACTS` - Carbon copy contacts when sending emails. This should be a
  list of (email, name) tuples like:
  `[("noc@example.com", "NOC"), ("netops@example.com", "NetOps Team")]`

!!! note
    The `USE_SSL` and `USE_TLS` parameters are mutually exclusive.

Email is sent from Peering Manager only for critical events or if configured
for [logging](#logging). If you would like to test the email server
configuration, Django provides a convenient
[send_mail()](https://docs.djangoproject.com/en/stable/topics/email/#send-mail)
function accessible within the Peering Manager shell:

```no-highlight
# python ./manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
  'Test Email Subject',
  'Test Email Body',
  'noreply-peeringmanager@example.com',
  ['users@example.com'],
  fail_silently=False
)
```

---

## HTTP_PROXIES

Default: None

A dictionary of HTTP proxies to use for outbound requests originating from
Peering Manager (e.g. when sending webhook requests). Proxies should be
specified by schema (HTTP and HTTPS) as per the
[Python requests library documentation](https://requests.readthedocs.io/en/latest/user/advanced/#proxies).
For example:

```python
HTTP_PROXIES = {
    'http': 'http://10.10.1.10:3128',
    'https': 'http://10.10.1.10:1080',
}
```

---

## REQUESTS_USER_AGENT

Default: "PeeringManager/x.y"

User agent that Peering Manager will use when making requests to external
HTTP resources. It should not require to be changed unless you have issues
with specific HTTP endpoints.

---

## INTERNAL_IPS

Default: `('127.0.0.1', '::1')`

A list of IP addresses recognized as internal to the system, used to control
the display of debugging output. For example, the debugging toolbar will be
viewable only when a client is accessing NetBox from one of the listed IP
addresses (and `DEBUG` is true).

---

## LOGGING

By default, all messages of INFO severity or higher will be logged to the
console. Additionally, if `DEBUG` is false and email access has been
configured, ERROR and CRITICAL messages will be emailed to the users defined
in `ADMINS`.

The Django framework on which Peering Manager runs allows for the
customisation of logging format and destination. Please consult the
[Django logging documentation](https://docs.djangoproject.com/en/stable/topics/logging/)
for more information on configuring this setting. Below is an example which
will write all INFO and higher messages to a local file:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/peering-manager.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Available Loggers

* `peering.manager.<app>` - Generic form for app-specific log messages
* `peering.manager.auth.*` - Authentication events
* `peering.manager.api.views.*` - Views which handle logic for the REST API
* `peering.manager.napalm` - NAPALM operations
* `peering.manager.views.*` - Views which handle logic for the web UI

---

## JINJA2_TEMPLATE_EXTENSIONS

Default: `[]`

List of Jinja2 extensions to load when rendering templates. Extensions can be
used to add more features to the initial ones. Extensions that are not built
into Jinja2 need to be installed in the Python environment used to run Peering
Manager.

Example:

```no-highlight
JINJA2_TEMPLATE_EXTENSIONS = [
  "jinja2.ext.debug",
  "jinja2.ext.do",
]
```

---

## CONFIG_CONTEXT_RECURSIVE_MERGE / CONFIG_CONTEXT_LIST_MERGE

Default: `True` / `replace`

When merging configuration contexts, Peering Manager needs to know what should
happen to nested dictionaries/hashes and to list. These two options can be
changed to reproduce the wanted behaviour. They are similar to Ansible's
`combine` filter and should produce the same results.

Keep in mind that config contexts are merged in a way that one that has a high
priority will override one with a lower priority.

If `CONFIG_CONTEXT_RECURSIVE_MERGE` is set to `True` (the default value), it
will recursively merge nested hashes.

`CONFIG_CONTEXT_LIST_MERGE` has multiple values possible:
* `replace`: default, arrays in the higher priority config context will
  replace the ones in lower priority config context,
* `keep`: arrays in the lower priority config context will be kept,
* `append`: arrays in the higher priority config context will be appended to
  the ones in the lower priority config context,
* `prepend`: arrays in the higher priority config context will be prepended to
  the ones in the lower priority config context,
* `append_rp`: arrays in the higher priority config context will be appended
  to the ones in the lower priority config context, elements of arrays in that
  are in both config contextes will be removed ("rp" stands for "remove
  present"), duplicate elements that aren’t in both config contexts are kept,
* `prepend_rp`: the behavior is similar to the one for `append_rp`, but
  elements of arrays are prepended.
