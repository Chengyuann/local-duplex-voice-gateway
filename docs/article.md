# 【Intel AI PC】Local Duplex Voice Gateway：让本地语音 Agent 学会听、等和打断

> 参赛方向：AI PC Agent Skills 征文活动  
> 作品名称：Local Duplex Voice Gateway  
> 推荐标签：`Intel AI PC`、`AIPC`、`OpenVINO`、`Agentic AI`、`Skills`、`Voice Agent`

这次 AI PC Agent Skills 征文强调的不是再做一个普通 demo，而是用 35B 以下小模型作为 Agent 大脑，驱动本地 AI 工具调用，最后形成可以复用的 Skill。这个方向里，语音是我觉得最适合 AI PC 的场景之一。

原因很简单：语音交互天然高频、低延迟、隐私敏感，而且它不是单纯的 ASR + LLM + TTS 串联。真正好用的语音 Agent 要能判断用户是不是说完了，要能在用户短暂停顿时继续等，要能在 TTS 播放时被用户打断，还要能把完整意图稳定提交给 Agent 大脑。这些细节决定了语音助手像不像一个“能交流的人”。

因此我做了 **Local Duplex Voice Gateway**。它不是一个单独的 ASR 模型，也不是一个 TTS 播放器，而是本地语音 Agent 的 turn-taking 控制层。它把本地 ASR、VAD、EOU、TTS 和 35B 以下 Agent 大脑连接起来，让 AI PC 上的语音助手具备全双工/半双工过渡能力。

## 为什么选择全双工语音

过去很多语音助手像“按住说话”的工具：用户说完，系统识别，模型生成，TTS 播放。这个流程能跑，但对真实对话来说太硬。

真实语音交流里会出现很多中间状态：

- 用户停顿 300ms，可能是在想下一句，不一定是结束。
- 用户说“然后……”，此时不应该立刻提交给 Agent。
- TTS 还在播，用户说“等一下”，系统应该立即停下。
- 用户插话后可能不是闲聊，而是在修正任务目标。
- Agent 需要知道什么时候继续听，什么时候调用工具，什么时候重说。

这些问题本质上是 turn-taking 和 interruption，不是单纯 ASR 精度问题。Local Duplex Voice Gateway 就是为这层能力做的 Skill。

## 产品形态

理想的使用体验是这样的：

```text
用户：帮我总结这份合同。
Agent：我先帮你看一下合同……
用户：等一下，先重点看付款周期。
Agent：停止当前 TTS，重新整理意图：优先检查付款周期。
```

如果没有打断能力，Agent 会继续把上一句说完，用户只能等。加上全双工控制层后，用户插话会变成一个明确事件：`interrupt_tts`。Agent 可以停掉 TTS，更新任务目标，再继续执行。

从产品角度看，这个 Skill 可以服务很多场景：

- AI PC 桌面语音 Copilot：边听边执行本地工具。
- 会议助手：识别自然停顿，避免把没说完的话过早提交。
- AI coding 语音控制：用户可以随时打断、修正需求、补充约束。
- 无障碍交互：用户不需要精确点击按钮，通过自然语音控制流程。
- 情感陪伴或语音桌宠：减少机械抢话，让对话更自然。

这也是 Agentic AI 和 Hybrid AI 的结合点：Agent 大脑负责理解和规划，语音 Gateway 负责本地听说节奏，AI PC 负责低延迟执行。

## 本地架构

Local Duplex Voice Gateway 的核心链路是：

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

在 QwenPaw、Trae 或其他支持工具调用的 Agent 环境里，这个 Skill 暴露的不是“转写一句话”这种低级接口，而是更接近语音交互状态机的事件：

| 事件 | 含义 |
|---|---|
| `listen` | 用户还在说，继续收音 |
| `hold` | 用户短暂停顿，暂不提交 |
| `commit_turn` | 用户一句话结束，可以交给 Agent |
| `interrupt_tts` | 用户插话，应停止当前 TTS |
| `tts_started` | Agent 开始说话 |
| `tts_finished` | Agent 说完 |

这些事件让 Agent 大脑不用关心底层音频细节，只需要处理稳定的语音回合。

## 为什么符合 35B 以下 Agent 大脑

活动推荐用 Qwen3.6-35B-A3B、openBMB4.5 等 35B 以下模型作为 Agent 大脑。我的设计里，模型并不直接处理原始音频流，而是消费 Gateway 输出的结构化事件。

这样做有三个好处：

1. 低延迟：VAD、EOU、打断这些高频判断先在本地轻量层处理。
2. 更稳定：Agent 大脑收到的是完整 turn，而不是不断抖动的 ASR partial。
3. 更可复用：ASR、TTS、EOU 模型都可以替换，Agent 事件协议保持不变。

实际部署时，35B 以下模型负责理解 `commit_turn` 的文本意图，并决定调用哪个本地工具；Gateway 负责保证语音交互的节奏。

## 模型与 OpenVINO 规划

我重新按 ModelScope 模型库梳理了一套更实际的语音栈。因为你本机不一定已经有这些模型，所以当前仓库不强制下载模型；文章和设计里把它们作为可接入 adapter，先让 Skill 的事件协议和控制层跑通。

基础链路可以从 ModelScope 的 FunASR 生态开始。`iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` 可以作为 VAD 层，用于检测有效语音片段的起止时间；`iic/SenseVoiceSmall` 可以作为 ASR 层，模型卡提供了 FunASR `AutoModel` 的用法，并支持自动语言识别、VAD 切分和 ITN；长音频或会议场景可以参考 `iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch`，它把 VAD、ASR、标点和时间戳集成在一起。

Turn detection 层可以优先关注 `TEN-framework/TEN_Turn_Detection`。它在 ModelScope 上的定位就是 full-duplex dialogue communication 的 turn detection，用来识别人机对话中的自然 turn-taking cues。这个模型方向和本项目最贴近：它不是识别文字，也不是合成语音，而是判断“用户是不是该交给 Agent 了”。

TTS 层可以用 `iic/CosyVoice2-0.5B` 作为本地语音输出参考。CosyVoice2 是 0.5B 级 TTS，ModelScope 模型卡里提到 streaming inference 相关优化，适合后续接到 `tts_started / tts_finished / interrupt_tts` 这些事件上。

在端到端语音模型方向，我主要看三件事：参数量是否低于 35B，是否支持实时语音/流式对话，是否有本地部署或开源生态。

Qwen2.5-Omni-7B 是 7B 级端到端多模态模型，官方介绍里强调它可以处理文本、图像、音频和视频，并通过文本生成和自然语音合成提供实时流式响应。它适合作为“语音 Agent 大脑 + 语音输出”的参考方向。

MiniCPM-o 2.6 是 OpenBMB 的端侧多模态模型，总参数约 8B，由视觉、音频理解、语音合成和 Qwen2.5-7B 语言模型等组件组成。官方文档强调它支持实时语音对话和多模态 live streaming，这一点非常贴近 AI PC 上的语音 Copilot。

Kyutai Moshi 则是 full-duplex spoken dialogue framework 的直接参考。Moshi 的公开介绍明确把它定位为 speech-text foundation model 和 full-duplex spoken dialogue framework，并指出传统 VAD、ASR、文本对话、TTS 串联方案会带来延迟和信息损失。这个判断和本项目的出发点一致：全双工语音体验不能只靠简单串联。

不过本作品没有把核心能力绑定到某一个模型上。原因是语音 Agent 的工程形态会持续变化，ASR、TTS、EOU 都可能替换。Local Duplex Voice Gateway 保留的是 Agent-facing 的事件协议和 turn-taking 逻辑。

OpenVINO 的位置主要有三层。OpenVINO GenAI 已经提供 Text2SpeechPipeline 和 speech generation 示例，说明本地语音生成链路可以纳入 OpenVINO 生态；同时 OpenVINO notebooks 里也有 text-to-speech、Qwen2.5-Omni、MiniCPM-o 等相关示例方向，适合后续把 demo 网关升级成真实 AI PC 语音工作流。

```text
ASR / VAD 加速
    -> 更低延迟的本地识别

EOU / turn detection 加速
    -> 更快判断用户是否说完

TTS / speech generation 加速
    -> 更自然、更及时的本地语音回复
```

在 Intel AI PC 上，这些模块可以利用 CPU/GPU/NPU 异构算力。高频、隐私敏感和个性化的语音交互留在本地；如果需要云端知识检索，也只传递非敏感摘要。这就是 Hybrid AI 在语音场景里的合理分工。

## 当前仓库怎么跑

为了保证评审者不用先下载大模型，我先把核心控制层做成可复现 demo。输入是 JSONL，模拟本地 ASR/VAD/TTS 事件。

示例输入：

```json
{"t": 0.00, "type": "asr_partial", "text": "帮我", "speech": true}
{"t": 0.36, "type": "asr_partial", "text": "帮我总结这份合同", "speech": true}
{"t": 1.35, "type": "tts_start", "text": "我先帮你看一下合同。"}
{"t": 1.70, "type": "asr_partial", "text": "等一下", "speech": true}
{"t": 1.95, "type": "asr_partial", "text": "等一下 先重点看付款周期", "speech": true}
```

运行命令：

```bash
python scripts/duplex_voice_gateway.py demo/duplex_conversation.jsonl
```

输出摘要：

```text
Committed turns: 2
TTS interruptions: 1
- commit_turn: 帮我总结这份合同
- commit_turn: 等一下 先重点看付款周期
- interrupt_tts at 1.70s: 等一下
```

这说明 Gateway 做了三件事：

1. 识别第一轮完整意图：“帮我总结这份合同”。
2. 在 TTS 播放时检测到用户插话：“等一下”。
3. 将修正后的第二轮意图提交给 Agent：“先重点看付款周期”。

## 短暂停顿不是结束

另一个 demo 用来验证短暂停顿：

```bash
python scripts/duplex_voice_gateway.py demo/short_pause_continuation.jsonl
```

用户说：

```text
帮我查一下今天的会议 然后……
```

短暂停顿之后继续：

```text
生成一个待办
```

Gateway 会先输出 `hold`，不会立刻提交半句话，最后提交完整 turn：

```text
帮我查一下今天的会议 然后生成一个待办
```

这个细节非常重要。很多语音系统把“短暂停顿”等同于“说完了”，结果 Agent 过早执行，用户体验会很差。

## 可复现测试

仓库里提供了 smoke test：

```bash
python scripts/run_demo_tests.py
```

本地结果：

```text
PASS duplex_conversation: commit_turn + interrupt_tts
PASS short_pause_continuation: hold before commit
```

这组测试验证了两个语音 Agent 的核心能力：可打断，以及短暂停顿时继续等待。

## Skill 如何被 Agent 复用

这个 Skill 的重点是复用事件协议，而不是绑定某个 demo 文件。

在真实环境里，Agent 可以这样使用：

```text
用户语音
    -> 本地 ASR adapter
    -> Gateway 输出 commit_turn
    -> 35B 以下本地模型理解意图
    -> 调用本地工具
    -> 本地 TTS 播放
    -> Gateway 监听是否被打断
```

比如用户在 AI coding 时说：

```text
帮我把这个函数重构一下，等一下，不要改接口，只优化内部逻辑。
```

普通语音助手可能在第一段就开始执行；Local Duplex Voice Gateway 会把“等一下”识别为打断，把后面的约束合并到新的 turn 里。Agent 得到的不是半截任务，而是更完整的意图。

## 产品路线图

当前版本已经跑通语音 Gateway 的核心控制层。后续我会按产品形态继续补三层能力。

第一层是 OpenVINO ASR/VAD/EOU adapter。目标是在 AI PC 上把麦克风音频实时转成流式事件，同时用 OpenVINO 降低端点判断延迟。

第二层是本地 TTS adapter。接入 Piper、F5-TTS、CosyVoice、ChatTTS 或 Qwen-Omni 类模型，让 `tts_started`、`tts_finished`、`interrupt_tts` 能真正控制播放。

第三层是 Agent 集成模板。针对 QwenPaw / Trae / Ollama，本地模型可以直接读取 `commit_turn`，再决定调用文件、日历、代码、搜索或其他本地工具。

最终形态会是一个本地语音 Agent Gateway：

```text
实时音频输入
    -> OpenVINO ASR/VAD/EOU
    -> Duplex Gateway
    -> 35B 以下 Agent 大脑
    -> 本地工具调用
    -> 本地 TTS
    -> 可打断继续对话
```

## 小结

Local Duplex Voice Gateway 想解决的不是“把语音转文字”这么简单的问题，而是让本地语音 Agent 具备真实对话所需的节奏感：会听、会等、会停、会被打断。

它符合这次活动的几个关键要求：运行在本地，面向 AI PC，使用 35B 以下模型作为 Agent 大脑，驱动 ASR/VAD/EOU/TTS 等本地 AI 工具，并最终封装成可复用 Skill。当前仓库已经提供可验证的事件控制层和 demo 测试，后续接入 OpenVINO 与真实语音模型后，可以自然演进为完整的 AI PC 语音 Copilot。
