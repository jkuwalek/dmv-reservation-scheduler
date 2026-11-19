"""Access codes are credentials: encrypted at rest, with a versioned key.

The key lives in the environment, never in the database, so a dump of the tables
yields nothing usable. The version travels with the ciphertext so keys can be
rotated without a migration or a bulk re-encrypt.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_BYTES = 12
KEY_BYTES = 32


class DecryptionFailed(Exception):
    pass


@dataclass(frozen=True, slots=True)
class EncryptedCode:
    ciphertext: bytes
    nonce: bytes
    key_version: int


class CodeCipher:
    def __init__(self, keys: Mapping[int, bytes], current_version: int) -> None:
        for version, key in keys.items():
            if len(key) != KEY_BYTES:
                raise ValueError(f"key version {version} must be {KEY_BYTES} bytes")
        if current_version not in keys:
            raise ValueError(f"no key for current version {current_version}")
        self._keys = dict(keys)
        self._current_version = current_version

    def encrypt(self, code: str) -> EncryptedCode:
        nonce = os.urandom(NONCE_BYTES)
        aead = AESGCM(self._keys[self._current_version])
        return EncryptedCode(
            ciphertext=aead.encrypt(nonce, code.encode(), None),
            nonce=nonce,
            key_version=self._current_version,
        )

    def decrypt(self, blob: EncryptedCode) -> str:
        key = self._keys.get(blob.key_version)
        if key is None:
            raise DecryptionFailed(f"no key for version {blob.key_version}")
        try:
            return AESGCM(key).decrypt(blob.nonce, blob.ciphertext, None).decode()
        except InvalidTag as exc:
            raise DecryptionFailed("ciphertext failed authentication") from exc
