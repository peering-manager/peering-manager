PREFIXES6 = '{"prefix_list": [{"prefix": "2001:db8::/32", "exact": true}]}'
PREFIXES4 = '{"prefix_list": [{"prefix": "203.0.113.0/24", "exact": true}]}'


def mocked_subprocess_popen(*args, **kwargs):
    class MockResponse:
        def __init__(self, returncode, out, err):
            self.returncode = returncode
            self.out = out
            self.err = err

        def communicate(self):
            return self.out, self.err

    if "AS-MOCKED" in args[0] or "AS65537" in args[0]:
        if "-6" in args[0]:
            return MockResponse(0, PREFIXES6.encode(), "".encode())
        if "-4" in args[0]:
            return MockResponse(0, PREFIXES4.encode(), "".encode())
    if "AS-ERROR" in args[0]:
        return MockResponse(1, "".encode(), "Exit with error".encode())

    return MockResponse(-1, "".encode(), "Something went wrong".encode())
