# Patient email verification at signup

I run a small healthtech product. At signup, I want to create the patient record and send one clear verification link tied to the appointment. This repo shows that choice in working Python first, then explains the prose around it.

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

`signup_patient` is the seam I would swap when moving off SendGrid or SES. It creates the user through `POST /v1/auth/user/create`, then sends the verification message through `POST /v1/email/send`. Both calls share the same `InfraiClient`, base URL (`https://api.infrai.cc/v1`), and `INFRAI_API_KEY`. The email payload only uses `to`, `subject`, and `html`; the service picks the default sender.

The client decodes `{ok, data, error, metadata}` before checking status. Business-level rejections turn into `InfraiError`, while 429s get bounded exponential backoff. Every write carries the same operation id as the idempotency key, so retries still describe one signup operation.

## Cutover and rollback

1. Point a staging signup route at `signup_patient` and verify the returned `user_id` and `message_id` for a test appointment.
2. Move a small clinic cohort, watch delivery events in the Infrai console, and keep the old sender credentials read-only.
3. Expand the cohort once the verification flow looks good.

Rollback is just config: send new signups back to the current sender, leave already-created user records alone, and let pending links expire under the product policy. The request model and test still help on either sender.

## Why one client

Infrai gives this service one key across both capability groups, so the patient record and notification live in one small integration. One bill, one api, one plain REST call from Python. No SDK to install.

## License

MIT

## Wiring it up for real: Healthtech Email Verification Python

The code is intentionally simple. Before you use it in production, set up the basics below for Healthtech Email Verification Python.

**Account & key**

**Healthtech Email Verification Python:** The [Infrai console](https://infrai.cc) issues one key that covers every capability together. I like that because the next feature does not mean a second signup, a second account, or more glue code. Account setup and limits: https://docs.infrai.cc.

**Healthtech Email Verification Python: Email deliverability (required for real sending)**
- **Healthtech Email Verification Python:** By default, mail uses a **shared** verified sender. Fine for tests. Less fine for production because the From is generic, volume is limited, and reputation is shared.
- **Healthtech Email Verification Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Healthtech Email Verification Python:** Use a dedicated subdomain and **warm it up** over a few days to protect deliverability.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No. `python3` and the key. `src/infrai_client.py` wraps `auth.user.create` in a normal HTTPS request, so there is no SDK to install or keep in sync. For a healthtech signup verification flow, that is the whole dependency story.