"""Compatibility entry point for ``python -m packet_stoat``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
