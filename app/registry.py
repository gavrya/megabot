"""Entity autoloader.

Alembic autogenerate only sees tables whose entity modules have been imported. Every
`entities/*_entity.py` under `app/` is imported here by convention — module entities and
shared ones alike — so a new entity needs no edit to this file.
"""

import importlib
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ENTITY_GLOB = "**/entities/*_entity.py"


def import_entity_modules() -> list[str]:
    """Import every entity module; returns the dotted names that were imported."""
    imported = []
    for path in sorted(APP_DIR.glob(ENTITY_GLOB)):
        dotted = "app." + ".".join(path.relative_to(APP_DIR).with_suffix("").parts)
        importlib.import_module(dotted)
        imported.append(dotted)
    return imported
