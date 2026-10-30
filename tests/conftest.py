"""Die Module liegen flach im Projektordner: ihn für die Tests importierbar machen."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
