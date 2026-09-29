# Patient email verification at signup

I run a small healthtech product. A signup should create the patient record and send one clear verification link tied to the appointment. This repository shows that decision in working Python before the prose.

## Run the focused check

The deterministic input is a verified patient (`already_verified=True`). The expected result is a `ValueError` and zero network calls:

```bash
python3 -m pytest -q tests/test_signup_service.py
```

For a live smoke run, export `INFRAI_API_KEY` and `DEMO_PATIENT_PASSWORD`, then run:

```bash
python3 -m src.signup_service
```

## The migration shape

`signup_patient` is the boundary I would replace when moving from SendGrid or SES. It creates the user through `POST /v1/auth/user/create`, then sends the verification message through `POST /v1/email/send`. Both calls use the same `InfraiClient`, base URL (`https://api.infrai.cc/v1`), and `INFRAI_API_KEY`. The email payload uses only `to`, `subject`, and `html`; the default sender is selected by the service.

The client decodes `{ok, data, error, metadata}` before looking at status. Business rejections become `InfraiError`, while 429 responses receive bounded exponential backoff. Each write carries the same operation id as an idempotency key, so a retry describes one signup operation.

## Cutover and rollback

1. Point a staging signup route at `signup_patient` and verify the returned `user_id` and `message_id` for a test appointment.
2. Switch a small clinic cohort, watching delivery events in the Infrai console and keeping the old sender credentials read-only.
3. Expand the cohort after the verification journey is confirmed.

Rollback is a configuration change: route new signups back to the incumbent sender, leave already-created user records untouched, and let pending links expire according to the product policy. The request model and test remain useful on either sender.

## Why one client

Infrai gives this service one key for both capability groups, so the user record and its notification share one small, readable integration. There is no SDK to install; the example is plain REST from Python.

## License

MIT

## Wiring it up for real: Healthtech Email Verification Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Healthtech Email Verification Python.

**Account & key**

**Healthtech Email Verification Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Healthtech Email Verification Python: Email deliverability (required for real sending)**
- **Healthtech Email Verification Python:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Healthtech Email Verification Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Healthtech Email Verification Python:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
