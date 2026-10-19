"""Conservative post-processing for multi-item Core Services answers."""
from __future__ import annotations

import re

_LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+(.+?)\s*$")
_LIST_LEAD_RE = re.compile(
    r"^(?P<intro>.*?(?:\b(?:include|includes|offer|offers|provide|provides|use|uses)\b\s*:?|:))\s*(?P<body>.+)$",
    re.IGNORECASE,
)
_SEMICOLON_SEPARATOR_RE = re.compile(r"\s*;\s*")
_COMMA_SEPARATOR_RE = re.compile(r"\s*,\s*")
_FINAL_CONJUNCTION_RE = re.compile(r"^(?:and|or)\s+", re.IGNORECASE)
_CONJUNCTION_RE = re.compile(r"\s+(?:and|or)\s+", re.IGNORECASE)


def _clean_item(value: str) -> str:
    """Collapse whitespace and remove list punctuation at item boundaries."""
    return re.sub(r"\s+", " ", value).strip().strip(" ,;:")


def _unique_items(items: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for raw_item in items:
        item = _clean_item(raw_item)
        key = item.casefold()
        if item and key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _render_list(items: list[str], intro: str = "") -> str:
    clean_intro = intro.strip()
    if clean_intro:
        clean_intro = clean_intro.rstrip(" .!?:;") + ":"
    bullets = "\n".join(f"- {item}" for item in items)
    return f"{clean_intro}\n{bullets}" if clean_intro else bullets


def _format_markdown_list(text: str) -> str | None:
    lines = text.splitlines()
    marked_lines = [
        (index, match.group(1))
        for index, line in enumerate(lines)
        if (match := _LIST_MARKER_RE.match(line))
    ]
    items = _unique_items([item for _, item in marked_lines])
    if len(items) < 2:
        return None

    first_index = marked_lines[0][0]
    last_index = marked_lines[-1][0]
    intro = "\n".join(line.strip() for line in lines[:first_index] if line.strip())
    suffix = "\n".join(line.strip() for line in lines[last_index + 1 :] if line.strip())
    expanded_items: list[str] = []
    for line in lines[first_index : last_index + 1]:
        match = _LIST_MARKER_RE.match(line)
        if match:
            expanded_items.append(match.group(1).strip())
        elif line.strip() and expanded_items:
            # Preserve wrapped/continuation lines as part of the preceding item.
            expanded_items[-1] = f"{expanded_items[-1]} {line.strip()}"
    items = _unique_items(expanded_items)
    formatted = _render_list(items, intro)
    return f"{formatted}\n\n{suffix}" if suffix else formatted


def _format_inline_list(text: str) -> str | None:
    # Inline-list parsing is intentionally limited to one short paragraph;
    # multiline prose can contain commas that are not item boundaries.
    if "\n" in text:
        return None

    content = text.strip()
    intro = ""
    lead = _LIST_LEAD_RE.match(content)
    if lead:
        intro = lead.group("intro").strip()
        content = lead.group("body").strip()

    content = content.rstrip(" .!?\t")
    # Allow punctuation inside names such as "Next.js", but don't split
    # across sentence boundaries or question/exclamation marks.
    if re.search(r"[!?]|\.(?:\s|$)", content):
        return None

    has_semicolons = ";" in content
    has_commas = "," in content
    explicitly_introduced = bool(intro)
    if has_semicolons:
        # Semicolons clearly separate list entries. Keep conjunctions inside
        # each entry, e.g. "LLM and OpenAI integrations".
        parts = _SEMICOLON_SEPARATOR_RE.split(content)
    elif has_commas:
        parts = _COMMA_SEPARATOR_RE.split(content)
        # Support the conventional Oxford-comma form "A, B, and C" without
        # splitting compound names joined by "and" inside an entry.
        if len(parts) > 1:
            parts[-1] = _FINAL_CONJUNCTION_RE.sub("", parts[-1])
    elif explicitly_introduced and re.search(r"\s+(?:and|or)\s+", content, re.IGNORECASE):
        # A clear list lead makes a simple conjunction safe to format while
        # ordinary prose such as "design and development" remains untouched.
        parts = _CONJUNCTION_RE.split(content)
    else:
        return None

    parts = _unique_items(parts)
    if len(parts) < 2:
        return None
    if not intro and any(len(item.split()) > 9 for item in parts):
        return None

    return _render_list(parts, intro)


def format_core_services_output(output: str) -> str:
    """Format clear multi-item service answers as concise Markdown bullets.

    Existing multi-line bullet/numbered lists are normalized to ``-`` bullets.
    A single inline list is split only when it has at least two distinct items.
    Non-list and single-item answers are returned unchanged apart from trimming
    surrounding whitespace. This function does not add facts or summarize items.
    """
    if not output or not output.strip():
        return ""

    text = output.strip()
    return _format_markdown_list(text) or _format_inline_list(text) or text
