/**
 * XICTEK Website Assistant — embeddable chat widget.
 *
 * Framework-agnostic, single-file drop-in: one <script> tag, no build
 * step, no dependency on the host page's stack (works whether the real
 * site is Next.js, static HTML, or anything else). Injects its own
 * styles and DOM; does not touch anything already on the page.
 *
 * Usage:
 *   <script
 *     src="xictek-widget.js"
 *     data-api-base="http://localhost:8000"
 *     data-api-token="change-me-dev-token"
 *   ></script>
 *
 * IMPORTANT — read before deploying to the real site:
 * `data-api-token` is sent as the `X-Internal-Token` header, which is
 * this repo's *service-to-service* shared secret (src/security.py) —
 * it is not designed to be safe to ship in client-side JS that anyone
 * visiting the site can read out of the page source or network tab.
 * That's fine for this demo (same secret already used for Swagger
 * testing), but it is NOT a production-safe auth story for a public
 * website widget. Flag this in the team-lead meeting alongside the
 * real widget/CORS integration — likely fixes are: a public,
 * unauthenticated-but-rate-limited variant of this endpoint, or a
 * short-lived per-session token minted server-side by the real site's
 * backend rather than this shared secret.
 */
(function () {
  "use strict";

  var scriptTag = document.currentScript;
  var config = {
    apiBase: (scriptTag && scriptTag.getAttribute("data-api-base")) || "",
    apiToken: (scriptTag && scriptTag.getAttribute("data-api-token")) || "",
    title: (scriptTag && scriptTag.getAttribute("data-title")) || "XICTEK Assistant",
    greeting:
      (scriptTag && scriptTag.getAttribute("data-greeting")) ||
      "Hi! Ask me anything about XICTEK Systems, our services, or HisabDo.",
  };

  if (!config.apiBase) {
    console.error(
      "[xictek-widget] Missing required data-api-base attribute on the <script> tag — widget not initialized."
    );
    return;
  }

  // ---------------------------------------------------------------------
  // Styles — CSS custom properties up top so the real brand palette can
  // be dropped in later by editing this one block (see README.md's
  // "Branding — action needed" section for why these are placeholders).
  // ---------------------------------------------------------------------
  var STYLE = `
    :root {
      /* Pulled from actual xicteksystems.com screenshots: near-black
         navy hero/footer, bright sky-blue CTA buttons, white/light-gray
         content sections, blue->indigo gradient on headline accents. */
      --xk-ink: #0B1120;
      --xk-bg: #FFFFFF;
      --xk-bg-soft: #F5F8FC;
      --xk-accent: #1E9EFF;
      --xk-accent-ink: #0D7FE0;
      --xk-accent-2: #6C63FF;
      --xk-border: #E4E9F2;
      --xk-muted: #64748B;
      --xk-radius: 14px;
      --xk-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #xk-launcher {
      position: fixed;
      right: 20px;
      bottom: 20px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: var(--xk-accent);
      color: #fff;
      border: none;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(18, 24, 43, 0.24);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2147483000;
      transition: transform 0.15s ease;
      font-family: var(--xk-font);
    }
    #xk-launcher:hover { transform: scale(1.06); }
    #xk-launcher svg { width: 26px; height: 26px; }

    #xk-panel {
      position: fixed;
      right: 20px;
      bottom: 88px;
      width: 360px;
      max-width: calc(100vw - 32px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: var(--xk-bg);
      border-radius: var(--xk-radius);
      box-shadow: 0 16px 48px rgba(18, 24, 43, 0.22);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 2147483000;
      font-family: var(--xk-font);
      border: 1px solid var(--xk-border);
    }
    #xk-panel.xk-open { display: flex; }

    #xk-header {
      background: linear-gradient(135deg, var(--xk-ink) 0%, #142042 100%);
      color: #fff;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    #xk-header-title { font-size: 15px; font-weight: 600; }
    #xk-header-sub { font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 2px; }
    #xk-close {
      background: transparent;
      border: none;
      color: rgba(255,255,255,0.8);
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
      padding: 4px;
    }
    #xk-close:hover { color: #fff; }

    #xk-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: var(--xk-bg-soft);
    }
    .xk-msg {
      max-width: 82%;
      padding: 10px 13px;
      border-radius: 12px;
      font-size: 13.5px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .xk-msg-bot {
      align-self: flex-start;
      background: #fff;
      color: var(--xk-ink);
      border: 1px solid var(--xk-border);
      border-bottom-left-radius: 4px;
    }
    .xk-msg-user {
      align-self: flex-end;
      background: var(--xk-accent);
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .xk-msg-sources {
      align-self: flex-start;
      font-size: 11px;
      color: var(--xk-muted);
      margin-top: -4px;
      max-width: 82%;
    }
    .xk-msg-sources a { color: var(--xk-accent); text-decoration: none; }
    .xk-msg-sources a:hover { text-decoration: underline; }

    .xk-typing { display: flex; gap: 3px; padding: 4px 0; }
    .xk-typing span {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--xk-muted);
      animation: xk-bounce 1.2s infinite ease-in-out;
    }
    .xk-typing span:nth-child(2) { animation-delay: 0.15s; }
    .xk-typing span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes xk-bounce {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
      30% { transform: translateY(-4px); opacity: 1; }
    }

    #xk-input-row {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      padding: 12px;
      border-top: 1px solid var(--xk-border);
      background: #fff;
      flex-shrink: 0;
    }
    #xk-input {
      flex: 1;
      resize: none;
      border: 1px solid var(--xk-border);
      border-radius: 10px;
      padding: 9px 11px;
      font-size: 13.5px;
      font-family: var(--xk-font);
      max-height: 90px;
      outline: none;
    }
    #xk-input:focus { border-color: var(--xk-accent); }
    #xk-send {
      background: var(--xk-accent);
      color: #fff;
      border: none;
      border-radius: 10px;
      width: 36px;
      height: 36px;
      flex-shrink: 0;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #xk-send:hover { background: var(--xk-accent-ink); }
    #xk-send:disabled { opacity: 0.5; cursor: not-allowed; }
    #xk-send svg { width: 16px; height: 16px; }

    @media (prefers-reduced-motion: reduce) {
      #xk-launcher, .xk-typing span { transition: none; animation: none; }
    }
  `;

  var styleEl = document.createElement("style");
  styleEl.textContent = STYLE;
  document.head.appendChild(styleEl);

  // ---------------------------------------------------------------------
  // DOM
  // ---------------------------------------------------------------------
  var launcher = document.createElement("button");
  launcher.id = "xk-launcher";
  launcher.setAttribute("aria-label", "Open chat with " + config.title);
  launcher.innerHTML =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>';

  var panel = document.createElement("div");
  panel.id = "xk-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", config.title);
  panel.innerHTML =
    '<div id="xk-header">' +
    '<div><div id="xk-header-title"></div><div id="xk-header-sub">XICTEK Systems</div></div>' +
    '<button id="xk-close" aria-label="Close chat">\u00D7</button>' +
    "</div>" +
    '<div id="xk-messages"></div>' +
    '<div id="xk-input-row">' +
    '<textarea id="xk-input" rows="1" placeholder="Ask a question…" aria-label="Message"></textarea>' +
    '<button id="xk-send" aria-label="Send message">' +
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>' +
    "</button>" +
    "</div>";

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  panel.querySelector("#xk-header-title").textContent = config.title;

  var messagesEl = panel.querySelector("#xk-messages");
  var inputEl = panel.querySelector("#xk-input");
  var sendEl = panel.querySelector("#xk-send");
  var closeEl = panel.querySelector("#xk-close");

  var conversationId =
    "widget-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  var history = [];
  var opened = false;

  function appendMessage(role, text) {
    var el = document.createElement("div");
    el.className = "xk-msg " + (role === "user" ? "xk-msg-user" : "xk-msg-bot");
    el.textContent = text;
    messagesEl.appendChild(el);
    return el;
  }

  function appendSources(sources) {
    if (!sources || !sources.length) return;
    var el = document.createElement("div");
    el.className = "xk-msg-sources";
    var label = document.createElement("div");
    label.textContent = "Sources: ";
    sources.forEach(function (s, i) {
      var link = s.url
        ? '<a href="' + s.url + '" target="_blank" rel="noopener">' + s.title + "</a>"
        : s.title;
      label.innerHTML += link + (i < sources.length - 1 ? ", " : "");
    });
    el.appendChild(label);
    messagesEl.appendChild(el);
  }

  function showTyping() {
    var el = document.createElement("div");
    el.className = "xk-msg xk-msg-bot xk-typing-wrap";
    el.innerHTML = '<div class="xk-typing"><span></span><span></span><span></span></div>';
    messagesEl.appendChild(el);
    scrollToBottom();
    return el;
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setSending(isSending) {
    sendEl.disabled = isSending;
    inputEl.disabled = isSending;
  }

  function sendMessage() {
    var text = inputEl.value.trim();
    if (!text) return;

    appendMessage("user", text);
    history.push({ role: "user", content: text });
    inputEl.value = "";
    inputEl.style.height = "auto";
    scrollToBottom();
    setSending(true);

    var typingEl = showTyping();

    fetch(config.apiBase.replace(/\/$/, "") + "/api/v1/xictek/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Token": config.apiToken,
      },
      body: JSON.stringify({
        message: text,
        conversation_id: conversationId,
        // Cap forwarded history so a long-running chat doesn't grow the
        // request body unboundedly.
        history: history.slice(-10),
      }),
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp
            .json()
            .catch(function () {
              return {};
            })
            .then(function (body) {
              throw new Error(body.message || "Request failed (" + resp.status + ")");
            });
        }
        return resp.json();
      })
      .then(function (data) {
        typingEl.remove();
        appendMessage("assistant", data.reply);
        appendSources(data.sources);
        history.push({ role: "assistant", content: data.reply });
        scrollToBottom();
      })
      .catch(function (err) {
        typingEl.remove();
        appendMessage(
          "assistant",
          "Sorry, something went wrong reaching the assistant. Please try again in a moment."
        );
        console.error("[xictek-widget]", err);
      })
      .finally(function () {
        setSending(false);
        inputEl.focus();
      });
  }

  function openPanel() {
    panel.classList.add("xk-open");
    opened = true;
    if (!messagesEl.children.length) {
      appendMessage("assistant", config.greeting);
    }
    inputEl.focus();
  }

  function closePanel() {
    panel.classList.remove("xk-open");
  }

  launcher.addEventListener("click", function () {
    if (panel.classList.contains("xk-open")) {
      closePanel();
    } else {
      openPanel();
    }
  });
  closeEl.addEventListener("click", closePanel);

  sendEl.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  inputEl.addEventListener("input", function () {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 90) + "px";
  });
})();
