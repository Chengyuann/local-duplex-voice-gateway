# Submission Guide

## GitHub Import

ModelScope Skills 支持通过 GitHub 公开仓库快速创建。使用仓库根目录即可解析：

```text
https://github.com/Chengyuann/local-duplex-voice-gateway
```

## Skill 信息

- Skill 名称：Local Duplex Voice Gateway
- 标签：`AIPC`、`voice`、`full-duplex`、`turn-taking`、`ASR`、`TTS`、`OpenVINO`
- 文章标签：`Intel AI PC`

## 验证命令

```bash
python scripts/run_demo_tests.py
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl
python scripts/prepare_models.py --dry-run
python scripts/export_openvino.py --model iic/SenseVoiceSmall --task automatic-speech-recognition --dry-run
python adapters/openvino_placeholder.py --output reports/openvino_check.json
```

验证摘要见 `docs/verification.md`。

真实 wav 链路：

```bash
pip install -r requirements.txt
python scripts/prepare_models.py
python adapters/modelscope_speech.py /path/to/demo.wav --vad-only --output demo/from_vad_events.jsonl
python adapters/modelscope_speech.py /path/to/demo.wav --output demo/from_audio_events.jsonl
python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl
```

常驻 server/client：

```bash
python server/speech_server.py --host 127.0.0.1 --port 8765
python client/gateway_client.py /path/to/demo.wav --server http://127.0.0.1:8765 --vad-only
```

## 表单简介

```text
Local Duplex Voice Gateway 是一个面向 AI PC 的本地语音 Agent Skill。它把 ASR/VAD/EOU/TTS 与 35B 以下本地 Agent 大脑连接起来，解决语音交互中“什么时候说完”“什么时候等待”“什么时候打断 TTS”“什么时候提交给 Agent”的问题。当前仓库提供可运行的 turn-taking 控制层和 demo 测试，支持 commit_turn、hold、interrupt_tts 等事件输出；后续可接入 OpenVINO 加速的 ASR/VAD/EOU/TTS 模块，形成完整本地全双工语音 Agent 工作流。
```
