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

## LOGIN_REQUIRED

Default: `False`

Setting this to `True` will permit only authenticated users to access any part
of Peering Manager. By default, anonymous users are permitted to access most
data in Peering Manager but not make any changes.
