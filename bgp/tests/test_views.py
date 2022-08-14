from bgp.models import Relationship
from utils.enums import Colour
from utils.testing import ViewTestCases


class RelationshipTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Relationship

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
                Relationship(name="Test2", slug="test2", color=Colour.WHITE),
                Relationship(name="Test3", slug="test3", color=Colour.BLACK),
            ]
        )

        cls.form_data = {"name": "Test4", "slug": "test4", "color": Colour.RED}
        cls.bulk_edit_data = {"description": "Foo"}
