import pytest

from src.signup_service import SignupRequest, signup_patient


def test_verified_patient_does_not_receive_duplicate_link():
    request = SignupRequest("a@example.com", "secret", "Ari", "apt-1")

    class FailingClient:
        def request(self, *args, **kwargs):
            raise AssertionError("network should not be called")

    with pytest.raises(ValueError, match="do not need"):
        signup_patient(request, FailingClient(), already_verified=True)

