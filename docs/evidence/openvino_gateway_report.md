# Local Duplex Voice Gateway Report

## Summary

- Source: `demo/short_pause_continuation.jsonl`
- Generated at: 2026-06-16T18:52:00
- Committed turns: 1
- TTS interruptions: 0

## Committed Turns

1. 帮我查一下今天的会议 然后生成一个待办

## Event Timeline

| t | action | latency | text | reason |
|---:|---|---:|---|---|
| 0.00 | `listen` | 0ms | 帮我查一下今天的会议 | user is speaking |
| 0.40 | `listen` | 0ms | 帮我查一下今天的会议 然后 | user is speaking |
| 0.75 | `hold` | 0ms | 帮我查一下今天的会议 然后 | OpenVINO EOU policy selected hold |
| 1.05 | `listen` | 0ms | 帮我查一下今天的会议 然后生成一个待办 | user is speaking |
| 1.82 | `commit_turn` | 0ms | 帮我查一下今天的会议 然后生成一个待办 | OpenVINO EOU policy selected commit after 770ms |
| 2.08 | `listen` | 0ms |  | silence without active utterance |

## Local AI PC Notes

- This demo processes local ASR/VAD/TTS events only.
- In production, connect local ASR, VAD, EOU and TTS adapters.
- OpenVINO can be used to accelerate ASR/VAD/EOU on Intel CPU/GPU/NPU.
- A <=35B local model can consume `commit_turn` events as the Agent brain.