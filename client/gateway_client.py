#!/usr/bin/env python3
"""Client for the persistent local speech server + gateway processor."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Call local speech server and then run gateway on returned events.")
    parser.add_argument("audio_path")
    parser.add_argument("--server", default="http://127.0.0.1:8765")
    parser.add_argument("--gateway-output", default="reports/client_gateway_report.md")
    parser.add_argument("--events-output-name")
    parser.add_argument("--vad-only", action="store_true", help="Ask server to run only VAD adapter.")
    args = parser.parse_args()

    payload = {"audio_path": str(Path(args.audio_path).expanduser())}
    if args.events_output_name:
        payload["output_name"] = args.events_output_name
    if args.vad_only:
        payload["vad_only"] = True
    result = post_json(args.server.rstrip("/") + "/v1/transcribe", payload)
    if not result.get("ok"):
        raise SystemExit(json.dumps(result, ensure_ascii=False, indent=2))

    events_path = result["events_path"]
    from scripts.duplex_voice_gateway import load_events, process_events, write_markdown_report, print_summary

    state = process_events(load_events(Path(events_path)))
    report_path = write_markdown_report(state, Path(events_path), Path(args.gateway_output))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print_summary(state, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
