# Local Duplex Voice Gateway Report

## Summary

- Source: `demo/duplex_conversation.jsonl`
- Generated at: 2026-06-16T18:37:12
- Committed turns: 2
- TTS interruptions: 1

## Committed Turns

1. 帮我总结这份合同
2. 等一下 先重点看付款周期

## Event Timeline

| t | action | latency | text | reason |
|---:|---|---:|---|---|
| 0.00 | `listen` | 0ms | 帮我 | user is speaking |
| 0.36 | `listen` | 0ms | 帮我总结这份合同 | user is speaking |
| 0.92 | `commit_turn` | 0ms | 帮我总结这份合同 | silence 560ms crossed EOU threshold |
| 1.22 | `listen` | 0ms |  | silence without active utterance |
| 1.35 | `tts_started` | 0ms | 我先帮你看一下合同。 | agent started speaking |
| 1.70 | `interrupt_tts` | 0ms | 等一下 | user barged in while TTS was active |
| 1.95 | `listen` | 0ms | 等一下 先重点看付款周期 | user is speaking |
| 2.72 | `commit_turn` | 0ms | 等一下 先重点看付款周期 | silence 770ms crossed EOU threshold |
| 3.05 | `listen` | 0ms |  | silence without active utterance |
| 3.20 | `tts_started` | 0ms | 好的，我会优先看付款周期。 | agent started speaking |
| 4.10 | `tts_finished` | 0ms |  | agent finished speaking |

## Local AI PC Notes

- This demo processes local ASR/VAD/TTS events only.
- In production, connect local ASR, VAD, EOU and TTS adapters.
- OpenVINO can be used to accelerate ASR/VAD/EOU on Intel CPU/GPU/NPU.
- A <=35B local model can consume `commit_turn` events as the Agent brain.