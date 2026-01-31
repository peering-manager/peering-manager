from abc import ABC, abstractmethod

__all__ = ("PasswordCipher",)


class PasswordCipher(ABC):
    """
    Abstract base class defining the interface for password encryption/decryption.
    """

    @abstractmethod
    def encrypt(self, value: str, key: str = "") -> str:
        """
        Encrypt a password.

        The key parameter is optional but may be required for certain algorithms.
        """

    @abstractmethod
    def decrypt(self, value: str, key: str = "") -> str:
        """
        Decrypt a password.

        The key parameter is optional but may be required for certain algorithms.
        """

    @abstractmethod
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value is already encrypted.
        """
