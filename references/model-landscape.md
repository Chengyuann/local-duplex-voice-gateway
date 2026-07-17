# Local Voice Model Landscape

This Skill is designed as a gateway. It can sit in front of several local voice stacks. For a ModelScope-first plan, read `references/modelscope-voice-stack.md`.

## Candidate local components

| Layer | Candidate | Why it fits |
|---|---|---|
| ASR | `iic/SenseVoiceSmall` | ModelScope/FunASR model with auto language support and VAD integration |
| ASR | `iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch` | ModelScope long-audio ASR with VAD, punctuation and timestamps |
| VAD | `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` | ModelScope VAD for effective speech start/end detection |
| Turn detection | `TEN-framework/TEN_Turn_Detection` | ModelScope model designed for full-duplex dialogue turn detection |
| Turn detection | VAD + EOU rules | Lightweight baseline, deterministic and easy to validate |
| Turn detection | MiniCPM-o / Moshi-style duplex models | Useful reference direction for full-duplex interaction design |
| TTS | `iic/CosyVoice2-0.5B` | ModelScope TTS with streaming and zero-shot voice capability |
| Agent brain | Qwen3-30B-A3B / MiniCPM-o 4.5 / smaller local LLMs | <=35B local model acts as planner and tool caller |

## Product stance

The dependency-free demo validates the voice gateway protocol. Production deployments can swap adapters while keeping the same Agent-facing event contract.
