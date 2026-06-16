#!/usr/bin/env python3
"""Prepare/download ModelScope voice models.

This script intentionally downloads model snapshots only when the user runs it.
It keeps the repository light while giving reviewers a concrete setup path for
the real local speech chain.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MODELS = [
    "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "iic/SenseVoiceSmall",
    "iic/CosyVoice2-0.5B",
    "TEN-framework/TEN_Turn_Detection",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Download ModelScope model snapshots used by the voice gateway roadmap.")
    parser.add_argument("--cache-dir", default="models/modelscope")
    parser.add_argument("--model", action="append", dest="models", help="Model id to download. Can repeat.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    model_ids = args.models or DEFAULT_MODELS
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(json.dumps({"cache_dir": str(cache_dir), "models": model_ids}, ensure_ascii=False, indent=2))
        return 0

    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError as exc:
        raise SystemExit("modelscope is not installed. Run `pip install -r requirements.txt`.") from exc

    results = {}
    for model_id in model_ids:
        path = snapshot_download(model_id, cache_dir=str(cache_dir))
        results[model_id] = path
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
