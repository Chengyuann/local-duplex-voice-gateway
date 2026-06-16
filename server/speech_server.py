#!/usr/bin/env python3
"""Persistent local ASR/VAD server.

The server keeps ModelScope/FunASR models loaded and exposes a small localhost
HTTP API. Gateway/client processes can call it repeatedly without reloading
speech models each turn.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.modelscope_speech import build_gateway_events, load_config


class SpeechService:
    def __init__(self, config_path: Path | None = None):
        self.config = load_config(config_path)

    def transcribe_to_events(self, audio_path: Path, output_path: Path, vad_only: bool = False) -> dict[str, Any]:
        config = dict(self.config)
        if vad_only:
            config["vad_only"] = True
        result = build_gateway_events(audio_path, config, output_path)
        return {
            "ok": True,
            "audio_path": result.audio_path,
            "events_path": result.events_path,
            "asr_text": result.asr_text,
            "vad_segments": result.vad_segments,
            "timings_ms": result.timings_ms,
            "vad_only": vad_only,
        }


def make_handler(service: SpeechService, output_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/health":
                self._send(200, {"ok": True, "service": "local-duplex-voice-gateway", "config": service.config})
                return
            self._send(404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/v1/transcribe":
                self._send(404, {"ok": False, "error": "not found"})
                return
            try:
                content_len = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_len)
                payload = json.loads(raw.decode("utf-8"))
                audio_path = Path(payload["audio_path"]).expanduser()
                output_name = payload.get("output_name") or f"{audio_path.stem}.events.jsonl"
                output_path = output_dir / output_name
                result = service.transcribe_to_events(audio_path, output_path, vad_only=bool(payload.get("vad_only", False)))
                self._send(200, result)
            except Exception as exc:
                self._send(500, {"ok": False, "error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            print("%s - %s" % (self.address_string(), format % args))

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a persistent local speech server for ModelScope/FunASR adapters.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", type=Path, default=Path("models/model_config.example.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/server_events"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    service = SpeechService(args.config)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(service, args.output_dir))
    print(f"Local speech server listening on http://{args.host}:{args.port}")
    print("Health: GET /health")
    print("Transcribe: POST /v1/transcribe {\"audio_path\":\"/path/to.wav\"}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
