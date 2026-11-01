#!/usr/bin/env python3
"""Reassemble the original, standalone example HTML without dependencies."""
from pathlib import Path
import hashlib
root = Path(__file__).resolve().parent.parent
parts = sorted((root / "example/parts").glob("iot_control_study.html.part*"))
if not parts:
    raise SystemExit("No example parts found")
data = b"".join(p.read_bytes() for p in parts)
EXPECTED = "552a5fbd6fd8dddd71f7bd59fa23bf9591ffea0b4643cbe0483cdcdc1b99b0c6"
if hashlib.sha256(data).hexdigest() != EXPECTED:
    raise SystemExit("Example integrity check failed")
out = root / "example/iot_control_study.html"
out.write_bytes(data)
print(f"Created {out} ({len(data)} bytes)")
