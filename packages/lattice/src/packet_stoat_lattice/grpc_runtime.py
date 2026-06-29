from __future__ import annotations

import hashlib
from importlib import import_module
from pathlib import Path
import sys
import tempfile

from grpc_tools import protoc


ROOT = Path(__file__).resolve().parents[2]
PROTO = ROOT / "proto" / "packetstoat" / "lattice_shim" / "v1" / "lattice_shim.proto"


def load_lattice_shim_modules():
    digest = hashlib.sha256(PROTO.read_bytes()).hexdigest()[:12]
    out_root = Path(tempfile.gettempdir()) / "fastdis_grpc_codegen" / digest
    package_root = out_root / "packetstoat" / "lattice_shim" / "v1"
    pb2 = package_root / "lattice_shim_pb2.py"
    pb2_grpc = package_root / "lattice_shim_pb2_grpc.py"
    if not pb2.is_file() or not pb2_grpc.is_file():
        out_root.mkdir(parents=True, exist_ok=True)
        rc = protoc.main(
            [
                "grpc_tools.protoc",
                f"-I{ROOT / 'proto'}",
                f"--python_out={out_root}",
                f"--grpc_python_out={out_root}",
                str(PROTO),
            ]
        )
        if rc != 0:
            raise RuntimeError(f"grpc_tools.protoc failed with exit code {rc}")
    if str(out_root) not in sys.path:
        sys.path.insert(0, str(out_root))
    return (
        import_module("packetstoat.lattice_shim.v1.lattice_shim_pb2"),
        import_module("packetstoat.lattice_shim.v1.lattice_shim_pb2_grpc"),
    )


__all__ = ["load_lattice_shim_modules", "PROTO"]
