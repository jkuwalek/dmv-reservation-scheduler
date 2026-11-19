import logging

import pytest

from dmvwatch.security.codes import CodeCipher, DecryptionFailed, EncryptedCode
from dmvwatch.security.redaction import RedactAccessCodes

KEY_V1 = b"0" * 32
KEY_V2 = b"1" * 32
CODE = "h75-56f-psf-yrs"


def _cipher(version: int = 1) -> CodeCipher:
    return CodeCipher(keys={1: KEY_V1, 2: KEY_V2}, current_version=version)


def test_a_code_survives_a_round_trip() -> None:
    cipher = _cipher()
    assert cipher.decrypt(cipher.encrypt(CODE)) == CODE


def test_the_ciphertext_does_not_contain_the_code() -> None:
    blob = _cipher().encrypt(CODE)
    assert CODE.encode() not in blob.ciphertext


def test_encrypting_twice_gives_different_ciphertext() -> None:
    cipher = _cipher()
    assert cipher.encrypt(CODE).ciphertext != cipher.encrypt(CODE).ciphertext


def test_the_key_version_is_recorded_so_keys_can_rotate() -> None:
    assert _cipher(version=2).encrypt(CODE).key_version == 2


def test_a_code_encrypted_with_an_old_key_still_decrypts() -> None:
    old = _cipher(version=1).encrypt(CODE)
    assert _cipher(version=2).decrypt(old) == CODE


def test_tampering_is_detected() -> None:
    blob = _cipher().encrypt(CODE)
    tampered = EncryptedCode(
        ciphertext=blob.ciphertext[:-1] + bytes([blob.ciphertext[-1] ^ 1]),
        nonce=blob.nonce,
        key_version=blob.key_version,
    )
    with pytest.raises(DecryptionFailed):
        _cipher().decrypt(tampered)


def test_an_unknown_key_version_is_refused() -> None:
    blob = _cipher().encrypt(CODE)
    lonely = CodeCipher(keys={2: KEY_V2}, current_version=2)
    with pytest.raises(DecryptionFailed):
        lonely.decrypt(blob)


def test_a_key_of_the_wrong_length_is_refused_at_construction() -> None:
    with pytest.raises(ValueError):
        CodeCipher(keys={1: b"short"}, current_version=1)


def test_a_missing_current_key_is_refused_at_construction() -> None:
    with pytest.raises(ValueError):
        CodeCipher(keys={1: KEY_V1}, current_version=9)


def test_log_records_have_access_codes_stripped() -> None:
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="redeeming %s for user",
        args=(CODE,),
        exc_info=None,
    )
    RedactAccessCodes().filter(record)
    assert CODE not in record.getMessage()
    assert "[redacted]" in record.getMessage()


def test_redaction_also_covers_codes_inside_the_message_itself() -> None:
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"redeeming {CODE}",
        args=None,
        exc_info=None,
    )
    RedactAccessCodes().filter(record)
    assert CODE not in record.getMessage()
