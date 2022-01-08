from django import forms
from taggit.forms import TagField

from messaging.models import Contact, ContactAssignment, ContactRole, Email
from utils.fields import CommentField, SlugField, TemplateField
from utils.forms import (
    AddRemoveTagsForm,
    BootstrapMixin,
    BulkEditForm,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    SmallTextarea,
    TagFilterField,
)

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


class ContactRoleForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    tags = TagField(required=False)

    class Meta:
        model = ContactRole
        fields = ["name", "slug", "description", "tags"]


class ContactRoleBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=ContactRole.objects.all(), widget=forms.MultipleHiddenInput
    )
    description = forms.CharField(max_length=200, required=False)

    class Meta:
        model = ContactRole
        nullable_fields = ["description"]


class ContactRoleFilterForm(BootstrapMixin, forms.Form):
    model = ContactRole
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class ContactForm(BootstrapMixin, forms.ModelForm):
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Contact
        fields = ["name", "title", "phone", "email", "address", "comments", "tags"]
        widgets = {"address": SmallTextarea(attrs={"rows": 3})}


class ContactBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(), widget=forms.MultipleHiddenInput
    )
    title = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=200, required=False)

    class Meta:
        model = Contact
        nullable_fields = ["title", "phone", "email", "address"]


class ContactFilterForm(BootstrapMixin, forms.Form):
    model = Contact
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class ContactAssignmentForm(BootstrapMixin, forms.ModelForm):
    contact = DynamicModelChoiceField(queryset=Contact.objects.all())
    role = DynamicModelChoiceField(queryset=ContactRole.objects.all())

    class Meta:
        model = ContactAssignment
        fields = ("contact", "role")


class EmailForm(BootstrapMixin, forms.ModelForm):
    subject = forms.CharField(
        help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported'
    )
    template = TemplateField(label="Body")
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Email
        fields = (
            "name",
            "subject",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        )


class EmailFilterForm(BootstrapMixin, forms.Form):
    model = Email
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)
