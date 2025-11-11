from django.forms.widgets import DateTimeInput

__all__ = ("DateTimePicker",)


class DateTimePicker(DateTimeInput):
    template_name = "widgets/datetime.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "datetime-picker"
        self.attrs["placeholder"] = "YYYY-MM-DD hh:mm"
