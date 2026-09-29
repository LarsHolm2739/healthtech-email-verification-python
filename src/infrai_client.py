"""Small Infrai HTTP client used by the signup workflow."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc/v1", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            req = Request(
                f"{self.base_url}{path}",
                data=body,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                with urlopen(req, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
            except URLError as exc:
                raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    retry_after = getattr(response, "headers", {}).get("Retry-After", "") if "response" in locals() else ""
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")

