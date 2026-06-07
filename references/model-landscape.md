# Local Voice Model Landscape

This Skill is designed as a gateway. It can sit in front of several local voice stacks.

## Candidate local components

| Layer | Candidate | Why it fits |
|---|---|---|
| ASR | Whisper / faster-whisper / whisper.cpp | Local speech recognition, widely used, can be optimized or replaced by OpenVINO pipelines |
| ASR | SenseVoice / Paraformer | Strong Mandarin ASR options in the ModelScope ecosystem |
| Turn detection | VAD + EOU rules | Lightweight baseline, deterministic and easy to validate |
| Turn detection | MiniCPM-o / Moshi-style duplex models | Useful reference direction for full-duplex interaction design |
| TTS | Piper | Small local TTS baseline |
| TTS | ChatTTS / F5-TTS / CosyVoice | More natural local speech output, depending on license and deployment needs |
| Agent brain | Qwen3.6-35B-A3B / openBMB4.5 / smaller local LLMs | <=35B local model acts as planner and tool caller |

## Product stance

The current repository does not require downloading these models to pass the demo. It validates the voice gateway logic first. Production deployments can swap adapters while keeping the same Agent-facing event contract.
