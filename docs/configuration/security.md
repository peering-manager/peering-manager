# Security & Authentication Parameters

## USE_X_FORWARDED_HOST

Default: `True`

Use the `X-Forwarded-Host` header in preference to the `Host` header. This
should only be enabled if a proxy which sets this header is in use.

---

## SECURE_PROXY_SSL_HEADER

Default: `("HTTP_X_FORWARDED_PROTO", "https")`

Parse defined header to let Django know that HTTPS is being used. This way
e.g. generated API URLs will have the corresponding `https://` prefix.

Use `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` to check
for `https` value in `X-Forwarded-Proto` header.

---

## CORS_ORIGIN_ALLOW_ALL

Default: `False`

If `True`, cross-origin resource sharing (CORS) requests will be accepted from
all origins. If `False`, a whitelist will be used (see below).

---

## CORS_ORIGIN_WHITELIST

## CORS_ORIGIN_REGEX_WHITELIST

These settings specify a list of origins that are authorized to make
cross-site API requests. Use `CORS_ORIGIN_WHITELIST` to define a list of exact
hostnames, or `CORS_ORIGIN_REGEX_WHITELIST` to define a set of regular
expressions. (These settings have no effect if `CORS_ORIGIN_ALLOW_ALL` is
`True`). For example:

```python
CORS_ORIGIN_WHITELIST = [
    'https://example.com',
]
```

---

## CSRF_COOKIE_NAME

Default: `csrftoken`

The name of the cookie to use for the cross-site request forgery (CSRF)
authentication token. See the
[Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-name)
for more detail.

---

## CSRF_COOKIE_SECURE

Default: `False`

If true, the cookie employed for cross-site request forgery (CSRF) protection
will be marked as secure, meaning that it can only be sent across an HTTPS
connection.

---

## CSRF_TRUSTED_ORIGINS

Default: `[]`

Defines a list of trusted origins for unsafe (e.g. `POST`) requests. This is a
pass-through to Django's
[`CSRF_TRUSTED_ORIGINS`](https://docs.djangoproject.com/en/4.0/ref/settings#std:setting-CSRF_TRUSTED_ORIGINS)
setting. Note that each host listed must specify a scheme (e.g. `http://` or
`https://`).

```python
CSRF_TRUSTED_ORIGINS = (
    'http://peering-manager.local',
    'https://peering-manager.local',
)
```

---

## LOGIN_PERSISTENCE

Default: `False`

If true, the lifetime of a user's authentication session will be automatically
reset upon each valid request. For example, if
[`LOGIN_TIMEOUT`](#login_timeout) is configured to 14 days (the default), and
a user whose session is due to expire in five days makes a Peering Manager
request (with a valid session cookie), the session's lifetime will be reset to
14 days.

Note that enabling this setting causes Peering Manager to update a user's
session in the database (or file, as configured per
[`SESSION_FILE_PATH`](#session_file_path)) with each request, which may
introduce significant overhead in very active environments. It also permits an
active user to remain authenticated to Peering Manager indefinitely.

---

## LOGIN_REQUIRED

Default: `False`

Setting this to `True` will permit only authenticated users to access any part
of Peering Manager. By default, anonymous users are permitted to access most
data in Peering Manager but not make any changes.

---

## LOGIN_TIMEOUT

Default: `1209600` seconds (2 weeks, in seconds)

The lifetime (in seconds) of the authentication cookie issued to a Peering
Manager user upon login. This setting is actually a wrapper around Django's
[`SESSION_COOKIE_AGE`](https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-age)

---

## LOGIN_FORM_HIDDEN

Default: `False`

When set to `True`, the login form will be hidden on the login page, keeping
only SSO authentication buttons available. This is useful when you want to
enforce SSO-only authentication and prevent users from logging in with
username/password credentials.

---

## SESSION_COOKIE_NAME

Default: `sessionid`

The name used for the session cookie. See the
[Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-name)
for more detail.

---

## SESSION_COOKIE_SECURE

Default: `False`

If true, the cookie employed for session authentication will be marked as
secure, meaning that it can only be sent across an HTTPS connection.

---

## SESSION_FILE_PATH

Default: None

HTTP session data is used to track authenticated users when they access
Peering Manager. By default, Peering Manager stores session data in its
PostgreSQL database. Alternatively, a local file path may be specified here
and Peering Manager will store session data as files instead of using the
database. Note that the Peering Manager system user must have read and write
permissions to this path.
