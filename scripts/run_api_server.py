# Start the HisabDo AI Financial Assistant API server.
#
# Usage: python scripts/run_api_server.py [--port PORT]

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is importable regardless of how the script runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from src.integration.app import app

PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8000

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")