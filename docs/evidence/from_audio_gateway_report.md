# Local Duplex Voice Gateway Report

## Summary

- Source: `demo/from_audio_events.jsonl`
- Generated at: 2026-06-16T18:37:12
- Committed turns: 1
- TTS interruptions: 0

## Committed Turns

1. 帮我总结这份合同，等一下，先重点看付款周期。

## Event Timeline

| t | action | latency | text | reason |
|---:|---|---:|---|---|
| 0.00 | `listen` | 0ms |  | VAD detected speech start |
| 0.05 | `listen` | 0ms | 帮我总结这份合同，等一下，先重点看付款周期。 | user is speaking |
| 4.46 | `commit_turn` | 0ms | 帮我总结这份合同，等一下，先重点看付款周期。 | silence 4410ms crossed EOU threshold |

## Local AI PC Notes

- This demo processes local ASR/VAD/TTS events only.
- In production, connect local ASR, VAD, EOU and TTS adapters.
- OpenVINO can be used to accelerate ASR/VAD/EOU on Intel CPU/GPU/NPU.
- A <=35B local model can consume `commit_turn` events as the Agent brain.