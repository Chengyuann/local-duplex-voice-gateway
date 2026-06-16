#!/usr/bin/env python3
"""OpenVINO availability and benchmark helper.

This file gives the project a concrete OpenVINO integration point even when a
review machine has not exported speech models yet. It checks OpenVINO runtime
availability and can benchmark an exported IR model when provided.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional


def check_openvino() -> dict:
    try:
        import openvino as ov
    except ImportError:
        return {"available": False, "error": "openvino is not installed"}
    core = ov.Core()
    return {"available": True, "version": getattr(ov, "__version__", "unknown"), "devices": core.available_devices}


def benchmark_ir(model_xml: Path, device: str = "CPU", iterations: int = 5) -> dict:
    import numpy as np
    import openvino as ov

    core = ov.Core()
    compiled = core.compile_model(str(model_xml), device)
    inputs = compiled.inputs
    if not inputs:
        raise RuntimeError("model has no inputs")
    request = compiled.create_infer_request()

    feed = {}
    dummy_note = (
        "This generic IR benchmark feeds zero tensors because no model-specific "
        "preprocessor is available. Use it only as a runtime smoke test; do not "
        "report it as speech-model latency."
    )
    for input_node in inputs:
        shape = []
        for dim in input_node.partial_shape:
            shape.append(1 if dim.is_dynamic else int(dim.get_length()))
        feed[input_node] = np.zeros(shape, dtype=np.float32)

    latencies = []
    for _ in range(iterations):
        started = time.perf_counter()
        request.infer(feed)
        latencies.append((time.perf_counter() - started) * 1000)

    return {
        "model": str(model_xml),
        "device": device,
        "iterations": iterations,
        "benchmark_type": "runtime_smoke_dummy_input",
        "note": dummy_note,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenVINO runtime and optionally benchmark an exported IR model.")
    parser.add_argument("--model-xml", type=Path)
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("reports/openvino_check.json"))
    args = parser.parse_args()

    result = {"runtime": check_openvino()}
    if args.model_xml:
        if not args.model_xml.exists():
            raise SystemExit(f"IR model not found: {args.model_xml}")
        result["benchmark"] = benchmark_ir(args.model_xml, args.device, args.iterations)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
