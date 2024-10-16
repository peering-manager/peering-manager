__all__ = ("add_blank_choice", "get_field_value")


def add_blank_choice(choices):
    """
    Add a blank choice to the beginning of a choices list.
    """
    return ((None, "---------"), *tuple(choices))


def get_field_value(form, field_name):
    """
    Return the bound or initial value for a form field, before calling the `clean()`
    method of the form.
    """
    field = form.fields[field_name]

    if (
        form.is_bound
        and (data := form.data.get(field_name))
        and hasattr(field, "valid_value")
        and field.valid_value(data)
    ):
        return data

    return form.get_initial_for_field(field, field_name)
