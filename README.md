# Local Duplex Voice Gateway

![Local Duplex Voice Gateway cover](assets/cover.jpg)

面向 AI PC 的本地全双工语音 Agent Skill。项目负责语音交互中的话轮控制：识别短暂停顿、提交完整语音意图、处理 TTS 播放期间的用户打断，并将稳定事件交给本地 Agent 大脑。

## 已实现能力

- JSONL 流式事件处理：`listen`、`hold`、`commit_turn`、`interrupt_tts`
- ModelScope FSMN-VAD 本地语音活动检测
- ModelScope SenseVoiceSmall 本地 ASR
- localhost 常驻 speech server 与 Gateway client
- OpenVINO EOU policy 实时推理
- Markdown / JSON 会话报告

## 基础验证

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl --format json
python scripts/run_demo_tests.py
```

基础 JSONL demo 仅依赖 Python 3.8+ 标准库。

## 安装真实语音链路

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

本地 wav 转 Gateway 事件：

```bash
# VAD-only
python adapters/modelscope_speech.py demo/audio/voice_demo.wav \
  --vad-only \
  --output demo/from_vad_events.jsonl \
  --summary reports/modelscope_vad_summary.json

# VAD + ASR
python adapters/modelscope_speech.py demo/audio/voice_demo.wav \
  --output demo/from_audio_events.jsonl \
  --summary reports/modelscope_asr_summary.json

python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl \
  --output reports/from_audio_gateway_report.md
```

仓库已提交真实模型运行生成的事件样例：

- `demo/from_vad_events.jsonl`
- `demo/from_audio_events.jsonl`
- `demo/audio/voice_demo.wav`

## 常驻服务

语音模型可常驻 localhost 服务，避免每轮重载：

```bash
python server/speech_server.py --host 127.0.0.1 --port 8765
```

另一个终端调用：

```bash
python client/gateway_client.py demo/audio/voice_demo.wav \
  --server http://127.0.0.1:8765 \
  --vad-only \
  --gateway-output reports/client_gateway_report.md
```

接口：

- `GET /health`
- `POST /v1/transcribe {"audio_path":"/path/to.wav"}`

## OpenVINO EOU

项目包含轻量 OpenVINO EOU policy。模型输入静音时长、文本长度、继续提示和结束提示，输出 hold / commit 分数。

```bash
python adapters/openvino_eou.py \
  --model-xml models/openvino/eou_policy.xml \
  --device CPU \
  --iterations 50 \
  --output docs/evidence/openvino_eou_benchmark.json
```

Gateway 使用 OpenVINO EOU：

```bash
python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl \
  --openvino-eou-model models/openvino/eou_policy.xml \
  --output docs/evidence/openvino_gateway_report.md
```

本机 CPU 实测 50 次推理：

```text
平均 0.0571ms
最小 0.0398ms
最大 0.6023ms
```

OpenVINO runtime 与导出工具：

```bash
python adapters/openvino_placeholder.py --output reports/openvino_check.json
python scripts/export_openvino.py \
  --model iic/SenseVoiceSmall \
  --task automatic-speech-recognition \
  --output models/openvino/sensevoice \
  --dry-run
```

## 输入事件

```json
{"t": 0.00, "type": "asr_partial", "text": "帮我", "speech": true}
{"t": 0.42, "type": "asr_partial", "text": "帮我总结这份合同", "speech": true}
{"t": 1.35, "type": "silence", "speech": false}
{"t": 2.05, "type": "tts_start", "text": "我先帮你看一下"}
{"t": 2.30, "type": "asr_partial", "text": "等一下", "speech": true}
```

## 输出事件

| 事件 | 含义 |
|---|---|
| `listen` | 继续收音 |
| `hold` | 短暂停顿，暂不提交 |
| `commit_turn` | 当前语音意图可以交给 Agent |
| `interrupt_tts` | 用户插话，停止 TTS |
| `tts_started` | TTS 开始播放 |
| `tts_finished` | TTS 播放结束 |

## 验证材料

- [完整文章](docs/article.md)
- [验证记录](docs/verification.md)
- [ModelScope 模型接入说明](references/modelscope-voice-stack.md)
- [运行证据](docs/evidence/)

## License

Apache-2.0
