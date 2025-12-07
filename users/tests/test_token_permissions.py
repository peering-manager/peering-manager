"""
Comprehensive Tests for Token Object Permissions with API Integration
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from devices.models import Platform, Router
from peering.models import AutonomousSystem
from users.models import Token, TokenObjectPermission


class TokenObjectPermissionModelTestCase(TestCase):
    """Test TokenObjectPermission model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.token = Token.objects.create(user=self.user, description="Test token")

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router = Router.objects.create(
            local_autonomous_system=self.asn,
            name="router1",
            hostname="router1.example.com",
            platform=self.platform,
        )

    def test_create_token_permission(self):
        """Test creating a token object permission"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
        )

        self.assertEqual(permission.token, self.token)
        self.assertEqual(permission.object_id, self.router.pk)
        self.assertTrue(permission.can_view)
        self.assertFalse(permission.can_edit)
        self.assertFalse(permission.can_delete)

    def test_has_permission_crud_actions(self):
        """Test has_permission method for CRUD actions"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
        )

        # Test view actions
        self.assertTrue(permission.has_permission("retrieve"))
        self.assertTrue(permission.has_permission("list"))

        # Test edit actions
        self.assertFalse(permission.has_permission("update"))
        self.assertFalse(permission.has_permission("partial_update"))
        self.assertFalse(permission.has_permission("create"))

        # Test delete actions
        self.assertFalse(permission.has_permission("destroy"))

    def test_has_permission_custom_actions(self):
        """Test has_permission method for custom actions"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=True,
            can_delete=True,
            custom_actions={
                "configure": True,
                "configuration": True,
                "poll_bgp_sessions": False,
                "test_napalm_connection": True,
            },
        )

        # Test allowed custom actions
        self.assertTrue(permission.has_permission("configure"))
        self.assertTrue(permission.has_permission("configuration"))
        self.assertTrue(permission.has_permission("test_napalm_connection"))

        # Test denied custom actions
        self.assertFalse(permission.has_permission("poll_bgp_sessions"))

        # Test unset custom actions (should default to False)
        self.assertFalse(permission.has_permission("push_datasource"))
        self.assertFalse(permission.has_permission("unknown_action"))

    def test_set_custom_action(self):
        """Test setting custom action permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
        )

        permission.set_custom_action("configure", True)
        permission.set_custom_action("poll_bgp_sessions", False)
        permission.save()

        self.assertTrue(permission.custom_actions["configure"])
        self.assertFalse(permission.custom_actions["poll_bgp_sessions"])

    def test_unique_constraint(self):
        """Test unique constraint on token/content_type/object_id"""
        from django.db import IntegrityError

        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
        )

        with self.assertRaises(IntegrityError):
            TokenObjectPermission.objects.create(
                token=self.token,
                content_type=content_type,
                object_id=self.router.pk,
            )

    def test_string_representation(self):
        """Test __str__ method"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.token,
            content_type=content_type,
            object_id=self.router.pk,
        )

        str_repr = str(permission)
        self.assertIn("router", str_repr.lower())
        self.assertIn(str(self.router.pk), str_repr)


class TokenObjectPermissionAPITestCase(TestCase):
    """Test Token Object Permission API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_staff = True
        self.user.is_superuser = True  # Grant all permissions for API tests
        self.user.save()
        self.admin_token = Token.objects.create(
            user=self.user,
            description="Admin token",
            write_enabled=True,
            can_manage_permissions=True,
        )
        self.restricted_token = Token.objects.create(
            user=self.user, description="Restricted token"
        )

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router1 = Router.objects.create(
            local_autonomous_system=self.asn,
            name="router1",
            hostname="router1.example.com",
            platform=self.platform,
        )
        self.router2 = Router.objects.create(
            local_autonomous_system=self.asn,
            name="router2",
            hostname="router2.example.com",
            platform=self.platform,
        )

        self.client = APIClient()

    def test_list_token_permissions(self):
        """Test listing token permissions via API"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router1.pk,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.get("/api/users/token-permissions/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertGreaterEqual(len(data["results"]), 1)

    def test_create_token_permission_via_api(self):
        """Test creating a token permission via API"""
        content_type = ContentType.objects.get_for_model(Router)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        data = {
            "token": self.restricted_token.pk,
            "content_type": content_type.pk,
            "object_id": self.router1.pk,
            "can_view": True,
            "can_edit": False,
            "can_delete": False,
            "custom_actions": {"configure": True, "poll_bgp_sessions": False},
        }

        response = self.client.post(
            "/api/users/token-permissions/", data, format="json"
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result["token"], self.restricted_token.pk)
        self.assertTrue(result["can_view"])
        self.assertFalse(result["can_edit"])

    def test_filter_by_token(self):
        """Test filtering permissions by token ID"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router1.pk,
        )
        TokenObjectPermission.objects.create(
            token=self.admin_token,
            content_type=content_type,
            object_id=self.router2.pk,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.get(
            f"/api/users/token-permissions/?token_id={self.restricted_token.pk}"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["token"], self.restricted_token.pk)

    def test_filter_by_content_type(self):
        """Test filtering permissions by content type"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router1.pk,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.get(
            f"/api/users/token-permissions/?content_type_id={content_type.pk}"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["count"], 1)

    def test_update_token_permission(self):
        """Test updating a token permission via API"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router1.pk,
            can_view=True,
            can_edit=False,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        data = {
            "can_edit": True,
            "custom_actions": {"configure": True},
        }

        response = self.client.patch(
            f"/api/users/token-permissions/{permission.pk}/", data, format="json"
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["can_edit"])

    def test_delete_token_permission(self):
        """Test deleting a token permission via API"""
        content_type = ContentType.objects.get_for_model(Router)

        permission = TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router1.pk,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.delete(f"/api/users/token-permissions/{permission.pk}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            TokenObjectPermission.objects.filter(pk=permission.pk).exists()
        )


@override_settings(TOKEN_PERMISSIONS_DEFAULT_MODE="allow")
class RouterPermissionEnforcementTestCase(TestCase):
    """Test that token permissions are enforced on router API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_staff = True
        self.user.is_superuser = True  # Grant all permissions
        self.user.save()
        self.unrestricted_token = Token.objects.create(
            user=self.user, description="Unrestricted", write_enabled=True
        )
        self.restricted_token = Token.objects.create(
            user=self.user, description="Restricted", write_enabled=True
        )

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router = Router.objects.create(
            local_autonomous_system=self.asn,
            name="test-router",
            hostname="router.example.com",
            platform=self.platform,
        )

        self.client = APIClient()

    def test_unrestricted_token_full_access(self):
        """Test that unrestricted token (no permission) has full access by default"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.unrestricted_token.key}"
        )

        # Should be able to retrieve
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)

        # Should be able to update
        response = self.client.patch(
            f"/api/devices/routers/{self.router.pk}/",
            {"comments": "Test update"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_restricted_token_view_only(self):
        """Test token with view-only permission"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
            custom_actions={},
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.restricted_token.key}")

        # Should be able to retrieve
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)

        # Should NOT be able to update
        response = self.client.patch(
            f"/api/devices/routers/{self.router.pk}/",
            {"comments": "Test update"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        # Should NOT be able to delete
        response = self.client.delete(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_restricted_token_no_view(self):
        """Test token with no view permission"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=False,
            can_edit=False,
            can_delete=False,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.restricted_token.key}")

        # Should NOT be able to retrieve
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_restricted_token_custom_action_configure(self):
        """Test token with configure custom action permission"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
            custom_actions={
                "configure": True,
                "poll_bgp_sessions": False,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.restricted_token.key}")

        # Should be able to view
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)

        # Should NOT be able to edit
        response = self.client.patch(
            f"/api/devices/routers/{self.router.pk}/",
            {"comments": "Test"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_restricted_token_multiple_routers(self):
        """Test token with permissions for one router but not another"""
        content_type = ContentType.objects.get_for_model(Router)

        router2 = Router.objects.create(
            local_autonomous_system=self.asn,
            name="router2",
            hostname="router2.example.com",
            platform=self.platform,
        )

        # Grant permission only for router1
        TokenObjectPermission.objects.create(
            token=self.restricted_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=True,
            can_delete=False,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.restricted_token.key}")

        # Should be able to access router1
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)

        # Should be able to edit router1
        response = self.client.patch(
            f"/api/devices/routers/{self.router.pk}/",
            {"comments": "Test"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Should be able to access router2 (no permission = allow by default)
        response = self.client.get(f"/api/devices/routers/{router2.pk}/")
        self.assertEqual(response.status_code, 200)


@override_settings(TOKEN_PERMISSIONS_DEFAULT_MODE="deny")
class RouterPermissionDenyModeTestCase(TestCase):
    """Test token permissions with deny by default mode"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.token_with_permission = Token.objects.create(
            user=self.user, description="With permission"
        )
        self.token_without_permission = Token.objects.create(
            user=self.user, description="Without permission"
        )

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router = Router.objects.create(
            local_autonomous_system=self.asn,
            name="test-router",
            hostname="router.example.com",
            platform=self.platform,
        )

        self.client = APIClient()

    def test_deny_mode_without_permission(self):
        """Test that deny mode blocks access without explicit permission"""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token_without_permission.key}"
        )

        # Should NOT be able to access
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_deny_mode_with_permission(self):
        """Test that deny mode allows access with explicit permission"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.token_with_permission,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token_with_permission.key}"
        )

        # Should be able to view
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)


class SuperuserTokenPermissionTestCase(TestCase):
    """Test that superuser tokens are also subject to token permissions"""

    def setUp(self):
        """Set up test data"""
        self.superuser = User.objects.create_superuser(
            username="admin", password="admin", email="admin@test.com"
        )
        self.superuser_token = Token.objects.create(
            user=self.superuser, description="Superuser token"
        )

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router = Router.objects.create(
            local_autonomous_system=self.asn,
            name="test-router",
            hostname="router.example.com",
            platform=self.platform,
        )

        self.client = APIClient()

    def test_superuser_token_can_be_restricted(self):
        """Test that even superuser tokens can be restricted"""
        content_type = ContentType.objects.get_for_model(Router)

        TokenObjectPermission.objects.create(
            token=self.superuser_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
            can_edit=False,
            can_delete=False,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.superuser_token.key}")

        # Should be able to view
        response = self.client.get(f"/api/devices/routers/{self.router.pk}/")
        self.assertEqual(response.status_code, 200)

        # Should NOT be able to edit (restricted by token permission)
        response = self.client.patch(
            f"/api/devices/routers/{self.router.pk}/",
            {"comments": "Test"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class TokenPermissionsAPIAccessTestCase(TestCase):
    """Test that can_manage_permissions flag controls access to token-permissions API"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Token with permission management enabled
        self.admin_token = Token.objects.create(
            user=self.user,
            description="Admin token",
            can_manage_permissions=True,
            write_enabled=True,
        )

        # Token without permission management (default)
        self.regular_token = Token.objects.create(
            user=self.user,
            description="Regular token",
            can_manage_permissions=False,
            write_enabled=True,
        )

        self.asn = AutonomousSystem.objects.create(
            asn=65001, name="Test AS", affiliated=True
        )
        self.platform = Platform.objects.create(
            name="Test Platform", slug="test-platform", napalm_driver="eos"
        )
        self.router = Router.objects.create(
            local_autonomous_system=self.asn,
            name="test-router",
            hostname="router.example.com",
            platform=self.platform,
        )

        self.client = APIClient()

    def test_regular_token_can_view_own_permissions(self):
        """Test that regular token can view its own permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        # Create a permission for the regular token
        perm = TokenObjectPermission.objects.create(
            token=self.regular_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")

        # Should be able to list (but only see own permissions)
        response = self.client.get("/api/users/token-permissions/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["id"], perm.pk)

        # Should be able to retrieve own permission
        response = self.client.get(f"/api/users/token-permissions/{perm.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_regular_token_cannot_view_other_permissions(self):
        """Test that regular token cannot see other token's permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        # Create a permission for the admin token
        TokenObjectPermission.objects.create(
            token=self.admin_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")

        # Should not see admin token's permissions in list
        response = self.client.get("/api/users/token-permissions/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)  # Should see 0 permissions

    def test_regular_token_cannot_create_permissions(self):
        """Test that regular token cannot create permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")

        data = {
            "token": self.regular_token.pk,
            "content_type": content_type.pk,
            "object_id": self.router.pk,
            "can_view": True,
        }

        response = self.client.post(
            "/api/users/token-permissions/", data, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_regular_token_cannot_update_permissions(self):
        """Test that regular token cannot update permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        perm = TokenObjectPermission.objects.create(
            token=self.regular_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")

        data = {"can_edit": True}
        response = self.client.patch(
            f"/api/users/token-permissions/{perm.pk}/", data, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_regular_token_cannot_delete_permissions(self):
        """Test that regular token cannot delete permissions"""
        content_type = ContentType.objects.get_for_model(Router)

        perm = TokenObjectPermission.objects.create(
            token=self.regular_token,
            content_type=content_type,
            object_id=self.router.pk,
            can_view=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")

        response = self.client.delete(f"/api/users/token-permissions/{perm.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_admin_token_has_full_access(self):
        """Test that token with can_manage_permissions=True has full access"""
        content_type = ContentType.objects.get_for_model(Router)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        # Should be able to create
        data = {
            "token": self.regular_token.pk,
            "content_type": content_type.pk,
            "object_id": self.router.pk,
            "can_view": True,
        }
        response = self.client.post(
            "/api/users/token-permissions/", data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        perm_id = response.json()["id"]

        # Should be able to update
        data = {"can_edit": True}
        response = self.client.patch(
            f"/api/users/token-permissions/{perm_id}/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)

        # Should be able to delete
        response = self.client.delete(f"/api/users/token-permissions/{perm_id}/")
        self.assertEqual(response.status_code, 204)
