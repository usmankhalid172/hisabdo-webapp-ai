"""
XICTEK Website Assistant — AI chatbot for XICTEK Systems' public website
(xicteksystems.com), covering company info, services, technologies,
HisabDo, careers, blog, and FAQ content.

Deliberately separate from `src.financial_assistant` (the HisabDo product
chatbot): different owner content, different knowledge base, different
audience (public website visitors vs. HisabDo app users). Kept as its own
top-level package — not a submodule of `financial_assistant` — so it can be
lifted out wholesale once the real xicteksystems.com integration is scoped.

See README.md in this folder for architecture, setup, and re-indexing docs.
"""
