# XICTEK Assistant — embeddable widget

Portable vanilla HTML/CSS/JS chat widget, framework-agnostic (no React,
no build step). Drop it into any page with one `<script>` tag; it
injects its own styles and DOM and doesn't touch anything else on the
page.

## Embed

```html
<script
  src="xictek-widget.js"
  data-api-base="https://your-api-host"
  data-api-token="YOUR_INTERNAL_TOKEN"
  data-title="XICTEK Assistant"
  data-greeting="Hi! Ask me anything about XICTEK Systems, our services, or HisabDo."
></script>
```

| Attribute | Required | Default | Purpose |
|---|---|---|---|
| `data-api-base` | yes | — | Base URL of the running `HisabDo-Webapp-AI` service (no trailing path) |
| `data-api-token` | yes* | — | Sent as `X-Internal-Token`. *See the security note below.* |
| `data-title` | no | `XICTEK Assistant` | Widget header title |
| `data-greeting` | no | generic greeting | First message shown when the panel opens |

## Local demo

Requires `XICTEK_WIDGET_ALLOWED_ORIGINS=["http://localhost:5500"]` in
the repo root's `.env` — `demo.html`'s port (`5500`) differs from the
API's port (`8000`), which browsers treat as a different origin, so
without this the widget's requests are silently blocked by the browser
itself (shows as a generic "Sorry, something went wrong" in the widget,
with the real CORS error only visible in the browser's dev console, not
in the server's logs). `.env.example` already includes this by default.

```bash
# terminal 1, from the repo root
uvicorn src.main:app --reload --port 8000

# terminal 2, from this widget/ folder
python -m http.server 5500
# then open http://localhost:5500/demo.html
```

`demo.html` is a stand-in page — the widget code itself is identical
to what would ship on the real site.

## Branding

Palette pulled from real xicteksystems.com screenshots (the fetch tool
available here only extracts page text, not CSS/images, so screenshots
were the way to get this accurately) — near-black navy hero/footer,
bright sky-blue CTA buttons, white/light-gray content sections, and a
blue→indigo gradient accent on headlines:

```css
--xk-ink: #0B1120;       /* hero/footer navy, header bar */
--xk-bg: #FFFFFF;
--xk-bg-soft: #F5F8FC;   /* light-section background */
--xk-accent: #1E9EFF;    /* primary CTA blue */
--xk-accent-ink: #0D7FE0;/* hover/pressed */
--xk-accent-2: #6C63FF;  /* gradient endpoint, unused directly yet */
--xk-border: #E4E9F2;
--xk-muted: #64748B;
```

These are close reads from screenshots, not exact hex values sampled
from the live CSS — worth a final pixel-level check against the real
site (or the design team) before shipping, but should already look
at-home next to the rest of xicteksystems.com. The generic chat-bubble
SVG in the launcher button is still a placeholder — swap in the real
"X" wordmark/icon (visible in the header/footer screenshots) when
integrating with the live site.

## Security note — read before the real integration

`data-api-token` is sent as `X-Internal-Token`, the same
service-to-service shared secret this repo already uses for Swagger
testing (`src/security.py`). That's fine for this demo, but **it is
not a safe production auth story for a public website widget** —
anything in a `<script>` tag's attributes or a browser's network tab
is visible to any visitor, so shipping the real internal token this
way would leak it. Flag this for the team-lead meeting alongside the
real widget/CORS integration; likely fixes are a public,
unauthenticated-but-rate-limited variant of the `/chat` endpoint, or a
short-lived per-session token minted server-side by the real site's
own backend rather than reusing this shared secret.

## What this is not (yet)

This is a standalone file, not wired into xicteksystems.com's actual
Next.js codebase — per the team lead's instruction, that integration
is deferred until repo/hosting access is sorted out. Dropping it onto
the real site should be as simple as adding the `<script>` tag above
to the site's layout once that access exists.
