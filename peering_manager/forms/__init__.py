from django import forms

from utils.forms import BootstrapMixin

from .base import *


class SearchForm(BootstrapMixin, forms.Form):
    q = forms.CharField(label="Search")
