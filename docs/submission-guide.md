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
Local Duplex Voice Gateway 是一个面向 AI PC 的本地全双工语音 Agent Skill。项目连接 ModelScope FSMN-VAD、SenseVoiceSmall、OpenVINO EOU policy 与 35B 以下本地 Agent 大脑，处理短暂停顿、完整话轮提交和 TTS 打断。代码包含真实 wav 输入、VAD/ASR adapter、localhost 常驻服务、OpenVINO Runtime 推理和可复现测试，可用于桌面语音助手、AI coding 语音控制、会议助手及无障碍交互。
```
