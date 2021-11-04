import json
import logging
import re
from contextlib import contextmanager


@contextmanager
def disable_warnings(logger_name):
    """
    Suppresses expected warning messages to keep the test output clean.
    """
    logger = logging.getLogger(logger_name)
    current_level = logger.level
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(current_level)


def extract_form_failures(html):
    """
    Given raw HTML content from an HTTP response, returns a list of form errors.
    """
    FORM_ERROR_REGEX = r"<!-- FORM-ERROR (.*) -->"
    return re.findall(FORM_ERROR_REGEX, str(html))


def json_file_to_python_type(filename):
    with open(filename, mode="r") as f:
        return json.load(f)


def post_data(data):
    """
    Takes a dictionary of test data and returns a dict suitable for POSTing.
    """
    r = {}

    for key, value in data.items():
        if value is None:
            r[key] = ""
        elif type(value) in (list, tuple):
            if value and hasattr(value[0], "pk"):
                # Value is a list of instances
                r[key] = [v.pk for v in value]
            else:
                r[key] = value
        elif hasattr(value, "pk"):
            # Value is an instance
            r[key] = value.pk
        else:
            r[key] = str(value)

    return r
