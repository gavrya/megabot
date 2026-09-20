"""Seed runner: executes every `seeders/seed_NNN_<name>.py` module that exposes `run(session)`."""

import argparse
import asyncio
import importlib
import pkgutil
from collections.abc import Sequence
from pathlib import Path

from app.core.database import engine, session_factory
from app.core.logging import configure_logging, get_logger

logger = get_logger("seeders")

SEEDERS_DIR = Path(__file__).parent


def discover(only: str | None = None) -> list[str]:
    names = sorted(
        module.name
        for module in pkgutil.iter_modules([str(SEEDERS_DIR)])
        if module.name != "runner"
    )
    if only:
        names = [name for name in names if only in name]
    return names


async def run_seeders(names: Sequence[str]) -> None:
    async with session_factory() as session:
        for name in names:
            module = importlib.import_module(f"seeders.{name}")
            run = getattr(module, "run", None)
            if run is None:
                logger.warning("skipping %s: no run(session) function", name)
                continue
            logger.info("seeding %s", name)
            await run(session)
            await session.commit()
    await engine.dispose()


async def _main(only: str | None) -> None:
    names = discover(only)
    if not names:
        logger.warning("no seeders found")
        return
    await run_seeders(names)
    logger.info("seeding finished: %s", ", ".join(names))


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run database seeders")
    parser.add_argument("--only", help="run only seeders whose name contains this substring")
    args = parser.parse_args()
    asyncio.run(_main(args.only))


if __name__ == "__main__":
    main()
