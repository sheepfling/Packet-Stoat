from __future__ import annotations

import argparse

from ..replay import read_v1_packets
from ._shared import send_udp_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Send a `.fastdispkt` replay over UDP.")
    parser.add_argument("replay")
    parser.add_argument("--dst", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--rate-hz", type=float, default=0.0)
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    packets = read_v1_packets(args.replay)
    sent = send_udp_packets(packets=packets, host=args.dst, port=args.port, rate_hz=args.rate_hz)
    print(f"sent {sent} replay packet(s) to {args.dst}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
