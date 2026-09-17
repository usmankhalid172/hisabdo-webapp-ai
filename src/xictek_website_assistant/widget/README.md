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

```bash
# terminal 1, from the repo root
uvicorn src.main:app --reload --port 8000

# terminal 2, from this widget/ folder
python -m http.server 5500
# then open http://localhost:5500/demo.html
```

`demo.html` is a stand-in page — the widget code itself is identical
to what would ship on the real site.

## Branding — action needed

I could not pull xicteksystems.com's actual brand colors, fonts, or
logo into this build: the site's Next.js pages only exposed page text
through the tools available here, not its compiled CSS or raster
assets. So `xictek-widget.js` currently ships a placeholder palette —
a clean blue/navy tech-company look chosen to look presentable on
its own — set as CSS custom properties at the top of the injected
`STYLE` block:

```css
--xk-ink: #12182B;
--xk-bg: #FFFFFF;
--xk-bg-soft: #F4F6FB;
--xk-accent: #2F6FED;
--xk-accent-ink: #1B4FC4;
--xk-border: #E3E7F0;
```

**Before this goes on the real site**, swap these for XICTEK's actual
brand hex values (and, if there's a wordmark/icon, replace the generic
chat-bubble SVG in the launcher button with it). That's a five-line
edit, deliberately isolated so it doesn't require touching any of the
widget's structure or logic.

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
