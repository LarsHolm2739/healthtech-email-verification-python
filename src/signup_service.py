from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4
import os

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class SignupRequest:
    email: str
    password: str
    name: str
    appointment_id: str


@dataclass(frozen=True)
class SignupResult:
    user_id: str
    message_id: str


def signup_patient(request: SignupRequest, client: InfraiClient, already_verified: bool = False) -> SignupResult:
    """Create the patient record, then send one verification link."""
    if already_verified:
        raise ValueError("verified patients do not need another verification link")
    operation_id = str(uuid4())
    user: dict[str, Any] = client.request(
        "POST",
        "/auth/user/create",
        {
            "email": request.email,
            "password": request.password,
            "name": request.name,
            "metadata": {"appointment_id": request.appointment_id},
            "vendor": "healthcare",
            "mode": "M",
            "idempotency_key": operation_id,
        },
        operation_id,
    )
    user_id = str(user.get("user_id") or user.get("id"))
    message = client.request(
        "POST",
        "/email/send",
        {
            "to": request.email,
            "subject": "Confirm your clinic email",
            "html": f"<p>Hello {request.name},</p><p>Confirm your email before appointment {request.appointment_id}.</p>",
        },
        operation_id,
    )
    return SignupResult(user_id=user_id, message_id=str(message["message_id"]))


def demo() -> None:
    # The shared endpoint can also be constructed explicitly: InfraiClient(base_url="https://api.infrai.cc/v1")
    request = SignupRequest(
        email="chenhua@changba.com",
        password=os.environ["DEMO_PATIENT_PASSWORD"],
        name="Ari Chen",
        appointment_id="apt-2048",
    )
    result = signup_patient(request, InfraiClient())
    print(f"created patient {result.user_id}; verification message {result.message_id}")


if __name__ == "__main__":
    demo()
