# Production Smoke-Test Script & Execution Guide

**Date:** 17 November 2026  
**Script:** `scripts/production_smoke_test.py`

## Checks performed

The script makes read-only API calls against a deployment URL explicitly provided by the operator:

1. `GET /api/v1/health` — requires HTTP 200 and JSON `status: "ok"`.
2. `GET /api/v1/xictek/index-status` — authenticated; requires HTTP 200, `index_built: true`, and a positive chunk count.
3. `POST /api/v1/xictek/chat` — authenticated; sends a simple public Core Services query and verifies a non-empty reply, the same conversation ID, and a `sources` array.

Transient errors receive up to three attempts. The script exits with code `0` only if every enabled check passes; otherwise it exits with code `1`. It prints a JSON summary but never prints the internal token.

## Windows PowerShell usage

Set the deployment URL and token in the current PowerShell session. Obtain the token through the organization's approved secure channel; do not paste it into the script, source control, screenshots, or group chat.

```powershell
$env:SMOKE_BASE_URL = "https://<approved-deployment-host>"
$env:SMOKE_INTERNAL_SERVICE_TOKEN = "<token-from-secure-channel>"
python scripts/production_smoke_test.py
```

For health and index checks without sending a chat request:

```powershell
python scripts/production_smoke_test.py --skip-chat
```

Alternatively, pass the base URL with `--base-url`; keep the token in `SMOKE_INTERNAL_SERVICE_TOKEN`.

## Local smoke check

Start the service in a separate terminal using the repository's normal run instructions, then set `SMOKE_BASE_URL` to that local origin (for example, `http://127.0.0.1:8000`) and set a development token matching the service configuration. Run the same script. A local pass verifies that the script and local API wiring work; it is not a production deployment sign-off.

## Production execution status for this handover

This handover includes the script and guide. A production smoke run is **not recorded** because no approved production URL or secure token was supplied for this run. After deployment, the release owner should run the script against the approved host and attach its JSON output to the release record.
