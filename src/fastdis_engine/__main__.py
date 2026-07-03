"""Compatibility entry point for ``python -m fastdis_engine``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
