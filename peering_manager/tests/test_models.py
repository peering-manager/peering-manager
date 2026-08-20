from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps

from core.constants import CENSORSHIP_STRING, CENSORSHIP_STRING_CHANGED
from core.enums import ObjectChangeAction
from peering_manager.models import ChangeLoggedModel


@isolate_apps("peering_manager")
class CensoredFieldsTest(TestCase):
    """
    Behaviour of `changelog_censored_fields`, without a concrete model of the project.
    """

    def build(self, *censored):
        class Thing(ChangeLoggedModel):
            secret = models.CharField(max_length=10)
            changelog_censored_fields = list(censored)

            class Meta:
                app_label = "peering_manager"

        return Thing()

    def test_a_model_without_censored_fields_keeps_its_data(self):
        before, after = self.build().censor_data({"secret": "old"}, {"secret": "new"})

        self.assertEqual({"secret": "old"}, before)
        self.assertEqual({"secret": "new"}, after)

    def test_a_new_value_is_marked_as_changed(self):
        before, after = self.build("secret").censor_data({"secret": "old"}, {"secret": "new"})

        self.assertEqual(CENSORSHIP_STRING, before["secret"])
        self.assertEqual(CENSORSHIP_STRING_CHANGED, after["secret"])

    def test_an_unchanged_value_is_hidden_without_a_mark(self):
        before, after = self.build("secret").censor_data({"secret": "same"}, {"secret": "same"})

        self.assertEqual(CENSORSHIP_STRING, before["secret"])
        self.assertEqual(CENSORSHIP_STRING, after["secret"])

    def test_the_data_it_reads_stays_untouched(self):
        prechange = {"secret": "old"}
        postchange = {"secret": "new"}

        self.build("secret").censor_data(prechange, postchange)

        # A caller must still be able to tell whether the field changed
        self.assertEqual({"secret": "old"}, prechange)
        self.assertEqual({"secret": "new"}, postchange)

    def test_a_creation_and_a_deletion_are_handled(self):
        thing = self.build("secret")

        self.assertEqual((None, {"secret": CENSORSHIP_STRING_CHANGED}), thing.censor_data(None, {"secret": "new"}))
        self.assertEqual(({"secret": CENSORSHIP_STRING}, None), thing.censor_data({"secret": "old"}, None))

    def test_a_field_the_data_does_not_carry_is_ignored(self):
        before, after = self.build("secret", "absent").censor_data({}, {"other": "value"})

        self.assertEqual({}, before)
        self.assertEqual({"other": "value"}, after)

    def test_a_change_hides_the_value_but_keeps_the_snapshot(self):
        thing = self.build("secret")
        thing.secret = "old"
        thing.snapshot()
        thing.secret = "new"

        object_change = thing.to_objectchange(ObjectChangeAction.UPDATE)

        self.assertEqual(CENSORSHIP_STRING, object_change.prechange_data["secret"])
        self.assertEqual(CENSORSHIP_STRING_CHANGED, object_change.postchange_data["secret"])
        # Censoring a change must not censor the snapshot it reads
        self.assertEqual("old", thing._prechange_snapshot["secret"])
