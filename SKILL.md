---
name: local-duplex-voice-gateway
description: >
  Local Duplex Voice Gateway 是一个面向 AI PC 的本地语音 Agent Skill。
  当用户需要构建可打断、低延迟、支持全双工/半双工过渡的语音助手时使用。
  它把本地 ASR/VAD/EOU/TTS 工具组织成 Agent 可调用的语音网关：识别用户是否说完、
  判断是否需要打断正在播放的 TTS、生成稳定的 turn-taking 事件，并把完整语音意图交给
  35B 以下本地模型作为 Agent 大脑处理。适合本地语音助手、桌面陪伴、会议助手、
  AI coding 语音控制、无障碍语音交互等场景。
version: 0.1.0
tags: [AIPC, voice, full-duplex, turn-taking, ASR, TTS, OpenVINO, local-ai]
license: Apache-2.0
author: AI PC Developer
---

# Local Duplex Voice Gateway

Local Duplex Voice Gateway 把语音 Agent 中最容易失控的部分拆出来：什么时候听、什么时候等、什么时候打断 TTS、什么时候把一句话提交给 Agent 大脑。

## 适用场景

当用户表达这些需求时触发：

- “做一个本地语音助手”
- “语音 Agent 怎么支持打断”
- “全双工语音交互”
- “帮我判断用户说完没有”
- “本地 ASR/TTS 工具调用”
- “AI PC 语音 Copilot”
- “voice turn detection / end of utterance”
- “barge-in / interruption”

## 能力边界

当前 Skill 提供可运行的 turn-taking 控制层和可替换适配器：

1. 读取流式 ASR 分片或 demo JSONL。
2. 判断用户是否仍在说话、是否短暂停顿、是否一句话结束。
3. 在 TTS 播放期间检测用户插话，输出 `interrupt_tts`。
4. 输出 Agent 可消费的事件：`listen`、`hold`、`commit_turn`、`interrupt_tts`。
5. 生成本地 Markdown / JSON 会话报告。

真实部署时推荐接入：

- ASR：Whisper / SenseVoice / Paraformer 等本地 ASR，OpenVINO 优化优先。
- EOU：轻量 turn detection 模型，或 35B 以下本地模型辅助判断。
- TTS：Piper / ChatTTS / F5-TTS / CosyVoice / Qwen-Omni 系列语音输出。
- Agent 大脑：Ollama + Qwen3.6-35B-A3B / openBMB4.5 系列 / 其他 35B 以下模型。

## 工作流程

```text
麦克风音频
    -> VAD / ASR 本地识别
    -> Local Duplex Voice Gateway
    -> EOU / 打断 / turn-taking 判断
    -> commit_turn 给 Agent 大脑
    -> Agent 调用工具或生成回复
    -> 本地 TTS 播放
    -> 用户插话时 interrupt_tts
```

## 调用方式

在 Skill 根目录运行：

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
```

输出 JSON：

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl --format json
```

运行 demo 测试：

```bash
python scripts/run_demo_tests.py
```

## Agent 输出建议

Agent 读取报告后不要只说“用户说完了”。更好的输出是：

- 本轮是否完成
- 是否发生打断
- 用户最终意图是什么
- 下一步应该调用哪个工具
- TTS 是否需要停止或重说

## 安全原则

- 默认只处理用户指定的本地音频转写或事件文件。
- 不上传原始音频、转写文本或会话报告。
- demo 不依赖云端 API。
- 真实接入麦克风时，应由用户明确授权。
