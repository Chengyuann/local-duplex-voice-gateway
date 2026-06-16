#!/usr/bin/env python3
"""Smoke tests for Local Duplex Voice Gateway."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from duplex_voice_gateway import load_events, process_events


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    state = process_events(load_events(root / "demo" / "duplex_conversation.jsonl"))
    actions = [event.action for event in state.output_events]
    assert "commit_turn" in actions, actions
    assert "interrupt_tts" in actions, actions
    assert state.interrupts == 1, state.interrupts
    assert any("总结这份合同" in turn for turn in state.committed_turns), state.committed_turns
    print("PASS duplex_conversation: commit_turn + interrupt_tts")

    state2 = process_events(load_events(root / "demo" / "short_pause_continuation.jsonl"))
    actions2 = [event.action for event in state2.output_events]
    assert "hold" in actions2, actions2
    assert state2.committed_turns[-1].endswith("然后生成一个待办"), state2.committed_turns
    print("PASS short_pause_continuation: hold before commit")

    vad_events = root / "demo" / "from_vad_events.jsonl"
    if vad_events.exists():
        state3 = process_events(load_events(vad_events))
        assert state3.output_events, "VAD event file should produce gateway events"
        actions3 = [event.action for event in state3.output_events]
        assert "ignore" not in actions3, actions3
        assert state3.output_events[-1].action in {"listen", "hold"}, actions3
        print("PASS from_vad_events: real VAD event file parsed")

    asr_events = root / "demo" / "from_audio_events.jsonl"
    if asr_events.exists():
        state4 = process_events(load_events(asr_events))
        assert state4.committed_turns, "ASR event file should commit at least one turn"
        assert "付款周期" in state4.committed_turns[-1], state4.committed_turns
        print("PASS from_audio_events: real ASR text committed")

    try:
        from adapters.openvino_eou import OpenVINOEOUPolicy

        policy = OpenVINOEOUPolicy(root / "models" / "openvino" / "eou_policy.xml")
        state5 = process_events(load_events(root / "demo" / "short_pause_continuation.jsonl"), eou_policy=policy)
        assert state5.committed_turns[-1].endswith("然后生成一个待办"), state5.committed_turns
        assert any("OpenVINO EOU policy" in event.reason for event in state5.output_events), [event.reason for event in state5.output_events]
        print("PASS openvino_eou_policy: OpenVINO model used in gateway")
    except ImportError:
        print("SKIP openvino_eou_policy: openvino not installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
