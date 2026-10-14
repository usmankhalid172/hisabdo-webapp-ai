"""Permanently remove conversations that were deleted more than N days ago.

Deleting a conversation in the app is a soft delete (hidden immediately,
recoverable by an admin). Run this daily from a scheduler (cron / Windows Task
Scheduler) to enforce the retention period:

    python purge_deleted_conversations.py --days 30
"""

import argparse
import os
from datetime import timedelta
from pathlib import Path

from chatbot.conversations import ConversationStore
from chatbot.repository import Repository

ROOT = Path(__file__).parent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30, help="retention period in days (default 30)")
    args = parser.parse_args()
    if args.days < 0:
        parser.error("--days must be 0 or more")

    repo = Repository(os.environ.get("CHATBOT_DB", ROOT / "data" / "app.db"))
    removed = ConversationStore(repo).purge_deleted(timedelta(days=args.days))
    print(f"Purged {removed} conversation(s) deleted more than {args.days} day(s) ago.")
