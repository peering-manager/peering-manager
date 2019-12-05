from django.db import transaction
from django.urls.exceptions import NoReverseMatch

from utils.models import Tag

from utils.tests import ViewTestCase


class TagTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = Tag
        self.name = "Test"
        self.slug = "test"
        self.tag = Tag.objects.create(name=self.name, slug=self.slug)

    def test_tag_list_view(self):
        self.get_request("utils:tag_list", data={"q": "test"})

    def test_tag_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("utils:tag_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("utils:tag_add", contains="Create")

        # Try to create an object with valid data
        tag_to_create = {
            "name": "tag-created",
            "slug": "tag-created",
            "color": "000000",
        }
        self.post_request("utils:tag_add", data=tag_to_create)
        self.does_object_exist(tag_to_create)

        # Try to create an object with invalid data
        tag_not_to_create = {"name": "tag-notcreated"}
        self.post_request("utils:tag_add", data=tag_not_to_create)
        self.does_object_not_exist(tag_not_to_create)

    def test_tag_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("utils:tag_bulk_delete", expected_status_code=302)

    def test_tag_details_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("utils:tag_details")

        # Using a wrong slug, status should be 404 not found
        self.get_request(
            "utils:tag_details", params={"slug": "not-found"}, expected_status_code=404
        )

        # Using an existing slug, status should be 200 and the name of the tag
        # should be somewhere in the HTML code
        self.get_request(
            "utils:tag_details", params={"slug": self.slug}, contains=self.name
        )

    def test_tag_edit_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("utils:tag_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "utils:tag_edit", params={"slug": self.slug}, expected_status_code=302
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "utils:tag_edit", params={"slug": self.slug}, contains="Update"
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "utils:tag_edit", params={"slug": "not-found"}, expected_status_code=404
        )

    def test_tag_delete_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("utils:tag_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "utils:tag_delete", params={"slug": self.slug}, expected_status_code=302
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "utils:tag_delete", params={"slug": self.slug}, contains="Confirm"
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "utils:tag_delete", params={"slug": "not-found"}, expected_status_code=404
        )
