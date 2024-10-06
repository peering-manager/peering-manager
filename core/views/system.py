import platform

from django import __version__ as django_version
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import ProgrammingError, connection
from django.shortcuts import render
from django.views.generic import View
from django_rq.queues import get_connection
from rq.worker import Worker

__all__ = ("SystemView",)


class SystemView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        psql_version = db_name = db_size = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                psql_version = cursor.fetchone()[0]
                psql_version = psql_version.split("(")[0].strip()
                cursor.execute("SELECT current_database()")
                db_name = cursor.fetchone()[0]
                cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db_name}'))")
                db_size = cursor.fetchone()[0]
        except (ProgrammingError, IndexError):
            pass
        stats = {
            "peering_manager_release": settings.VERSION,
            "python_version": platform.python_version(),
            "django_version": django_version,
            "postgresql_version": psql_version,
            "database_name": db_name,
            "database_size": db_size,
            "rq_worker_count": Worker.count(get_connection("default")),
        }

        return render(request, "core/system.html", {"stats": stats})
