"""Compatibility entry point for ``python -m fastdis``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
