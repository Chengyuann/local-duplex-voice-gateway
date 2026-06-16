# Verification

Last local verification: 2026-06-16.

## Commands

```bash
python scripts/run_demo_tests.py
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl --output reports/demo_gateway_report.md
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl --format json --output reports/demo_gateway_report.json
python scripts/prepare_models.py --dry-run
python scripts/export_openvino.py --model iic/SenseVoiceSmall --task automatic-speech-recognition --dry-run
python adapters/openvino_placeholder.py --output docs/evidence/openvino_check.json
python -m py_compile scripts/duplex_voice_gateway.py scripts/run_demo_tests.py scripts/prepare_models.py scripts/export_openvino.py adapters/modelscope_speech.py adapters/openvino_placeholder.py server/speech_server.py client/gateway_client.py
```

## Results

```text
PASS duplex_conversation: commit_turn + interrupt_tts
PASS short_pause_continuation: hold before commit
```

Gateway demo:

```text
Committed turns: 2
TTS interruptions: 1
- commit_turn: 帮我总结这份合同
- commit_turn: 等一下 先重点看付款周期
- interrupt_tts at 1.70s: 等一下
```

Model preparation dry run:

```json
{
  "cache_dir": "models/modelscope",
  "models": [
    "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "iic/SenseVoiceSmall",
    "iic/CosyVoice2-0.5B",
    "TEN-framework/TEN_Turn_Detection"
  ]
}
```

OpenVINO export dry run:

```json
{
  "command": [
    "optimum-cli",
    "export",
    "openvino",
    "--model",
    "iic/SenseVoiceSmall",
    "--task",
    "automatic-speech-recognition",
    "models/openvino/exported"
  ]
}
```

OpenVINO EOU policy benchmark:

```bash
python adapters/openvino_eou.py \
  --model-xml models/openvino/eou_policy.xml \
  --device CPU \
  --iterations 50 \
  --output docs/evidence/openvino_eou_benchmark.json
python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl \
  --openvino-eou-model models/openvino/eou_policy.xml \
  --output docs/evidence/openvino_gateway_report.md
```

Observed result:

```json
{
  "device": "CPU",
  "iterations": 50,
  "avg_latency_ms": 0.0571,
  "min_latency_ms": 0.0398,
  "max_latency_ms": 0.6023,
  "last_decision": {
    "action": "commit",
    "hold_score": -1.7627,
    "commit_score": 2.4102,
    "latency_ms": 0.0402
  }
}
```

Gateway output with OpenVINO EOU policy:

```text
PASS openvino_eou_policy: OpenVINO model used in gateway
```

OpenVINO runtime check:

```json
{
  "runtime": {
    "available": true,
    "version": "2025.3.0-19807-44526285f24-releases/2025/3",
    "devices": ["CPU"]
  }
}
```

OpenVINO EOU is now part of the Gateway execution path. The benchmark above uses `adapters/openvino_eou.py`, and `docs/evidence/openvino_gateway_report.md` shows Gateway decisions with reasons `OpenVINO EOU policy selected hold` and `OpenVINO EOU policy selected commit`.

For exported speech IR models, run:

```bash
python adapters/openvino_placeholder.py --model-xml models/openvino/sensevoice/openvino_model.xml --device CPU --iterations 10 --output docs/evidence/openvino_benchmark.json
```

## Real Model Smoke: ModelScope FSMN-VAD

The repository now includes a true local ModelScope/FunASR VAD path. A local wav was generated with macOS `say`, converted to 16k mono wav with ffmpeg, then processed by `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`.

Command:

```bash
python adapters/modelscope_speech.py demo/audio/voice_demo.wav \
  --vad-only \
  --output demo/from_vad_events.jsonl \
  --summary docs/evidence/modelscope_vad_summary.json
python scripts/duplex_voice_gateway.py demo/from_vad_events.jsonl \
  --output docs/evidence/from_vad_gateway_report.md
```

Observed result on the current development machine:

```json
{
  "audio_path": "demo/audio/voice_demo.wav",
  "asr_text": "",
  "events_path": "demo/from_vad_events.jsonl",
  "vad_segments": [[0, 4460]],
  "timings_ms": {
    "vad": 1752.8,
    "asr": 0.0
  },
  "config": {
    "vad_model": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "vad_revision": "v2.0.4",
    "vad_only": true
  }
}
```

The first uncached run also downloaded the VAD model from ModelScope and produced a direct model smoke result:

```json
{
  "load_ms": 2193.54,
  "infer_ms": 28.1,
  "result": [{"key": "voice_demo", "value": [[0, 4460]]}]
}
```

The VAD-only path does not produce `commit_turn` because it has no ASR text; it proves that a real local speech model can feed speech/silence timing into the Gateway. The ASR path is implemented in `adapters/modelscope_speech.py` and can be enabled by removing `--vad-only` after downloading `iic/SenseVoiceSmall`.

## Real Model Smoke: SenseVoiceSmall ASR + Gateway Commit

After installing `torch` and `torchaudio`, the full VAD + ASR adapter path was also run with `iic/SenseVoiceSmall`.

Command:

```bash
python adapters/modelscope_speech.py demo/audio/voice_demo.wav \
  --output demo/from_audio_events.jsonl \
  --summary docs/evidence/modelscope_asr_summary.json
python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl \
  --output docs/evidence/from_audio_gateway_report.md
```

Observed result:

```json
{
  "audio_path": "demo/audio/voice_demo.wav",
  "asr_text": "帮我总结这份合同，等一下，先重点看付款周期。",
  "events_path": "demo/from_audio_events.jsonl",
  "vad_segments": [[0, 4460]],
  "timings_ms": {
    "vad": 1367.93,
    "asr": 3994.89
  }
}
```

Gateway output:

```text
Committed turns: 1
- commit_turn: 帮我总结这份合同，等一下，先重点看付款周期。
```

This verifies the full local audio-file path: local wav -> ModelScope VAD -> SenseVoiceSmall ASR -> Gateway events -> `commit_turn`.

## Persistent Server / Client Smoke

The localhost server/client path was also verified with the cached ModelScope FSMN-VAD model.

Commands:

```bash
python server/speech_server.py --host 127.0.0.1 --port 8765
curl http://127.0.0.1:8765/health
python client/gateway_client.py demo/audio/voice_demo.wav \
  --server http://127.0.0.1:8765 \
  --vad-only \
  --events-output-name server_vad_events.jsonl \
  --gateway-output docs/evidence/server_client_gateway_report.md
```

Observed health response:

```json
{
  "ok": true,
  "service": "local-duplex-voice-gateway"
}
```

Observed client response:

```json
{
  "ok": true,
  "audio_path": "demo/audio/voice_demo.wav",
  "events_path": "reports/server_events/server_vad_events.jsonl",
  "asr_text": "",
  "vad_segments": [[0, 4460]],
  "timings_ms": {
    "vad": 1255.23,
    "asr": 0.0
  },
  "vad_only": true
}
```

This verifies the recommended architecture: speech model stays in a localhost service, while the Gateway client consumes generated event files without reloading the model for every user turn.
