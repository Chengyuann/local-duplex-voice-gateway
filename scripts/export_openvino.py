#!/usr/bin/env python3
"""OpenVINO export helper.

For models supported by Optimum Intel, this wrapper records the exact export
command. Some ModelScope/FunASR speech models may require custom conversion;
when export is unsupported, keep the command and runtime check output as
evidence and use `adapters/openvino_placeholder.py` to benchmark exported IR.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a HuggingFace/Optimum-compatible model to OpenVINO IR.")
    parser.add_argument("--model", required=True, help="Model id or local path accepted by optimum-cli")
    parser.add_argument("--task", default="automatic-speech-recognition")
    parser.add_argument("--output", default="models/openvino/exported")
    parser.add_argument("--extra", action="append", default=[], help="Extra argument passed to optimum-cli")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    cmd = [
        "optimum-cli",
        "export",
        "openvino",
        "--model",
        args.model,
        "--task",
        args.task,
        str(output),
    ] + args.extra

    if args.dry_run:
        print(json.dumps({"command": cmd}, ensure_ascii=False, indent=2))
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(cmd, text=True, capture_output=True)
    report = {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/openvino_export_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
