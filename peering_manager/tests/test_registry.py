from django.test import TestCase

from peering_manager.registry import Registry


class RegistryTest(TestCase):
    def test_set_store(self):
        r = Registry({"foo": 123})
        with self.assertRaises(TypeError):
            r["bar"] = 456

    def test_mutate_store(self):
        r = Registry({"foo": [1, 2]})
        r["foo"].append(3)
        self.assertListEqual(r["foo"], [1, 2, 3])

    def test_delete_store(self):
        r = Registry({"foo": 123})
        with self.assertRaises(TypeError):
            del r["foo"]
