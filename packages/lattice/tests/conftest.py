from __future__ import annotations

import sys
from pathlib import Path


LATTICE_SRC = Path(__file__).resolve().parents[1] / "src"
if str(LATTICE_SRC) not in sys.path:
    sys.path.insert(0, str(LATTICE_SRC))
