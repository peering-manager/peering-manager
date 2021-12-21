from django import forms

from utils.forms import BootstrapMixin


class SearchForm(BootstrapMixin, forms.Form):
    q = forms.CharField(label="Search")
