# Local Duplex Voice Gateway

![Local Duplex Voice Gateway cover](assets/cover.jpg)

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

## 真实本地语音链路

安装真实语音适配器依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

准备 ModelScope 模型：

```bash
python scripts/prepare_models.py --dry-run
python scripts/prepare_models.py
```

把本地 wav 转成 Gateway 事件，再交给网关处理：

```bash
# 先跑轻量 VAD 真实链路
python adapters/modelscope_speech.py /path/to/demo.wav \
  --vad-only \
  --output demo/from_vad_events.jsonl \
  --summary reports/modelscope_vad_summary.json

# 再跑 VAD + ASR 链路
python adapters/modelscope_speech.py /path/to/demo.wav \
  --output demo/from_audio_events.jsonl \
  --summary reports/modelscope_adapter_summary.json

python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl \
  --output reports/from_audio_gateway_report.md
```

## 常驻 server/client 架构

为避免每轮重载 ASR/VAD 模型，可以启动 localhost 常驻服务：

```bash
python server/speech_server.py --host 127.0.0.1 --port 8765
```

另一个终端调用：

```bash
python client/gateway_client.py /path/to/demo.wav \
  --server http://127.0.0.1:8765 \
  --vad-only \
  --gateway-output reports/client_gateway_report.md
```

服务接口：

- `GET /health`
- `POST /v1/transcribe {"audio_path":"/path/to.wav"}`

## OpenVINO 检查与导出

检查 OpenVINO runtime：

```bash
python adapters/openvino_placeholder.py --output reports/openvino_check.json
```

Optimum Intel 导出命令模板：

```bash
python scripts/export_openvino.py \
  --model iic/SenseVoiceSmall \
  --task automatic-speech-recognition \
  --output models/openvino/sensevoice \
  --dry-run
```

如果模型已导出为 IR，可做本地 benchmark：

```bash
python adapters/openvino_placeholder.py \
  --model-xml models/openvino/sensevoice/openvino_model.xml \
  --device CPU \
  --iterations 10 \
  --output reports/openvino_benchmark.json
```

当前仓库验证摘要见 `docs/verification.md`。

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
