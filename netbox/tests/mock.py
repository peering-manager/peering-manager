import json


class MockedResponse(object):
    def __init__(self, status_code=200, ok=True, fixture=None, content=None):
        if not fixture and not content:
            raise ValueError(
                "Either fixture or content should be set to a non-None value."
            )

        self.status_code = status_code
        self.content = json.dumps(content) if content else self.load_fixture(fixture)
        self.ok = ok

    def load_fixture(self, path):
        with open(path, "r") as f:
            return f.read()

    def json(self):
        return json.loads(self.content)
