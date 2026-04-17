"""Pytest config for plain-markdown-skill/tests.

Adds ``plain-markdown-skill/scripts`` to ``sys.path`` so individual tests
can ``import normalize_math`` without fiddling with imports themselves.

No ``__init__.py`` is placed in this directory on purpose: the suite is
discovered in pytest's default rootdir mode, where adding ``__init__.py``
would flip the collector into "package mode" and require a consistent
import path up to the repo root. Conftest is the canonical hook for
shared setup.
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
