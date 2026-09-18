"""
Deterministic guardrails, run BEFORE the LLM is ever called.

Mirrors the pattern in `src.financial_assistant.service`'s third-party
data guard: a regex/heuristic layer that can't be talked around by an
instruction-override attempt, because it never reaches the model at all
for the patterns it catches. This is NOT a claim that regex alone stops
every injection attempt — SYSTEM_PROMPT in prompts.py is a second layer,
and the LLM's own instruction-following is a third — but it deterministically
closes off the most common/scripted attempts (the ones the task brief's
"20-30 test questions including prompt-injection attempts" will include)
without depending on the model's behavior at all.

Layers, in order (see service.py):
  1. length/abuse cap (schema + this module)              -> declined, no LLM call
  2. prompt-injection / system-prompt-extraction heuristics -> declined, no LLM call
  3. SYSTEM_PROMPT instructs the model to refuse the rest    -> model call, but hardened

KNOWN LIMITATION: the patterns below are English-only. Now that the
assistant answers in English/Urdu/Hindi/Arabic (see prompts.py), an
injection attempt phrased in Urdu, Hindi, or Arabic will NOT be caught
by this deterministic layer -- it falls through to layer 3 (the system
prompt) alone. This isn't a full bypass (the model is still instructed
to refuse), just a weaker defense-in-depth for those languages than
English gets. Translating these regexes accurately enough to be worth
trusting is a real task on its own (a wrong or overly literal
translation gives false confidence), not something to bolt on without
verification -- flagging this as a follow-up rather than shipping
untested translated patterns.
"""
import re

# Attempts to override, extract, or bypass instructions. Grouped by intent
# for readability/maintainability, all case-insensitive.
_INSTRUCTION_OVERRIDE_PATTERNS = [
    # Broad "<override verb> ... instructions/rules" catch-all: allows up
    # to 3 filler words between the verb and the noun so phrasing like
    # "disregard your prior instructions" or "forget your rules" matches
    # without needing every qualifier word enumerated individually.
    r"\b(ignore|disregard|forget)\b(?:\s+\S+){0,3}\s+(instructions?|rules)\b",
    r"\boverride (your |the )?(instructions?|system prompt|rules)\b",
    r"\byou are now\b",
    r"\bact as (if|a|an)\b.*\b(dan|jailbreak|unrestricted|no rules|anything)\b",
    r"\bdeveloper mode\b",
    r"\bjailbreak\b",
    r"\bpretend (you('| a)?re|to be)\b.*\b(unrestricted|no rules|different ai|not xictek)\b",
    r"\bdo anything now\b",
]

_PROMPT_EXTRACTION_PATTERNS = [
    r"\b(reveal|show|print|repeat|output|leak|give me|tell me)\b.{0,40}\b(system prompt|system message|your instructions?|your rules|your prompt)\b",
    # Allow a short descriptor between "your" and the noun, e.g. "your
    # exact instructions", "your full system prompt".
    r"\bwhat (is|are|were) your\b(?:\s+\S+){0,2}\s+(instructions?|system prompt|rules)\b",
    r"\brepeat\b.{0,30}\babove\b",
    r"\bverbatim\b.{0,30}\b(prompt|instructions?)\b",
]

_SECRET_PROBE_PATTERNS = [
    # No leading \b: keys/tokens are often written glued to a prefix with
    # an underscore (e.g. "GROQ_API_KEY"), which is a \w character on both
    # sides of where "api" starts — a leading \b would never fire there.
    r"api[_ -]?key",
    r"\benv(ironment)?[ _-]?var(iable)?s?\b",
    r"\.env\b",
    r"\baccess token\b",
    r"\bcredentials?\b",
    r"internal[_ -]?(service[_ -]?)?token",
]

_ALL_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (*_INSTRUCTION_OVERRIDE_PATTERNS, *_PROMPT_EXTRACTION_PATTERNS, *_SECRET_PROBE_PATTERNS)
]

INJECTION_REFUSAL_MESSAGE = (
    "I can only help with questions about XICTEK Systems and HisabDo — "
    "I'm not able to share internal instructions, system details, or act outside that scope."
)

OUT_OF_SCOPE_HINT = (
    "That's outside what I can help with here — I'm the XICTEK Systems website assistant, "
    "so I can answer questions about our services, technologies, HisabDo, careers, or blog content."
)


def looks_like_injection_or_extraction(message: str) -> bool:
    return any(pattern.search(message) for pattern in _ALL_INJECTION_PATTERNS)


def exceeds_length_limit(message: str, max_chars: int) -> bool:
    return len(message) > max_chars
