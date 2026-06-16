# Local Duplex Voice Gateway Report

## Summary

- Source: `demo/from_vad_events.jsonl`
- Generated at: 2026-06-16T18:37:12
- Committed turns: 0
- TTS interruptions: 0

## Committed Turns

No completed user turn was committed.

## Event Timeline

| t | action | latency | text | reason |
|---:|---|---:|---|---|
| 0.00 | `listen` | 0ms |  | VAD detected speech start |
| 4.46 | `hold` | 4460ms |  | VAD speech ended but no ASR text is available |

## Local AI PC Notes

- This demo processes local ASR/VAD/TTS events only.
- In production, connect local ASR, VAD, EOU and TTS adapters.
- OpenVINO can be used to accelerate ASR/VAD/EOU on Intel CPU/GPU/NPU.
- A <=35B local model can consume `commit_turn` events as the Agent brain.