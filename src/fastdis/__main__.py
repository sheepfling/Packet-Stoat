"""CLI entrypoint for FASTDIS."""

from .catalog import supported_pdu_families, supported_protocol_versions


def main() -> None:
    print("FASTDIS support surface")
    print(f"Protocol versions: {', '.join(str(version) for version in supported_protocol_versions())}")
    print(f"PDU families: {', '.join(supported_pdu_families())}")


if __name__ == "__main__":
    main()
