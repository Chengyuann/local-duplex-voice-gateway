# 【Intel AI PC】Local Duplex Voice Gateway：面向 AI PC 的本地全双工语音 Agent Skill

> 参赛方向：AI PC Agent Skills 主题活动  
> 作品名称：Local Duplex Voice Gateway  
> 推荐标签：`Intel AI PC`、`AIPC`、`OpenVINO`、`Agentic AI`、`Skills`、`Voice Agent`

![Local Duplex Voice Gateway 封面](https://raw.githubusercontent.com/Chengyuann/local-duplex-voice-gateway/main/assets/cover.jpg)

语音 Agent 的体验问题，往往不只在 ASR 准确率或 TTS 音色上。一个能被日常使用的语音入口，需要处理更细的交互节奏：用户什么时候还在说、什么时候只是短暂停顿、什么时候已经说完、什么时候正在打断系统回复。

传统语音链路常见做法是 ASR 转写、LLM 生成、TTS 播放。这条链路能完成基本问答，但在真实对话里容易卡住。用户说“然后……”时，系统可能过早提交半句话；用户说“等一下”时，TTS 可能还在继续播放上一轮回复；用户临时补充约束时，Agent 可能已经开始执行错误任务。Local Duplex Voice Gateway 关注的正是这层听说节奏。

本项目把语音 Agent 的 turn-taking 控制层独立出来，形成一个可复用 Skill。它接收本地 ASR/VAD/TTS 事件，输出 `listen`、`hold`、`commit_turn`、`interrupt_tts` 等状态，并把完整语音意图交给 35B 以下本地 Agent 大脑处理。这样，ASR、VAD、EOU、TTS 与本地模型可以各司其职，语音入口也更接近自然对话。

AI PC 适合承载这类能力。语音交互对延迟敏感，音频和转写内容又常包含会议、代码需求、工作安排或私人信息。将 VAD、ASR、EOU、TTS 和话轮判断放在本地，可以减少外传数据，也能降低往返延迟。云端仍可处理公开检索或非敏感协作，但靠近用户的听说环节更适合在端侧完成。

![Local Duplex Voice Gateway 架构](https://raw.githubusercontent.com/Chengyuann/local-duplex-voice-gateway/main/assets/architecture.svg)

## 语音 Agent 的三个细节

第一个细节是短暂停顿。用户说“帮我查一下今天的会议，然后……”时，中间停顿半秒并不一定代表结束。如果系统立刻提交，Agent 拿到的是半句话；如果等待太久，用户又会感觉系统迟钝。Gateway 需要同时参考静音时长、文本长度和继续表达。

第二个细节是打断。Agent 正在播报“我先帮你看一下合同……”时，用户说“等一下，先看付款周期”，这不是噪声，而是新的高优先级指令。Gateway 需要输出 `interrupt_tts`，让 TTS 停止，并把新的意图提交给 Agent。

第三个细节是修正。语音输入经常带有临时改口，例如“帮我写个总结，等一下，不要太正式，像日报一点”。如果只提交第一段，后续工具调用会偏离用户意图。Gateway 的作用是把这些修正转成稳定事件，减少半截话触发执行的情况。

## 产品形态

一个典型交互过程如下：

```text
用户：帮我总结这份合同。
Agent：我先帮你看一下合同……
用户：等一下，先重点看付款周期。
Agent：停止当前 TTS，重新整理意图：优先检查付款周期。
```

在这段对话里，Gateway 先提交“帮我总结这份合同”，随后在 TTS 播放期间继续监听。听到“等一下”后，它输出 `interrupt_tts`，并把“先重点看付款周期”作为新的语音意图提交。

这类能力可以放进桌面语音助手、AI coding 语音控制、会议助手、语音桌宠或无障碍交互工具。它并不替代业务 Agent，而是作为语音前台，处理用户说话过程中的停顿、修正和打断。

## 事件协议

Local Duplex Voice Gateway 的链路如下：

```text
麦克风音频
    -> 本地 VAD / ASR
    -> Local Duplex Voice Gateway
    -> EOU 判断 / 打断检测 / turn-taking 事件
    -> commit_turn 给本地 Agent 大脑
    -> Agent 调用工具或生成回复
    -> 本地 TTS 播放
    -> 用户插话时 interrupt_tts
```

![全双工语音事件时间线](https://raw.githubusercontent.com/Chengyuann/local-duplex-voice-gateway/main/assets/timeline.svg)

Gateway 输出的事件保持精简：

| 事件 | 作用 |
|---|---|
| `listen` | 用户仍在说话，继续收音 |
| `hold` | 用户短暂停顿，暂时不要提交 |
| `commit_turn` | 用户这一轮说完，可以交给 Agent |
| `interrupt_tts` | 用户插话，停止当前 TTS |
| `tts_started` | Agent 开始说话 |
| `tts_finished` | Agent 说完 |

事件协议的好处是模型可替换。ASR 可以使用 SenseVoiceSmall、Paraformer 或其他本地模型；VAD 可以使用 FSMN-VAD；TTS 可以接 CosyVoice2 或其他本地 TTS；EOU 可以使用规则，也可以使用 OpenVINO policy 或专门的 turn detection 模型。Agent 侧只需要处理稳定事件，而不用关心底层音频模型细节。

## 与 35B 以下本地模型的分工

该 Skill 不要求 35B 以下模型直接处理原始音频流。VAD、EOU、打断检测等高频判断先由本地轻量层完成；当 Gateway 产出 `commit_turn` 后，本地 Agent 大脑再理解文本意图并决定工具调用。

这种分工适合 Qwen3-30B-A3B、MiniCPM-o 4.5 或其他 35B 以下模型。模型收到的是完整 turn，而不是不断抖动的 ASR partial，规划和工具调用会更稳定。在 Trae、Ollama 或其他支持工具调用的本地 Agent 环境中，Local Duplex Voice Gateway 可以作为前置语音工具接入。

## ModelScope 模型接入

仓库没有把启动流程绑定到某一个预装模型。基础 demo 可直接运行；真实语音链路则按 ModelScope 模型库逐步接入。

VAD 层可使用 `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`，用于检测有效语音片段起止点，并输出 speech/silence 时间事件。ASR 层可使用 `iic/SenseVoiceSmall`，模型卡提供了 FunASR `AutoModel` 调用方式，支持自动语言识别、VAD 切分、ITN 等能力。长音频或会议场景可参考 `iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch`，它集成了 VAD、ASR、标点和时间戳。

Turn detection 层可关注 `TEN-framework/TEN_Turn_Detection`。它面向 full-duplex dialogue communication，用于识别人机对话中的自然话轮信号。TTS 层可参考 `iic/CosyVoice2-0.5B`，后续可接入 `tts_started`、`tts_finished`、`interrupt_tts` 等事件，实现播放和打断控制。

端到端语音模型也可作为产品形态参考，例如 Qwen2.5-Omni-7B、MiniCPM-o 系列和 Moshi。Local Duplex Voice Gateway 不绑定某个端到端模型，而是保留事件协议，让 ASR、TTS、EOU 或端到端语音模型都能按需替换。

一个真实 adapter 的形态如下：

```python
for chunk in local_asr_stream(audio):
    gateway.push({
        "t": chunk.time,
        "type": "asr_partial",
        "text": chunk.text,
        "speech": chunk.is_speech,
    })

for decision in gateway.events():
    if decision.action == "commit_turn":
        agent.run(decision.text)
    elif decision.action == "interrupt_tts":
        tts.stop()
```

## 已落地的真实语音链路

仓库新增 `adapters/modelscope_speech.py`，用于把本地 wav 转成 Gateway 可消费的 JSONL 事件。该 adapter 调用 ModelScope/FunASR 模型，支持 VAD-only 和 VAD+ASR 两种模式。

运行方式：

```bash
pip install -r requirements.txt
python scripts/prepare_models.py
python adapters/modelscope_speech.py /path/to/demo.wav \
  --output demo/from_audio_events.jsonl \
  --summary reports/modelscope_adapter_summary.json
python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl
```

项目中提交了本地音频样例 `demo/audio/voice_demo.wav`。该音频由 macOS `say` 生成，并通过 ffmpeg 转成 16k mono wav。FSMN-VAD 首次未缓存运行会下载模型，模型加载约 2.19 秒，单次 VAD 推理约 28.1ms，输出语音片段 `[[0, 4460]]`。缓存后通过 adapter 跑同一条 VAD-only 链路，耗时约 1.75 秒。

VAD+ASR 链路也已跑通。SenseVoiceSmall 将样例音频转写为：

```text
帮我总结这份合同，等一下，先重点看付款周期。
```

adapter 生成 `demo/from_audio_events.jsonl`，Gateway 最终输出 1 个 `commit_turn`。本机 CPU 环境下，缓存后 ASR 路径耗时约 3.99 秒，VAD 约 1.22 秒。这一数字还不理想，但它给 OpenVINO 或更轻量模型优化提供了明确基线。

## 常驻 server/client 架构

为了避免每次用户说一句话都重新加载模型，项目新增了 localhost 常驻服务：

```bash
python server/speech_server.py --host 127.0.0.1 --port 8765
python client/gateway_client.py /path/to/demo.wav --server http://127.0.0.1:8765
```

服务提供：

```text
GET  /health
POST /v1/transcribe {"audio_path": "/path/to.wav"}
```

本地 smoke 测试中，`GET /health` 返回 `ok: true`；client 传入 `demo/audio/voice_demo.wav --vad-only` 后，server 返回 `vad_segments: [[0, 4460]]`，并生成 Gateway 事件文件。这说明 ASR/VAD 模型可以常驻在本地服务中，Gateway 作为 client 消费生成的事件。

## OpenVINO 实现

OpenVINO 已接入 Gateway 执行路径。项目新增 `adapters/openvino_eou.py`，用于构建一个轻量 EOU policy IR 模型。该模型输入四个本地特征：

```text
silence_ms
text_chars
has_continue_hint
has_commit_hint
```

模型输出 hold / commit 两个分数。Gateway 在 `handle_silence` 中调用 OpenVINO EOU policy，决定继续等待还是提交本轮语音。

实测命令：

```bash
python adapters/openvino_eou.py \
  --model-xml models/openvino/eou_policy.xml \
  --device CPU \
  --iterations 50 \
  --output docs/evidence/openvino_eou_benchmark.json

python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl \
  --openvino-eou-model models/openvino/eou_policy.xml \
  --output docs/evidence/openvino_gateway_report.md
```

本机 CPU 上 50 次推理平均耗时约 `0.0571ms`，最小 `0.0398ms`，最大 `0.6023ms`。Gateway 报告中可以看到由 OpenVINO 触发的决策：

```text
0.75s -> hold   | OpenVINO EOU policy selected hold
1.82s -> commit | OpenVINO EOU policy selected commit after 770ms
```

这不是 VAD/ASR 大模型加速，但已经把 OpenVINO 放入实际话轮判断链路。后续导出 VAD、ASR 或 TTS 的 IR 模型后，可继续沿用 `scripts/export_openvino.py` 和 `adapters/openvino_placeholder.py` 做模型级 benchmark。

## 复现方式

基础 demo 不需要第三方依赖：

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
python scripts/run_demo_tests.py
```

真实 ModelScope 语音链路：

```bash
pip install -r requirements.txt
python scripts/prepare_models.py
python adapters/modelscope_speech.py demo/audio/voice_demo.wav \
  --output demo/from_audio_events.jsonl \
  --summary reports/modelscope_adapter_summary.json
python scripts/duplex_voice_gateway.py demo/from_audio_events.jsonl
```

OpenVINO EOU 链路：

```bash
python adapters/openvino_eou.py --model-xml models/openvino/eou_policy.xml --iterations 50
python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl \
  --openvino-eou-model models/openvino/eou_policy.xml
```

测试结果：

```text
PASS duplex_conversation: commit_turn + interrupt_tts
PASS short_pause_continuation: hold before commit
PASS from_vad_events: real VAD event file parsed
PASS from_audio_events: real ASR text committed
PASS openvino_eou_policy: OpenVINO model used in gateway
```

## 后续路线

后续工作将沿着三条线推进。第一条线是把 wav 文件输入扩展到麦克风流式输入；第二条线是把 OpenVINO EOU policy 与 TEN Turn Detection 这类模型做融合；第三条线是接入本地 TTS adapter，让 `interrupt_tts` 从事件变成实际播放控制。

不同应用场景可以使用不同配置。会议模式可设置更保守的停顿阈值；AI coding 模式可提高打断优先级，让用户随时补充“不要改接口”“先只改测试”这类约束；无障碍模式则应强调确认和回滚，减少误触发关键操作。

## 小结

Local Duplex Voice Gateway 解决的是语音 Agent 的节奏问题。它把听、等、提交、打断这些状态定义成稳定事件，让 ASR、VAD、EOU、TTS 和本地 Agent 大脑可以协作。

当前版本已经具备三条可验证链路：JSONL turn-taking demo、ModelScope VAD+SenseVoiceSmall 本地语音链路、OpenVINO EOU policy 执行链路。借助 ModelScope 语音模型与 OpenVINO 端侧推理优化，这个 Skill 可以继续扩展为本地全双工语音 Agent 网关。
