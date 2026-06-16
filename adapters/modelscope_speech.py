#!/usr/bin/env python3
"""ModelScope/FunASR adapter for Local Duplex Voice Gateway.

The dependency-free gateway accepts JSONL events. This adapter turns a local
wav/audio file into the same event contract by using ModelScope/FunASR VAD and
ASR models when they are installed locally.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


DEFAULT_CONFIG = {
    "vad_model": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "vad_revision": "v2.0.4",
    "asr_model": "iic/SenseVoiceSmall",
    "asr_revision": "master",
    "asr_device": "cpu",
    "language": "auto",
    "use_itn": True,
    "merge_vad": True,
    "merge_length_s": 15,
    "max_single_segment_time": 30000,
}


@dataclass
class AdapterResult:
    audio_path: str
    asr_text: str
    events_path: str
    vad_segments: list[Any]
    timings_ms: dict[str, float]
    config: dict[str, Any]


def load_config(path: Optional[Path]) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path and path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
    return config


def require_funasr():
    try:
        from funasr import AutoModel
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
    except ImportError as exc:
        raise RuntimeError(
            "FunASR is not installed. Run `pip install -r requirements.txt` "
            "or use JSONL demo mode."
        ) from exc
    return AutoModel, rich_transcription_postprocess


def run_vad(audio_path: Path, config: dict[str, Any]) -> tuple[list[Any], float]:
    AutoModel, _ = require_funasr()
    started = time.perf_counter()
    vad = AutoModel(
        model=config["vad_model"],
        model_revision=config.get("vad_revision"),
        disable_update=True,
    )
    result = vad.generate(input=str(audio_path))
    elapsed_ms = (time.perf_counter() - started) * 1000
    return result, elapsed_ms


def run_asr(audio_path: Path, config: dict[str, Any]) -> tuple[str, float]:
    AutoModel, rich_transcription_postprocess = require_funasr()
    started = time.perf_counter()
    asr = AutoModel(
        model=config["asr_model"],
        model_revision=config.get("asr_revision"),
        trust_remote_code=True,
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": config.get("max_single_segment_time", 30000)},
        device=config.get("asr_device", "cpu"),
        disable_update=True,
    )
    result = asr.generate(
        input=str(audio_path),
        cache={},
        language=config.get("language", "auto"),
        use_itn=bool(config.get("use_itn", True)),
        batch_size_s=int(config.get("batch_size_s", 60)),
        merge_vad=bool(config.get("merge_vad", True)),
        merge_length_s=int(config.get("merge_length_s", 15)),
    )
    text = result[0].get("text", "") if result else ""
    text = rich_transcription_postprocess(text)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return text, elapsed_ms


def vad_segments_to_events(vad_result: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    segments = extract_segments(vad_result)
    for start_ms, end_ms in segments:
        events.append({"t": round(start_ms / 1000, 3), "type": "vad_start", "text": "", "speech": True})
        events.append({"t": round(end_ms / 1000, 3), "type": "silence", "text": "", "speech": False})
    return sorted(events, key=lambda item: item["t"])


def extract_segments(vad_result: list[Any]) -> list[tuple[int, int]]:
    """Best-effort parse for common FunASR VAD result structures."""
    segments: list[tuple[int, int]] = []
    for item in vad_result if isinstance(vad_result, list) else [vad_result]:
        value = item
        if isinstance(item, dict):
            value = item.get("value") or item.get("text") or item.get("segments") or []
        if isinstance(value, list):
            for segment in value:
                if isinstance(segment, (list, tuple)) and len(segment) >= 2:
                    try:
                        segments.append((int(segment[0]), int(segment[1])))
                    except (TypeError, ValueError):
                        continue
    return segments


def build_gateway_events(audio_path: Path, config: dict[str, Any], output: Path) -> AdapterResult:
    vad_result, vad_ms = run_vad(audio_path, config)
    asr_text = ""
    asr_ms = 0.0
    if not config.get("vad_only", False):
        asr_text, asr_ms = run_asr(audio_path, config)

    events = vad_segments_to_events(vad_result)
    if asr_text:
        first_t = events[0]["t"] if events else 0.0
        last_silence = max((event["t"] for event in events if event["type"] == "silence"), default=first_t + 0.9)
        events.append({"t": round(max(0.0, first_t + 0.05), 3), "type": "asr_partial", "text": asr_text, "speech": True})
        events.append({"t": round(last_silence, 3), "type": "silence", "text": "", "speech": False})
    events = dedupe_events(sorted(events, key=lambda item: item["t"]))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n", encoding="utf-8")

    result_config = dict(config)
    if result_config.get("vad_only"):
        result_config = {
            "vad_model": result_config.get("vad_model"),
            "vad_revision": result_config.get("vad_revision"),
            "vad_only": True,
        }

    return AdapterResult(
        audio_path=str(audio_path),
        asr_text=asr_text,
        events_path=str(output),
        vad_segments=extract_segments(vad_result),
        timings_ms={"vad": round(vad_ms, 2), "asr": round(asr_ms, 2)},
        config=result_config,
    )


def dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        key = json.dumps(event, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a local wav/audio file to Gateway JSONL events using ModelScope/FunASR.")
    parser.add_argument("audio", help="Local wav/audio file")
    parser.add_argument("--config", type=Path, default=Path("models/model_config.example.json"))
    parser.add_argument("--output", "-o", type=Path, default=Path("demo/from_audio_events.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("reports/modelscope_adapter_summary.json"))
    parser.add_argument("--vad-only", action="store_true", help="Only run ModelScope VAD and emit speech/silence events.")
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    config = load_config(args.config)
    if args.vad_only:
        config["vad_only"] = True
    result = build_gateway_events(audio_path, config, args.output)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
