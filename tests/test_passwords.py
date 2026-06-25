"""Password hashing must round-trip and reject bad inputs."""

from app.auth import passwords


def test_hash_then_verify():
    h = passwords.hash_password("hunter22A!")
    assert passwords.verify_password("hunter22A!", h)


def test_wrong_password_rejected():
    h = passwords.hash_password("hunter22A!")
    assert not passwords.verify_password("wrong", h)


def test_hash_is_salted():
    a = passwords.hash_password("same-password")
    b = passwords.hash_password("same-password")
    assert a != b, "two hashes of the same password must differ (salted)"


def test_malformed_encoded_rejected():
    assert not passwords.verify_password("anything", "not-a-real-encoded-hash")
    assert not passwords.verify_password("anything", "")
