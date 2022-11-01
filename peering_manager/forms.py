from django import forms
from django.forms.formsets import BaseFormSet

from utils.forms import BootstrapMixin


class SearchForm(BootstrapMixin, forms.Form):
    q = forms.CharField(label="Search")


class HiddenControlFormSet(BaseFormSet):
    deletion_widget = forms.widgets.HiddenInput
