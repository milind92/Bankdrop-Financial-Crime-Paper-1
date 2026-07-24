"""Run the complete Phase 1 Markdown baseline pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run(script_name: str) -> None:
    subprocess.run([sys.executable, str(SCRIPT_DIR / script_name)], check=True)


if __name__ == "__main__":
    run("extract_phase1.py")
    run("summarise_phase1.py")
