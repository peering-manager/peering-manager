import json


class MockedResponse(object):
    def __init__(self, status_code=200, ok=True, fixture=None, content=None):
        self.status_code = status_code
        if fixture:
            self.content = self.load_fixture(fixture)
        elif content:
            self.content = json.dumps(content)
        else:
            self.content = None
        self.ok = ok

    def load_fixture(self, path):
        with open(path, "r") as f:
            return f.read()

    def json(self):
        return json.loads(self.content)
