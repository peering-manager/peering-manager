from datetime import datetime, timezone

__all__ = ("BaseFilterSetTests", "ChangeLoggedFilterSetTests")


class BaseFilterSetTests:
    queryset = None
    filterset = None

    def test_id(self):
        """
        Test filtering for two PKs from a set of >2 objects.
        """
        params = {"id": self.queryset.values_list("pk", flat=True)[:2]}
        self.assertGreater(self.queryset.count(), 2)
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ChangeLoggedFilterSetTests(BaseFilterSetTests):
    def test_created(self):
        pk_list = self.queryset.values_list("pk", flat=True)[:2]
        self.queryset.filter(pk__in=pk_list).update(
            created=datetime(2021, 1, 1, tzinfo=timezone.utc)
        )
        params = {"created": "2021-01-01"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_updated(self):
        pk_list = self.queryset.values_list("pk", flat=True)[:2]
        self.queryset.filter(pk__in=pk_list).update(
            updated=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        params = {"updated": "2021-01-01T00:00:00"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
