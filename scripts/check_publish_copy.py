#!/usr/bin/env python3
"""Check public-facing copy for conversation leakage and stale claims."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FILES = [
    Path("docs/article.md"),
    Path("README.md"),
    Path("docs/submission-guide.md"),
    Path("references/modelscope-voice-stack.md"),
    Path("references/model-landscape.md"),
    Path("docs/model-research-notes.md"),
]

FORBIDDEN = [
    r"你现在本机",
    r"你本机",
    r"我没有把仓库",
    r"收到预审核建议后",
    r"评审者如果",
    r"我一开始",
    r"我最初",
    r"我希望",
    r"我会继续",
    r"QwenPaw",
    r"openvino is not installed",
    r"Qwen3\.6-35B-A3B",
    r"openBMB4\.5",
]


def main() -> int:
    findings = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                line_no = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path}:{line_no}: forbidden pattern `{pattern}`")

    if findings:
        print("\n".join(findings))
        return 1

    print(f"PASS publish copy: checked {len(FILES)} public files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
