# Production Smoke-Test Script & Execution Guide

**Date:** 18 November 2026
**Script:** `scripts/production_smoke_test.py`

## Checks performed

The script makes read-only API calls against a deployment URL explicitly provided by the operator:

1. `GET /api/v1/health` — requires HTTP 200 and JSON `status: "ok"`.
2. `GET /api/v1/xictek/index-status` — authenticated; requires HTTP 200, `index_built: true`, and a positive chunk count.
3. `POST /api/v1/xictek/chat` — authenticated; sends a simple public Core Services query and verifies a non-empty reply, the same conversation ID, and a `sources` array.
4. Eight authenticated guardrail probes — one prompt-injection attempt for each of the seven content domains, plus one employee PII probe. Each must return `intent: "declined_prompt_injection"`.

Transient errors receive up to three attempts. The script exits with code `0` only if every enabled check passes; otherwise it exits with code `1`. It prints a JSON summary but never prints the internal token.

## Windows PowerShell usage

Set the deployment URL and make the token available as `SMOKE_INTERNAL_SERVICE_TOKEN` through the organization's approved secure environment/secret mechanism. Do not commit it, include it in shell command history, screenshots, or group chat. The confirmed API origin for the current verification is `https://hisabdo-ai-api.hisabdo.app`.

```powershell
$env:SMOKE_BASE_URL = "https://hisabdo-ai-api.hisabdo.app"
# Configure SMOKE_INTERNAL_SERVICE_TOKEN through your approved secure mechanism.
python scripts/production_smoke_test.py
```

The full run makes one health request, one index-status request, one ordinary chat request, and eight short safety probes. The script does not send the token as a command-line argument or print it.

To run only the public liveness check (no token and no chat request):

```powershell
python scripts/production_smoke_test.py --base-url "https://hisabdo-ai-api.hisabdo.app" --health-only
```

For health and index checks without sending a chat request:

```powershell
python scripts/production_smoke_test.py --skip-chat
```

Alternatively, pass the base URL with `--base-url`; keep the token in `SMOKE_INTERNAL_SERVICE_TOKEN`.

## Local smoke check

Start the service in a separate terminal using the repository's normal run instructions, then set `SMOKE_BASE_URL` to that local origin (for example, `http://127.0.0.1:8000`) and set a development token matching the service configuration. Run the same script. A local pass verifies that the script and local API wiring work; it is not a production deployment sign-off.

## Production execution status for this handover

The public health-only run was recorded on 18 November 2026: HTTP 200, `status: "ok"`, one measured response at 1,373.07 ms. This single health sample does not establish chat latency or an SLA. Authenticated index, chat, retrieval, and guardrail checks remain unverified until the authorized service token is available.
