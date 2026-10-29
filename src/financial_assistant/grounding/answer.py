"""Evidence-based answers from the approved knowledge base.

Rules (docs/grounded-answer-rules.md):
  R1  Clarify first: a message with no topic ("how?", "kaise?") or a one-word topic that matches different
      sections gets ONE clarifying question, never a guessed answer.
  R2  No source, no facts: when nothing passes the measured retrieval threshold, or the router sent the message
      outside the knowledge route, the reply says so and gives a useful next step. It states no product facts
      except the support contact, which is itself from the KB.
  R3  Conflicts are shown, not resolved: a passage marked needs_confirmation (sources disagree) is answered with
      every version, its source and its date, and the turn is flagged for review.
  R4  Cite only what supports: every citation [n] must be backed by passage n (word overlap check); unsupported
      citations are removed, unsupported sentences are dropped, and a reply left with no support becomes R2.
  R5  Show sources: each reply that uses the KB ends with the page title, section and link of every cited passage.
  R6  Legal pages (usage reference_only) are quoted with their section and link, never paraphrased into advice.
  R8  When the cited source answers a neighbouring question (its heading does not cover the user's topic), its
      leading "Yes" / "No" is dropped and the reply names the help topic the text comes from.
  R9  One source unless needed: a second passage is cited only when the first leaves over half the question
      uncovered and the second covers at least half of it.
  R7  Urdu and Roman Urdu: the frame (intro, question, fallback) is in the user's language; the evidence is the
      English source text quoted verbatim, because a translated answer cannot be checked against its source.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from ..prompts import GROUNDING_RULES
from .retrieval import Passage, load_kb, normalise, rewrite, to_passage, tokens

log = logging.getLogger("hisabdo.ai.grounding")

SUPPORT_MIN = 0.5          # share of a sentence's content words that must appear in the cited passage
SWITCH_MARGIN = 0.2        # cite a different retrieved source when it supports the sentence this much better
MAX_SENTENCES_PER_PASSAGE = 3

ROMAN_URDU_CUES = {"kya", "hai", "hain", "kaise", "kaisay", "mein", "karun", "karte", "kar", "sakta", "sakti",
                   "hota", "hoti", "nahi", "aur", "ko", "se", "ka", "ki", "ke", "batao", "chahiye", "kyun", "kab"}
QUESTION_ONLY = {"how", "what", "why", "when", "where", "which", "who", "help", "please", "tell", "explain", "kaise",
                 "kya", "kyun", "kab", "kahan", "kaun", "kon", "madad", "batao", "bataen", "bataiye", "this", "that",
                 "it", "work", "works", "use", "app", "hisabdo", "sir", "plz", "pls", "karun", "kare", "karen",
                 "chahiye", "hota", "hoti", "hai", "hain", "about", "info", "information", "question",
                 "کیسے", "کیا", "مدد", "بتائیں", "بتاؤ", "کیوں", "کب", "کہاں",
                 # verbs and function words that say nothing about the topic
                 "have", "has", "had", "get", "got", "can", "could", "need", "want", "make", "give", "there", "any",
                 "using", "used", "find", "know", "should", "would", "will", "may", "might", "must", "also", "way",
                 "like", "much", "many", "some", "one", "possible", "able", "ok", "okay", "yes", "no"}

TEMPLATES = {
    "en": {
        "sources": "Sources:",
        "fallback": ("I couldn't find this in HisabDo's official help pages, so I won't guess. You can ask HisabDo support "
                     "at hisabdo.app@gmail.com or through the Contact page (https://hisabdo.app/contact); they aim to "
                     "reply within 48 hours. You can also rephrase the question or ask about a specific feature, such "
                     "as PDF reports, backup or customer udhar."),
        "out_of_scope": ("I can help with HisabDo and with bookkeeping for your business, but I don't have reliable "
                         "information on that. Try asking about a HisabDo feature, such as PDF reports, backup or "
                         "customer udhar, or contact HisabDo support at hisabdo.app@gmail.com."),
        "advice": " For advice specific to your business, please consult a qualified accountant.",
        "clarify_open": ("Which part of HisabDo do you need help with? For example: customers and udhar, expenses, "
                         "PDF reports, backup, or using the app without internet."),
        "clarify_pick": 'Do you mean "{a}" or "{b}"?',
        "conflict": ("HisabDo's official sources don't agree on this yet, so I can't give you one answer. "
                     "I've flagged it for review."),
        "legal": 'The {title} says, in "{section}":',
        "related": 'I found this on the related help topic "{heading}":',
        "evidence": "",
    },
    "roman_ur": {
        "sources": "Sources:",
        "fallback": ("Mujhe yeh HisabDo ke official help pages mein nahi mila, is liye main andaza nahi lagaunga. Aap "
                     "HisabDo support se hisabdo.app@gmail.com par ya Contact page (https://hisabdo.app/contact) se "
                     "rabta kar sakte hain; woh 48 ghante mein jawab dene ki koshish karte hain. Aap sawal doosre "
                     "alfaaz mein bhi pooch sakte hain, maslan PDF reports, backup ya customer udhar ke baare mein."),
        "out_of_scope": ("Main HisabDo aur aap ke business ke hisaab kitaab mein madad kar sakta hoon, lekin is baare "
                         "mein mere paas qabil e aitbaar maloomat nahi hai. HisabDo ke kisi feature ke baare mein "
                         "poochein, ya support se hisabdo.app@gmail.com par rabta karein."),
        "advice": " Apne business ke liye makhsoos mashwaray ke liye kisi qualified accountant se rabta karein.",
        "clarify_open": ("Aap ko HisabDo ke kis hissay mein madad chahiye? Maslan: customers aur udhar, kharcha, PDF "
                         "reports, backup, ya internet ke baghair istemal."),
        "clarify_pick": 'Kya aap ka matlab "{a}" hai, ya "{b}"?',
        "conflict": ("HisabDo ke official sources is baare mein abhi mutafiq nahi hain, is liye main ek jawab nahi de "
                     "sakta. Maine isay review ke liye flag kar diya hai."),
        "legal": '{title} mein "{section}" ke tehat likha hai:',
        "related": 'Mujhe yeh mutalliqa help topic "{heading}" par mila:',
        "evidence": "HisabDo ke official page ke mutabiq (English mein):",
    },
    "ur": {
        "sources": "ذرائع:",
        "fallback": ("مجھے یہ حساب دو کے آفیشل ہیلپ پیجز میں نہیں ملا، اس لیے میں اندازہ نہیں لگاؤں گا۔ آپ حساب دو سپورٹ سے "
                     "hisabdo.app@gmail.com پر یا Contact page (https://hisabdo.app/contact) سے رابطہ کر سکتے ہیں؛ وہ "
                     "48 گھنٹے میں جواب دینے کی کوشش کرتے ہیں۔ آپ سوال دوسرے الفاظ میں بھی پوچھ سکتے ہیں۔"),
        "out_of_scope": ("میں حساب دو اور آپ کے کاروبار کے حساب کتاب میں مدد کر سکتا ہوں، لیکن اس بارے میں میرے پاس قابلِ "
                         "اعتبار معلومات نہیں ہیں۔ حساب دو کے کسی فیچر کے بارے میں پوچھیں، یا سپورٹ سے "
                         "hisabdo.app@gmail.com پر رابطہ کریں۔"),
        "advice": " اپنے کاروبار کے لیے مخصوص مشورے کے لیے کسی مستند اکاؤنٹنٹ سے رابطہ کریں۔",
        "clarify_open": ("آپ کو حساب دو کے کس حصے میں مدد چاہیے؟ مثلاً: گاہک اور ادھار، خرچہ، پی ڈی ایف رپورٹس، بیک اپ، یا "
                         "انٹرنیٹ کے بغیر استعمال۔"),
        "clarify_pick": 'کیا آپ کا مطلب "{a}" ہے، یا "{b}"؟',
        "conflict": ("حساب دو کے آفیشل ذرائع اس بارے میں ابھی متفق نہیں ہیں، اس لیے میں ایک جواب نہیں دے سکتا۔ میں نے "
                     "اسے ریویو کے لیے فلیگ کر دیا ہے۔"),
        "legal": '{title} میں "{section}" کے تحت لکھا ہے:',
        "related": 'مجھے یہ متعلقہ ہیلپ ٹاپک "{heading}" پر ملا:',
        "evidence": "حساب دو کے آفیشل پیج کے مطابق (انگریزی میں):",
    },
}

# "What is HisabDo?" names its topic: the app itself. (HisabDo / app are not topic words for the relevance check,
# because nearly every passage contains them.)
PRODUCT_NAME = re.compile(r"hisab\s*do|\bapp\b|حساب\s*دو|ہساب\s*دو", re.I)

ADVICE_WORDS = re.compile(r"\b(tax|taxes|fbr|legal|lawyer|loan|invest\w*|zakat|audit)\b", re.I)


@dataclass
class Citation:
    n: int
    chunk_id: str
    label: str           # page title › section
    url: str
    last_updated: str | None


@dataclass
class GroundedAnswer:
    reply: str
    status: str          # answered | conflict | no_source | out_of_scope | clarify
    citations: list[Citation] = field(default_factory=list)
    needs_review: bool = False
    review_reason: str | None = None
    language: str = "en"


# ------------------------------------------------------------------------------------ helpers


def detect_language(text: str) -> str:
    if re.search(r"[؀-ۿ]", text):
        return "ur"
    words = set(normalise(text).split())
    return "roman_ur" if len(words & ROMAN_URDU_CUES) >= 2 else "en"


def content_words(text: str) -> set[str]:
    return set(tokens(text))


URDU_PUNCTUATION = re.compile("[،؛؟۔]")  # ، ؛ ؟ ۔ sit inside the Urdu letter range


def topic_words(text: str) -> set[str]:
    return {w for w in content_words(normalise(URDU_PUNCTUATION.sub(" ", text))) if w not in QUESTION_ONLY}


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.replace("\n- ", " ").replace("\n", " ")).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def support(sentence: str, p: Passage) -> float:
    """Share of the sentence's content words that appear in the passage (heading + body)."""
    words = content_words(re.sub(r"\[\d+\]", " ", sentence))
    if not words:
        return 1.0
    return len(words & content_words(f"{p.heading} {p.body}")) / len(words)


def matches(word: str, vocab: set[str]) -> bool:
    """Exact word, or the same first 5 letters (currency / currencies, backup / backups)."""
    return word in vocab or (len(word) >= 5 and any(v[:5] == word[:5] for v in vocab if len(v) >= 5))


def coverage(topic: set[str], p: Passage) -> set[str]:
    """The question's topic words that the passage actually talks about."""
    vocab = content_words(f"{p.heading} {p.body}")
    return {w for w in topic if matches(w, vocab)}


def relevant(topic: set[str], p: Passage) -> bool:
    """R4 at passage level: a passage that covers none (or under a third) of the question's topic words is not
    evidence for it, whatever its retrieval score."""
    return bool(topic) and len(coverage(topic, p)) >= max(1, len(topic) / 3)


def excerpt(p: Passage, focus: set[str] | None = None, limit: int = MAX_SENTENCES_PER_PASSAGE) -> str:
    """The passage's first sentences, or with `focus`, the sentences that mention the question's topic first."""
    parts = sentences(re.sub(r"#+\s*", "", p.body))
    if focus:
        hits = [x for x in parts if coverage(focus, Passage(**{**p.__dict__, "heading": "", "body": x}))]
        parts = hits or parts
    return " ".join(parts[:limit])


# ------------------------------------------------------------------------------------ the answerer


class GroundedAnswerer:
    def __init__(self, retriever, kb_chunks: list[dict] | None = None):
        self.retriever = retriever
        chunks = kb_chunks if kb_chunks is not None else getattr(retriever, "chunks", None) or load_kb()
        # Passages that share a conflict note belong to one conflict group (built at cleaning time, audit C-06).
        # Words that occur anywhere in the KB: a topic word outside it (a Roman Urdu verb, say) cannot appear in any
        # heading, so R8 ignores it when deciding whether a source answers this question or a neighbouring one.
        self.vocab = {w for c in chunks for w in content_words(f"{c['heading']} {c['body']}")}
        self.conflict_groups: dict[str, list[Passage]] = {}
        for c in chunks:
            if c.get("status") == "needs_confirmation" and c.get("notes"):
                self.conflict_groups.setdefault(c["notes"][0], []).append(to_passage(c))

    # R1 -----------------------------------------------------------------------------------------------------
    def clarify(self, message: str, passages: list[Passage], lang: str) -> str | None:
        topic = topic_words(message)
        if not topic:
            return None if PRODUCT_NAME.search(message) else TEMPLATES[lang]["clarify_open"]
        if len(topic) == 1 and len(passages) >= 2 and passages[0].heading != passages[1].heading:
            a, b = (p.heading.rstrip("?") for p in passages[:2])
            return TEMPLATES[lang]["clarify_pick"].format(a=a, b=b)
        return None

    # R2 -----------------------------------------------------------------------------------------------------
    def fallback(self, message: str, lang: str, out_of_scope: bool = False) -> GroundedAnswer:
        t = TEMPLATES[lang]
        reply = t["out_of_scope"] if out_of_scope else t["fallback"]
        if ADVICE_WORDS.search(message):
            reply += t["advice"]
        return GroundedAnswer(reply=reply, status="out_of_scope" if out_of_scope else "no_source", language=lang)

    # R3 -----------------------------------------------------------------------------------------------------
    def conflict(self, passages: list[Passage], lang: str, focus: set[str] | None = None) -> GroundedAnswer | None:
        flagged = next((p for p in passages if p.status == "needs_confirmation" and p.notes), None)
        if not flagged:
            return None
        group = self.conflict_groups.get(flagged.notes[0], [flagged])
        lines, cites = [TEMPLATES[lang]["conflict"]], []
        for n, p in enumerate(group, 1):
            date = p.last_updated or "no date shown"
            lines.append(f"[{n}] {p.label} ({date}): {excerpt(p, focus)}")
            cites.append(Citation(n, p.chunk_id, p.label, p.source_url, p.last_updated))
        reason = flagged.notes[0]
        log.warning("kb_conflict", extra={"chunks": [c.chunk_id for c in cites]})  # ids only, never user text
        return GroundedAnswer(reply=self._with_sources("\n".join(lines), cites, lang), status="conflict",
                              citations=cites, needs_review=True, review_reason=reason, language=lang)

    # R4 + R5 + R6 ------------------------------------------------------------------------------------------
    def extractive(self, passages: list[Passage], lang: str, topic: set[str] | None = None,
                   asked_topic: set[str] | None = None) -> GroundedAnswer:
        """The answer is the source text itself (mock provider, and every non-English reply: R7)."""
        t, parts, cites, covered = TEMPLATES[lang], [], [], set()
        if t["evidence"]:
            parts.append(t["evidence"])
        for p in passages:
            new = coverage(topic or set(), p) - covered
            if cites and (len(covered) >= len(topic or ()) / 2 or not new
                          or len(coverage(topic or set(), p)) < len(topic or ()) / 2):
                continue  # a second source only when the first leaves over half the question uncovered
            covered |= coverage(topic or set(), p)
            text = excerpt(p)
            n = len(cites) + 1
            if p.usage == "reference_only":
                parts.append(f'{t["legal"].format(title=p.title, section=p.section)} "{text}" [{n}]')
            elif ((asked := {w for w in asked_topic or () if matches(w, self.vocab)})
                  and coverage(asked, Passage(**{**p.__dict__, "body": ""})) != asked):
                # R8: the source answers a neighbouring question. Its "Yes." / "No." is not an answer to this one,
                # so drop it and say which help topic the text is from.
                text = re.sub(r"^(yes|no)\b[.,!]?\s*", "", text, flags=re.I)
                parts.append(f'{t["related"].format(heading=p.heading)} {text} [{n}]')
            else:
                parts.append(f"{text} [{n}]")
            cites.append(Citation(n, p.chunk_id, p.label, p.source_url, p.last_updated))
        return GroundedAnswer(reply=self._with_sources("\n\n".join(parts), cites, lang), status="answered",
                              citations=cites, language=lang)

    def verify(self, draft: str, passages: list[Passage], lang: str) -> GroundedAnswer | None:
        """Keep a model's draft only where the passages support it (R4). None = nothing supported."""
        kept, used = [], {}
        draft = re.sub(r"\n*Sources?:.*", "", draft, flags=re.S)
        # "fact. [2] Next fact." -> "fact [2]. Next fact.": a marker after the full stop belongs to that sentence
        draft = re.sub(r"([.!?])\s*((?:\[\d+\]\s*)+)", lambda m: f" {m.group(2).strip()}{m.group(1)} ", draft)
        for s in sentences(draft):
            if not content_words(re.sub(r"\[\d+\]", " ", s)):
                continue  # a marker or punctuation left on its own carries no claim
            marks = [int(m) for m in re.findall(r"\[(\d+)\]", s) if 1 <= int(m) <= len(passages)]
            good = [m for m in marks if support(s, passages[m - 1]) >= SUPPORT_MIN]
            best = max(range(len(passages)), key=lambda i: support(s, passages[i]))
            if not good:  # uncited, or cited wrongly: keep it only if some passage supports it
                if support(s, passages[best]) < SUPPORT_MIN:
                    log.info("grounding_dropped_sentence", extra={"reason": "unsupported"})
                    continue
                good = [best + 1]
            elif support(s, passages[best]) >= max(support(s, passages[m - 1]) for m in good) + SWITCH_MARGIN:
                good = [best + 1]  # another retrieved source states the fact clearly better: cite that one
            text = re.sub(r"\s*\[\d+\]", "", s).rstrip()
            for m in good:
                used.setdefault(m, len(used) + 1)
            kept.append(text + "".join(f" [{used[m]}]" for m in good))
        if not kept:
            return None
        cites = [Citation(new, passages[old - 1].chunk_id, passages[old - 1].label, passages[old - 1].source_url,
                          passages[old - 1].last_updated) for old, new in sorted(used.items(), key=lambda kv: kv[1])]
        return GroundedAnswer(reply=self._with_sources(" ".join(kept), cites, lang), status="answered",
                              citations=cites, language=lang)

    # ---------------------------------------------------------------------------------------------------------
    def answer(self, message: str, provider=None, history: list[dict] | None = None,
               kb_allowed: bool = True) -> GroundedAnswer:
        lang = detect_language(message)
        if not topic_words(message) and not PRODUCT_NAME.search(message):
            return GroundedAnswer(reply=TEMPLATES[lang]["clarify_open"], status="clarify", language=lang)
        if not kb_allowed:
            return self.fallback(message, lang, out_of_scope=True)
        # Latin-script words only: the KB is English, so Urdu-script words are represented by their glossary terms.
        topic = {w for w in topic_words(rewrite(message)) if re.fullmatch(r"[a-z0-9]+", w)}
        passages = [p for p in self.retriever.retrieve(message) if not topic or relevant(topic, p)]
        question = self.clarify(message, passages, lang)
        if question:
            return GroundedAnswer(reply=question, status="clarify", language=lang)
        if not passages:
            return self.fallback(message, lang)
        if (c := self.conflict(passages, lang, topic)) is not None:
            return c
        if provider is None or lang != "en" or getattr(provider, "extractive", False) or \
                type(provider).__name__ == "MockLLMProvider":
            # R8 compares the user's own words with the heading; the rewrite's added synonyms are not what was asked.
            return self.extractive(passages, lang, topic, asked_topic=topic_words(message))
        draft, _ = provider.generate_reply(message, context=numbered_context(passages), history=history)
        return self.verify(draft, passages, lang) or self.fallback(message, lang)

    @staticmethod
    def _with_sources(body: str, cites: list[Citation], lang: str) -> str:
        if not cites:
            return body
        lines = [f"[{c.n}] {c.label}: {c.url}" for c in cites]
        return f"{body}\n\n{TEMPLATES[lang]['sources']}\n" + "\n".join(lines)


def numbered_context(passages: list[Passage]) -> str:
    """Context handed to a real model: numbered sources it may cite (see GROUNDING_RULES in prompts.py)."""
    blocks = []
    for n, p in enumerate(passages, 1):
        kind = "legal page: quote it, do not interpret it" if p.usage == "reference_only" else "help page"
        blocks.append(f"[{n}] {p.label} ({p.source_url}; {kind}; updated {p.last_updated or 'not shown'})\n{p.body}")
    return GROUNDING_RULES + "\n\n" + "\n\n".join(blocks)
