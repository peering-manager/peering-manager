This guide explains how to implement Prometheus metrics.

# Requirements

## Install django-prometheus

```
# pip3 install -r requirements_prometheus.txt
```

# Configuration

Add `METRICS_ENABLED=True` to your `configuration.py`.

## Prometheus Configuration

Django-prometheus is tightly coupled with the application code, therefore
no configuration is exposed at this time.

## Prometheus metrics

If `METRICS_ENABLED` is set to `True`, metrics are exposed at the `/metrics`
 endpoint.
