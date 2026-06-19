from __future__ import annotations

import argparse

from ..replay import write_v1_packets
from ._shared import receive_udp_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Capture UDP payloads into a `.fastdispkt` replay.")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--max-packets", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    packets = receive_udp_packets(
        bind_host=args.bind,
        port=args.port,
        max_packets=args.max_packets,
        timeout_s=args.timeout,
    )
    count = write_v1_packets(args.out, packets)
    print(f"captured {count} packet(s) into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
