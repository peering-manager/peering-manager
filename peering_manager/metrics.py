from django_prometheus import middleware
from django_prometheus.conf import NAMESPACE
from prometheus_client import Counter

__all__ = ("Metrics",)


class Metrics(middleware.Metrics):
    """
    Custom Prometheus metrics middleware for Peering Manager.
    """

    def register(self):
        super().register()

        self.rest_api_requests = self.register_metric(
            Counter,
            "rest_api_requests_total_by_method",
            "Count of total REST API requests by method",
            ["method"],
            namespace=NAMESPACE,
        )
        self.rest_api_requests_by_view_by_method = self.register_metric(
            Counter,
            "rest_api_requests_total_by_view_method",
            "Count of total REST API requests by view and method",
            ["view", "method"],
            namespace=NAMESPACE,
        )
