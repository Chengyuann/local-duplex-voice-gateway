#!/usr/bin/env python3
"""OpenVINO EOU policy adapter.

This module creates and runs a tiny OpenVINO IR model for end-of-utterance
policy scoring. It is intentionally lightweight: the model consumes four local
turn-taking features and outputs [hold_score, commit_score]. It proves the
Gateway can call an OpenVINO model in the hot turn-taking loop without relying
on heavyweight ASR model export.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class EOUFeatures:
    silence_ms: float
    text_chars: float
    has_continue_hint: float
    has_commit_hint: float


@dataclass
class EOUDecision:
    action: str
    hold_score: float
    commit_score: float
    latency_ms: float


def ensure_model(model_xml: Path) -> Path:
    if model_xml.exists():
        return model_xml
    model_xml.parent.mkdir(parents=True, exist_ok=True)
    build_linear_eou_model(model_xml)
    return model_xml


def build_linear_eou_model(model_xml: Path) -> None:
    import openvino as ov
    from openvino import opset13 as ops

    # Features: silence_s, text_len_norm, has_continue_hint, has_commit_hint
    x = ops.parameter([1, 4], np.float32, name="features")
    weights = ops.constant(
        np.array(
            [
                [-1.1, -0.4, 1.8, -1.2],  # hold score
                [1.2, 0.6, -1.6, 1.6],   # commit score
            ],
            dtype=np.float32,
        )
    )
    bias = ops.constant(np.array([[0.45, -0.35]], dtype=np.float32))
    logits = ops.add(ops.matmul(x, ops.transpose(weights, [1, 0]), False, False), bias)
    model = ov.Model([logits], [x], name="local_duplex_eou_policy")
    ov.save_model(model, str(model_xml))


class OpenVINOEOUPolicy:
    def __init__(self, model_xml: Path, device: str = "CPU"):
        import openvino as ov

        model_xml = ensure_model(model_xml)
        self.core = ov.Core()
        self.compiled = self.core.compile_model(str(model_xml), device)
        self.input_layer = self.compiled.inputs[0]
        self.output_layer = self.compiled.outputs[0]
        self.device = device
        self.model_xml = model_xml

    def decide(self, features: EOUFeatures) -> EOUDecision:
        vector = np.array(
            [
                [
                    min(features.silence_ms / 1000.0, 3.0),
                    min(features.text_chars / 30.0, 3.0),
                    features.has_continue_hint,
                    features.has_commit_hint,
                ]
            ],
            dtype=np.float32,
        )
        started = time.perf_counter()
        result = self.compiled([vector])[self.output_layer]
        latency_ms = (time.perf_counter() - started) * 1000
        hold_score = float(result[0][0])
        commit_score = float(result[0][1])
        action = "commit" if commit_score >= hold_score else "hold"
        return EOUDecision(action=action, hold_score=round(hold_score, 4), commit_score=round(commit_score, 4), latency_ms=round(latency_ms, 4))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/run a tiny OpenVINO EOU policy model.")
    parser.add_argument("--model-xml", type=Path, default=Path("models/openvino/eou_policy.xml"))
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--silence-ms", type=float, default=800)
    parser.add_argument("--text-chars", type=float, default=10)
    parser.add_argument("--continue-hint", type=float, default=0)
    parser.add_argument("--commit-hint", type=float, default=1)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/openvino_eou_benchmark.json"))
    args = parser.parse_args()

    policy = OpenVINOEOUPolicy(args.model_xml, args.device)
    features = EOUFeatures(args.silence_ms, args.text_chars, args.continue_hint, args.commit_hint)
    decisions = [policy.decide(features) for _ in range(args.iterations)]
    latencies = [decision.latency_ms for decision in decisions]
    payload = {
        "model_xml": str(args.model_xml),
        "device": args.device,
        "features": asdict(features),
        "last_decision": asdict(decisions[-1]),
        "iterations": args.iterations,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 4),
        "min_latency_ms": round(min(latencies), 4),
        "max_latency_ms": round(max(latencies), 4),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
