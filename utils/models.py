from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe


# User Actions Constants
USER_ACTION_CREATE = 1
USER_ACTION_EDIT = 2
USER_ACTION_DELETE = 3
USER_ACTION_IMPORT = 4
USER_ACTION_BULK_DELETE = 5
USER_ACTION_CHOICES = (
    (USER_ACTION_CREATE, 'created'),
    (USER_ACTION_EDIT, 'modified'),
    (USER_ACTION_DELETE, 'deleted'),
    (USER_ACTION_IMPORT, 'imported'),
    (USER_ACTION_BULK_DELETE, 'bulk deleted'),
)


class UserActionManager(models.Manager):
    """
    Manager for UserAction model.
    """

    def log_action(self, user, obj, action, message):
        self.model.objects.create(content_type=ContentType.objects.get_for_model(
            obj), object_id=obj.id, user=user, action=action, message=message)

    def log_bulk_action(self, user, obj_type, action, message):
        self.model.objects.create(content_type=ContentType.objects.get_for_model(
            obj_type), user=user, action=action, message=message)

    def log_bulk_delete(self, user, obj_type, message):
        self.log_bulk_action(user, obj_type, USER_ACTION_BULK_DELETE, message)

    def log_create(self, user, obj, message):
        self.log_action(user, obj, USER_ACTION_CREATE, message)

    def log_delete(self, user, obj, message):
        self.log_action(user, obj, USER_ACTION_DELETE, message)

    def log_edit(self, user, obj, message):
        self.log_action(user, obj, USER_ACTION_EDIT, message)

    def log_import(self, user, obj_type, message):
        self.log_bulk_action(user, obj_type, USER_ACTION_IMPORT, message)


class UserAction(models.Model):
    """
    A record of a user action (add/edit/delete/import).
    """
    time = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(
        User, related_name='actions', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    action = models.PositiveSmallIntegerField(choices=USER_ACTION_CHOICES)
    message = models.TextField(blank=True)

    objects = UserActionManager()

    class Meta:
        ordering = ['-time']

    def get_icon(self):
        """
        Return an HTML element based on the user action.
        """
        if self.action in [USER_ACTION_CREATE, USER_ACTION_IMPORT]:
            return mark_safe('<i class="fa fa-plus-square text-success"></i>')

        if self.action == USER_ACTION_EDIT:
            return mark_safe('<i class="fa fa-pencil-square text-warning"></i>')

        if self.action in [USER_ACTION_DELETE, USER_ACTION_BULK_DELETE]:
            return mark_safe('<i class="fa fa-minus-square text-danger"></i>')

        return ''

    def __str__(self):
        if self.message:
            return '{} {}'.format(self.user, self.message)

        return '{} {} {}'.format(self.user, self.get_action_display(), self.content_type)
