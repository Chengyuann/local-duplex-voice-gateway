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
```

## 表单简介

```text
Local Duplex Voice Gateway 是一个面向 AI PC 的本地语音 Agent Skill。它把 ASR/VAD/EOU/TTS 与 35B 以下本地 Agent 大脑连接起来，解决语音交互中“什么时候说完”“什么时候等待”“什么时候打断 TTS”“什么时候提交给 Agent”的问题。当前仓库提供可运行的 turn-taking 控制层和 demo 测试，支持 commit_turn、hold、interrupt_tts 等事件输出；后续可接入 OpenVINO 加速的 ASR/VAD/EOU/TTS 模块，形成完整本地全双工语音 Agent 工作流。
```
