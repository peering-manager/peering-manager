"""
Views for managing Token Object Permissions via web UI.
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from peering_manager.views.generic import ObjectChildrenView

from .forms import TokenObjectPermissionForm
from .models import TokenObjectPermission
from .tables import TokenObjectPermissionTable
from .token_actions import get_available_actions


class ObjectTokenPermissionsView(ObjectChildrenView):
    """Display token permissions for a specific object."""

    permission_required = "users.view_tokenobjectpermission"
    template_name = "users/object_token_permissions.html"
    table = TokenObjectPermissionTable
    tab = "token_permissions"

    def get_children(self, request, parent):
        """Get all token permissions for this object."""
        content_type = ContentType.objects.get_for_model(parent)
        return TokenObjectPermission.objects.filter(
            content_type=content_type, object_id=parent.pk
        ).select_related("token", "token__user")

    def get_extra_context(self, request, instance):
        """Add context for creating new permissions."""
        return {
            "object": instance,
            "content_type": ContentType.objects.get_for_model(instance),
            "can_add": request.user.has_perm("users.add_tokenobjectpermission"),
        }


class TokenObjectPermissionAddView(PermissionRequiredMixin, View):
    """Create a new token object permission."""

    permission_required = "users.add_tokenobjectpermission"
    template_name = "users/tokenobjectpermission_add.html"

    def get(self, request, content_type_id, object_id):
        """Display the permission creation form."""
        content_type = get_object_or_404(ContentType, pk=content_type_id)
        model_class = content_type.model_class()
        obj = get_object_or_404(model_class, pk=object_id)

        # Get available actions for this model
        available_actions = get_available_actions(model_class)

        form = TokenObjectPermissionForm(available_actions=available_actions)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "instance": TokenObjectPermission(),
                "object": obj,
                "content_type": content_type,
                "return_url": obj.get_absolute_url() + "token-permissions/",
            },
        )

    def post(self, request, content_type_id, object_id):
        """Handle permission creation."""
        content_type = get_object_or_404(ContentType, pk=content_type_id)
        model_class = content_type.model_class()
        obj = get_object_or_404(model_class, pk=object_id)

        # Get available actions for this model
        available_actions = get_available_actions(model_class)

        form = TokenObjectPermissionForm(
            request.POST, available_actions=available_actions
        )

        if form.is_valid():
            permission = form.save(commit=False)
            permission.content_type = content_type
            permission.object_id = object_id
            permission.save()

            messages.success(
                request, f"Created token permission for {permission.token} on {obj}"
            )

            return redirect(obj.get_absolute_url() + "token-permissions/")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "instance": TokenObjectPermission(),  # For generic/edit.html
                "object": obj,
                "content_type": content_type,
                "return_url": obj.get_absolute_url() + "token-permissions/",
            },
        )


class TokenObjectPermissionEditView(PermissionRequiredMixin, View):
    """Edit an existing token object permission."""

    permission_required = "users.change_tokenobjectpermission"
    template_name = "users/tokenobjectpermission_edit.html"

    def get(self, request, pk):
        """Display the permission edit form."""
        permission = get_object_or_404(TokenObjectPermission, pk=pk)
        obj = permission.content_object

        # Get available actions for this model
        available_actions = get_available_actions(obj) if obj else {}

        form = TokenObjectPermissionForm(
            instance=permission, available_actions=available_actions
        )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "instance": permission,
                "permission": permission,
                "object": obj,
                "return_url": obj.get_absolute_url() + "token-permissions/"
                if obj
                else reverse("users:token_list"),
            },
        )

    def post(self, request, pk):
        """Handle permission update."""
        permission = get_object_or_404(TokenObjectPermission, pk=pk)
        obj = permission.content_object

        # Get available actions for this model
        available_actions = get_available_actions(obj) if obj else {}

        form = TokenObjectPermissionForm(
            request.POST, instance=permission, available_actions=available_actions
        )

        if form.is_valid():
            permission = form.save()

            messages.success(
                request, f"Updated token permission for {permission.token}"
            )

            obj = permission.content_object
            if obj:
                return redirect(obj.get_absolute_url() + "token-permissions/")
            return redirect("users:token_list")

        obj = permission.content_object

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "instance": permission,
                "permission": permission,
                "object": obj,
                "return_url": obj.get_absolute_url() + "token-permissions/"
                if obj
                else reverse("users:token_list"),
            },
        )


class TokenObjectPermissionDeleteView(PermissionRequiredMixin, View):
    """Delete a token object permission."""

    permission_required = "users.delete_tokenobjectpermission"
    template_name = "users/tokenobjectpermission_delete.html"

    def get(self, request, pk):
        """Display confirmation page."""
        permission = get_object_or_404(TokenObjectPermission, pk=pk)
        obj = permission.content_object

        return render(
            request,
            self.template_name,
            {
                "instance": permission,  # For generic templates
                "permission": permission,
                "object": obj,
                "return_url": obj.get_absolute_url() + "token-permissions/"
                if obj
                else reverse("users:token_list"),
            },
        )

    def post(self, request, pk):
        """Handle permission deletion."""
        permission = get_object_or_404(TokenObjectPermission, pk=pk)
        obj = permission.content_object
        token = permission.token

        permission.delete()

        messages.success(request, f"Deleted token permission for {token}")

        if obj:
            return redirect(obj.get_absolute_url() + "token-permissions/")
        return redirect("users:token_list")
