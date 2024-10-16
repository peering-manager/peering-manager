from django import forms
from django.core.exceptions import ValidationError
from taggit.forms import TagField

from core.forms import SynchronisedDataMixin
from peering_manager.forms import (
    PeeringManagerModelBulkEditForm,
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms import BootstrapMixin
from utils.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    SlugField,
    TagFilterField,
    TemplateField,
)

from .models import Contact, ContactAssignment, ContactRole, Email

__all__ = (
    "ContactForm",
    "ContactBulkEditForm",
    "ContactFilterForm",
    "ContactRoleForm",
    "ContactRoleBulkEditForm",
    "ContactRoleFilterForm",
    "ContactAssignmentForm",
    "EmailForm",
    "EmailFilterForm",
)


class ContactRoleForm(PeeringManagerModelForm):
    slug = SlugField()
    tags = TagField(required=False)
    fieldsets = (("Role", ("name", "slug", "description")),)

    class Meta:
        model = ContactRole
        fields = ["name", "slug", "description", "tags"]


class ContactRoleBulkEditForm(PeeringManagerModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False)

    model = ContactRole
    nullable_fields = ("description",)


class ContactRoleFilterForm(PeeringManagerModelFilterSetForm):
    model = ContactRole
    tag = TagFilterField(model)


class ContactForm(PeeringManagerModelForm):
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (("Contact", ("name", "title", "phone", "email", "address")),)

    class Meta:
        model = Contact
        fields = [
            "name",
            "title",
            "phone",
            "email",
            "address",
            "description",
            "comments",
            "tags",
        ]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class ContactBulkEditForm(PeeringManagerModelBulkEditForm):
    title = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=200, required=False)

    model = Contact
    nullable_fields = ("title", "phone", "email", "address")


class ContactFilterForm(PeeringManagerModelFilterSetForm):
    model = Contact
    tag = TagFilterField(model)


class ContactAssignmentForm(BootstrapMixin, forms.ModelForm):
    contact = DynamicModelChoiceField(queryset=Contact.objects.all())
    role = DynamicModelChoiceField(queryset=ContactRole.objects.all())
    # fieldsets not here, overriden in template

    class Meta:
        model = ContactAssignment
        fields = ("contact", "role")


class EmailForm(PeeringManagerModelForm, SynchronisedDataMixin):
    subject = forms.CharField(
        help_text='<i class="fa-fw fa-solid fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported'
    )
    template = TemplateField(required=False, label="Body")
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        ("E-mail", ("name", "subject", "jinja2_trim", "jinja2_lstrip", "template")),
        ("Data Source", ("data_source", "data_file", "auto_synchronisation_enabled")),
    )

    class Meta:
        model = Email
        fields = (
            "name",
            "subject",
            "jinja2_trim",
            "jinja2_lstrip",
            "template",
            "data_source",
            "data_file",
            "auto_synchronisation_enabled",
        )

    def clean(self):
        if not self.cleaned_data["template"] and not self.cleaned_data["data_file"]:
            raise ValidationError(
                "Either the template code or a file from a data source must be provided"
            )
        return super().clean()


class EmailFilterForm(BootstrapMixin, forms.Form):
    model = Email
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)
