import os
BASE_URL=os.getenv("QA_BASE_URL", "")
CHAT_PATH=os.getenv("QA_CHAT_PATH", "/chat")
DOMAIN=os.getenv("QA_DOMAIN", "www.xicteksystems.com").lower()
PREFIXES=tuple(x.strip() for x in os.getenv("QA_ALLOWED_PREFIXES", "/blog/").split(",") if x.strip())
TEXT_FIELD=os.getenv("QA_RESPONSE_TEXT_FIELD", "reply")
HISTORY_MODE=os.getenv("QA_HISTORY_MODE", "payload")
TIMEOUT=int(os.getenv("QA_TIMEOUT", "60"))
