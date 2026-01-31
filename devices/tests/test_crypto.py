import base64
from unittest import TestCase

from devices.crypto import get_cipher
from devices.crypto.arista import AristaType7Cipher
from devices.crypto.cisco import MAGIC as CISCO_TYPE7_MAGIC
from devices.crypto.cisco import CiscoType7Cipher
from devices.crypto.juniper import MAGIC as JUNIPER_TYPE9_MAGIC
from devices.crypto.juniper import JuniperType9Cipher
from devices.enums import PasswordAlgorithm


class TestGetCipher(TestCase):
    def test_get_cipher_cisco(self):
        cipher = get_cipher(algorithm=PasswordAlgorithm.CISCO_TYPE7)
        self.assertIsInstance(cipher, CiscoType7Cipher)

    def test_get_cipher_juniper(self):
        cipher = get_cipher(algorithm=PasswordAlgorithm.JUNIPER_TYPE9)
        self.assertIsInstance(cipher, JuniperType9Cipher)

    def test_get_cipher_arista(self):
        cipher = get_cipher(algorithm=PasswordAlgorithm.ARISTA_TYPE7)
        self.assertIsInstance(cipher, AristaType7Cipher)

    def test_get_cipher_unknown(self):
        cipher = get_cipher(algorithm="unknown-algorithm")
        self.assertIsNone(cipher)

        cipher = get_cipher(algorithm="")
        self.assertIsNone(cipher)


class TestCiscoType7Cipher(TestCase):
    def setUp(self):
        self.cipher = CiscoType7Cipher()
        self.plain_password = "mypassword"

    def test_encrypt_return_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        self.assertIsInstance(encrypted, str)
        self.assertTrue(encrypted.startswith(CISCO_TYPE7_MAGIC))

    def test_encrypt_decrypt_roundtrip(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        decrypted = self.cipher.decrypt(value=encrypted)
        self.assertEqual(decrypted, self.plain_password)

    def test_empty_string(self):
        encrypted = self.cipher.encrypt(value="")
        self.assertEqual(encrypted, "")

        decrypted = self.cipher.decrypt(value="")
        self.assertEqual(decrypted, "")

    def test_is_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        self.assertTrue(self.cipher.is_encrypted(value=encrypted))
        self.assertFalse(self.cipher.is_encrypted(value=self.plain_password))
        self.assertFalse(self.cipher.is_encrypted(value=""))

    def test_encrypt_already_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        double_encrypted = self.cipher.encrypt(value=encrypted)
        self.assertEqual(encrypted, double_encrypted)

    def test_decrypt_not_encrypted(self):
        decrypted = self.cipher.decrypt(value=self.plain_password)
        self.assertEqual(decrypted, self.plain_password)

    def test_key_parameter_ignored(self):
        encrypted_with_key = self.cipher.encrypt(
            value=self.plain_password, key="somekey"
        )
        encrypted_without_key = self.cipher.encrypt(value=self.plain_password)
        self.assertEqual(
            self.cipher.decrypt(encrypted_with_key),
            self.cipher.decrypt(encrypted_without_key),
        )

    def test_different_passwords_produce_different_ciphertext(self):
        encrypted1 = self.cipher.encrypt(value="password1")
        encrypted2 = self.cipher.encrypt(value="password2")
        self.assertNotEqual(encrypted1, encrypted2)


class TestJuniperType9Cipher(TestCase):
    def setUp(self):
        self.cipher = JuniperType9Cipher()
        self.plain_password = "mypassword"

    def test_encrypt_return_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        self.assertIsInstance(encrypted, str)
        self.assertTrue(encrypted.startswith(JUNIPER_TYPE9_MAGIC))

    def test_encrypt_decrypt_roundtrip(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        decrypted = self.cipher.decrypt(value=encrypted)
        self.assertEqual(decrypted, self.plain_password)

    def test_encrypt_empty_string(self):
        encrypted = self.cipher.encrypt(value="")
        self.assertEqual(encrypted, "")

        decrypted = self.cipher.decrypt(value="")
        self.assertEqual(decrypted, "")

    def test_is_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        self.assertTrue(self.cipher.is_encrypted(value=encrypted))
        self.assertFalse(self.cipher.is_encrypted(value=self.plain_password))
        self.assertFalse(self.cipher.is_encrypted(value=""))

    def test_encrypt_already_encrypted(self):
        encrypted = self.cipher.encrypt(value=self.plain_password)
        double_encrypted = self.cipher.encrypt(value=encrypted)
        self.assertEqual(encrypted, double_encrypted)

    def test_decrypt_not_encrypted(self):
        decrypted = self.cipher.decrypt(value=self.plain_password)
        self.assertEqual(decrypted, self.plain_password)

    def test_key_produces_deterministic_encryption(self):
        key = "192.0.2.1"
        encrypted1 = self.cipher.encrypt(value=self.plain_password, key=key)
        encrypted2 = self.cipher.encrypt(value=self.plain_password, key=key)
        encrypted3 = self.cipher.encrypt(value=self.plain_password, key=key)
        self.assertEqual(encrypted1, encrypted2)
        self.assertEqual(encrypted2, encrypted3)

    def test_different_keys_produce_different_ciphertext(self):
        encrypted1 = self.cipher.encrypt(value=self.plain_password, key="192.0.2.1")
        encrypted2 = self.cipher.encrypt(value=self.plain_password, key="192.0.2.2")
        self.assertNotEqual(encrypted1, encrypted2)
        self.assertEqual(self.cipher.decrypt(value=encrypted1), self.plain_password)
        self.assertEqual(self.cipher.decrypt(value=encrypted2), self.plain_password)

    def test_different_passwords_produce_different_ciphertext(self):
        encrypted1 = self.cipher.encrypt(value="password1")
        encrypted2 = self.cipher.encrypt(value="password2")
        self.assertNotEqual(encrypted1, encrypted2)


class TestAristaType7Cipher(TestCase):
    def setUp(self):
        self.cipher = AristaType7Cipher()
        self.plain_password = "mypassword"
        self.encryption_key = "192.0.2.1"

    def test_encrypt_return_encrypted(self):
        encrypted = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        self.assertIsInstance(encrypted, str)

    def test_encrypt_return_base64(self):
        encrypted = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        try:
            base64.b64decode(encrypted)
        except Exception:
            self.fail("Encrypted password is not valid base64")

    def test_decrypt_returns_plain_text(self):
        """Decrypt should return the original plain text."""
        encrypted = self.cipher.encrypt(self.plain_password, self.encryption_key)
        decrypted = self.cipher.decrypt(encrypted, self.encryption_key)
        self.assertEqual(decrypted, self.plain_password)

    def test_encrypt_decrypt_roundtrip(self):
        encrypted = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        decrypted = self.cipher.decrypt(value=encrypted, key=self.encryption_key)
        self.assertEqual(decrypted, self.plain_password)

    def test_encrypt_empty_string(self):
        encrypted = self.cipher.encrypt(value="", key=self.encryption_key)
        self.assertEqual(encrypted, "")

        decrypted = self.cipher.decrypt(value="", key=self.encryption_key)
        self.assertEqual(decrypted, "")

    def test_is_encrypted(self):
        encrypted = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        self.assertTrue(self.cipher.is_encrypted(value=encrypted))
        self.assertFalse(self.cipher.is_encrypted(value=self.plain_password))
        self.assertFalse(self.cipher.is_encrypted(value=""))

    def test_encrypt_already_encrypted(self):
        encrypted = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        double_encrypted = self.cipher.encrypt(value=encrypted, key=self.encryption_key)
        self.assertEqual(encrypted, double_encrypted)

    def test_decrypt_not_encrypted(self):
        decrypted = self.cipher.decrypt(
            value=self.plain_password, key=self.encryption_key
        )
        self.assertEqual(decrypted, self.plain_password)

    def test_key_produces_deterministic_encryption(self):
        encrypted1 = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        encrypted2 = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        encrypted3 = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        self.assertEqual(encrypted1, encrypted2)
        self.assertEqual(encrypted2, encrypted3)

    def test_different_keys_produce_different_ciphertext(self):
        encrypted1 = self.cipher.encrypt(
            value=self.plain_password, key=self.encryption_key
        )
        encrypted2 = self.cipher.encrypt(value=self.plain_password, key="192.0.2.2")
        self.assertNotEqual(encrypted1, encrypted2)
        self.assertEqual(
            self.cipher.decrypt(value=encrypted1, key=self.encryption_key),
            self.plain_password,
        )
        self.assertEqual(
            self.cipher.decrypt(value=encrypted2, key="192.0.2.2"), self.plain_password
        )

    def test_different_passwords_produce_different_ciphertext(self):
        encrypted1 = self.cipher.encrypt(value="password1", key=self.encryption_key)
        encrypted2 = self.cipher.encrypt(value="password2", key=self.encryption_key)
        self.assertNotEqual(encrypted1, encrypted2)
