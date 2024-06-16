from social_core.storage import NO_ASCII_REGEX, NO_SPECIAL_REGEX


def clean_username(value):
    """
    Clean username by removing unsupported characters.
    """
    return NO_SPECIAL_REGEX.sub("", NO_ASCII_REGEX.sub("", value)).replace(":", "")
