from django.conf import settings
from django.test import TestCase

from devices.enums import PasswordAlgorithm
from devices.models import Platform


class PlatformTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.platforms = [
            Platform(
                name="Juniper Junos",
                slug="juniper-junos",
                password_algorithm=PasswordAlgorithm.JUNIPER_TYPE9,
            ),
            Platform(
                name="Cisco IOS",
                slug="cisco-ios",
                password_algorithm=PasswordAlgorithm.CISCO_TYPE7,
            ),
            Platform(name="Arista EOS", slug="arista-eos"),
        ]
        Platform.objects.bulk_create(cls.platforms)

    def test_password_encryption_decryption(self):
        clear_text_password = "mypassword"
        junos = Platform.objects.filter(
            password_algorithm=PasswordAlgorithm.JUNIPER_TYPE9
        ).first()
        encrypted_password = junos.encrypt_password(clear_text_password)
        self.assertNotEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, junos.decrypt_password(encrypted_password)
        )

        cisco = Platform.objects.filter(
            password_algorithm=PasswordAlgorithm.CISCO_TYPE7
        ).first()
        encrypted_password = cisco.encrypt_password(clear_text_password)
        self.assertNotEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, cisco.decrypt_password(encrypted_password)
        )

        arista = Platform.objects.filter(password_algorithm="").first()
        encrypted_password = arista.encrypt_password(clear_text_password)
        self.assertEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, arista.decrypt_password(encrypted_password)
        )
