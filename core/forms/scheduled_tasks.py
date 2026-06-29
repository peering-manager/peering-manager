from django import forms

from peering_manager.jobs import scheduled_task_registry
from utils.forms.mixins import BootstrapMixin
from utils.forms.widgets import StaticSelect

from ..models import ScheduledTask

__all__ = ("ScheduledTaskForm",)


class ScheduledTaskForm(BootstrapMixin, forms.ModelForm):
    task = forms.ChoiceField(
        widget=StaticSelect,
        help_text="Task to schedule. The list is the set of tasks Peering Manager can run.",
    )

    class Meta:
        model = ScheduledTask
        fields = ("task", "enabled", "interval")
        help_texts = {"interval": "Recurrence interval, in minutes."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        catalog = scheduled_task_registry()

        if self.instance.pk:
            label = catalog.get(self.instance.task, {}).get("label", self.instance.task)
            self.fields["task"].choices = [(self.instance.task, label)]
            self.fields["task"].disabled = True
        else:
            # Offer only catalog tasks without a schedule yet
            configured = set(ScheduledTask.objects.values_list("task", flat=True))
            self.fields["task"].choices = [
                (key, meta["label"]) for key, meta in catalog.items() if key not in configured
            ]
