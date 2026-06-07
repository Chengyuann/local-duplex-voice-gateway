# Local Duplex Voice Gateway

一个面向 AI PC 的本地语音 Agent Skill。它不只是 ASR 或 TTS demo，而是语音 Agent 的 turn-taking 控制层：判断用户是否说完、是否短暂停顿、是否插话打断、是否应该提交给 Agent 大脑。

## 为什么做这个

语音 Agent 真正难用的地方，往往不是“识别一句话”，而是这些细节：

- 用户停顿 300ms，是想继续说，还是已经说完？
- TTS 还在播放时用户插话，要不要立刻停？
- 用户说“嗯，等一下，我想改一下”，这是不是新的意图？
- Agent 什么时候该调用工具，什么时候该继续听？

Local Duplex Voice Gateway 把这些问题变成可复用的本地 Skill。

## 快速开始

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl --format json
python scripts/run_demo_tests.py
```

基础 demo 只需要 Python 3.8+ 标准库。

## 输入格式

demo 使用 JSONL 模拟流式 ASR/VAD/TTS 事件：

```json
{"t": 0.00, "type": "asr_partial", "text": "帮我", "speech": true}
{"t": 0.42, "type": "asr_partial", "text": "帮我总结这份合同", "speech": true}
{"t": 1.35, "type": "silence", "speech": false}
{"t": 1.90, "type": "silence", "speech": false}
{"t": 2.05, "type": "tts_start", "text": "我先帮你看一下"}
{"t": 2.30, "type": "asr_partial", "text": "等一下", "speech": true}
```

## 输出事件

| 事件 | 含义 |
|---|---|
| `listen` | 继续收音 |
| `hold` | 用户短暂停顿，暂不提交 |
| `commit_turn` | 用户一句话结束，可以交给 Agent |
| `interrupt_tts` | 用户插话，应停止 TTS |
| `tts_started` | TTS 开始播放 |
| `tts_finished` | TTS 播放结束 |

## AI PC / OpenVINO 规划

当前仓库先提供可复现的语音网关控制层。实际产品接入时：

- ModelScope VAD/ASR/TTS 模型作为本地语音工具来源，详见 `references/modelscope-voice-stack.md`。
- OpenVINO 加速 ASR / VAD / EOU / TTS 模型，降低端侧延迟。
- 35B 以下本地模型作为 Agent 大脑，负责理解用户意图和调用工具。
- 本地 TTS 负责语音回复。
- Gateway 管理打断、端点判断和会话状态。

## License

Apache-2.0
