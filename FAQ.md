# Spark-X2.6 FAQ · 常见问题

English · [中文](#中文)

This page covers Spark-X2.6-4B / 1.7B and the 4B DSpark draft model. For historical Spark-X2.5-specific discussions, see the [existing Wiki FAQ](https://github.com/XHToken/Spark-X2.6/wiki/FAQ). Check the model generation and runtime before reusing an older deployment example or benchmark.

## English

### What should I use Spark-X2.6 for? Can it take images as input?

The published 4B and 1.7B models target text generation, coding, tool calling and agentic tasks, including on-device applications. They do not natively accept images as model input. An application that needs screenshots or documents interpreted must provide a separate OCR or vision step and pass its text output to Spark; a client displaying an image-upload button does not add vision capability to the model.

See the [model introduction](README.md#introduction) and the [4B](https://huggingface.co/XHToken/Spark-X2.6-4B) / [1.7B](https://huggingface.co/XHToken/Spark-X2.6-1.7B) model cards. Choose and test the model against the actual task rather than treating the parameter count as an accuracy guarantee.

### Where can I run the models locally, including on a Mac?

Start with the [official download channels](README.md#model-downloads) and [runtime instructions](README.md#quickstart). The X2.6 collection and Ollama organization list both model sizes; select the X2.6 model and a weight format supported by your runtime.

For Apple Silicon, [Spark-MLX-LLM](https://github.com/XHToken/Spark-MLX-LLM) provides local generation, chat and an OpenAI-compatible server. Follow that project's hardware/backend requirements. A laptop model name alone is not enough to promise that a configuration fits: record available RAM/VRAM, model precision, runtime, context length and concurrency when asking for help. Weight-file size alone does not include runtime and context memory.

### Is DSpark another standalone chat model? Does it always double inference speed?

No. [Spark-X2.6-4B-DSpark-GGUF](https://huggingface.co/XHToken/Spark-X2.6-4B-DSpark-GGUF) is a 624M-parameter BF16 **draft model** for speculative decoding with the **Spark-X2.6-4B target model**. The draft proposes tokens and the target verifies them. Use both models with a runtime that implements the documented DSpark path; normal Spark architecture support alone is not evidence of DSpark support. The model card provides the required runtime and commands.

The reported BF16 mean speedups are 2.14× on RTX 4090 with llama.cpp and 2.50× on M5 Pro with MLX. The 2.94× maximum was measured on MATH500 with BF16 on M5 Pro; the 532 tok/s peak was measured on GSM8K with Q4_K_M on RTX 4090. These are different configurations, not universal guarantees or a single combined result. Compare the same task, target quantization, context and hardware with and without DSpark.

### A tool returned successfully, or the output is valid JSON. Is the task complete?

Not necessarily. Check that the final answer was actually delivered, the tool result was used correctly, and the output satisfies your application's rules. A schema-valid response can still contain an incorrect decision, and a thinking or tool-call budget can be exhausted before the final answer is produced.

For bounded tasks, select a suitable thinking budget, retain the final output and stop reason, and validate important calculations or decisions in application code. Earlier Spark-X2.5 community experiments illustrate these failure modes; their scores should not be presented as Spark-X2.6 benchmark results. See the [tool-use experiment](https://huggingface.co/XHToken/Spark-X2.5-4B/discussions/19) and [structured-decision experiment](https://huggingface.co/XHToken/Spark-X2.5-1.7B/discussions/4).

## 中文

本页适用于 Spark-X2.6-4B / 1.7B 及 4B DSpark 草稿模型。历史 Spark-X2.5 问答保留在 [Wiki FAQ](https://github.com/XHToken/Spark-X2.6/wiki/FAQ)；复用旧版部署示例或评测结果前，请先核对模型代际与运行时。

### Spark-X2.6 主要用于什么场景？支持图片输入吗？

已发布的 4B、1.7B 模型面向文本生成、代码、工具调用和 Agent 任务，也可用于端侧应用；模型本身不原生接收图片输入。需要理解截图或文档时，应用应另接 OCR 或视觉能力，再把其文本结果交给 Spark。客户端显示上传图片按钮，不代表模型具备视觉能力。

参见 [模型介绍](README.md#introduction)及 [4B](https://huggingface.co/XHToken/Spark-X2.6-4B)、[1.7B](https://huggingface.co/XHToken/Spark-X2.6-1.7B) 模型卡。选型应依据实际任务验证，不能把参数规模当作准确率保证。

### 在哪里下载并本地运行？Mac 用户从哪里开始？

先查看 [官方下载渠道](README.md#model-downloads)与 [运行说明](README.md#quickstart)。X2.6 合集和 Ollama 组织页提供两种模型规模，请确认选择的是 X2.6，并使用运行时支持的权重格式。

Apple Silicon 用户可查看 [Spark-MLX-LLM](https://github.com/XHToken/Spark-MLX-LLM)，它提供本地生成、交互聊天和 OpenAI 兼容服务；硬件与后端要求以该项目说明为准。仅凭笔记本型号不能保证某个配置可以运行，反馈时请注明可用内存/显存、权重精度、运行时、上下文长度和并发数。模型文件大小不包含全部运行时和上下文内存开销。

### DSpark 能独立聊天吗？是否在任何设备上都能加速两倍？

不能独立替代目标模型。[Spark-X2.6-4B-DSpark-GGUF](https://huggingface.co/XHToken/Spark-X2.6-4B-DSpark-GGUF) 是配合 **Spark-X2.6-4B 目标模型**使用的 624M 参数 BF16 **草稿模型**：草稿提出 token，目标模型负责验证。需要同时使用两者及实现了 DSpark 路径的运行时；普通 Spark 架构可加载，不等于已经支持 DSpark。具体运行时与命令以模型卡为准。

官方测试的 BF16 平均加速分别为 RTX 4090 / llama.cpp 上的 2.14×、M5 Pro / MLX 上的 2.50×。最高 2.94× 来自 M5 Pro 的 BF16 MATH500 测试，532 tok/s 峰值来自 RTX 4090 的 Q4_K_M GSM8K 测试。这是不同配置下的结果，不是所有设备上的保证，也不是同一组测试同时达到两个峰值。实测应固定任务、目标模型量化、上下文和硬件，对比启用前后表现。

### 工具调用成功或 JSON 格式合法，就代表任务完成了吗？

不一定。还要检查最终答案是否真正交付、是否正确使用了工具结果，以及输出是否满足业务规则。符合 Schema 的响应仍可能决策错误；思考或工具调用预算也可能在最终答案产生前耗尽。

对有明确边界的任务，应选择合适的思考预算，保留最终输出与停止原因，并通过应用代码校验关键计算和决策。此前 Spark-X2.5 社区案例展示过这些失败模式，但不能把它们的分数写成 Spark-X2.6 评测结果。可参考 [工具调用案例](https://huggingface.co/XHToken/Spark-X2.5-4B/discussions/19)与 [结构化决策案例](https://huggingface.co/XHToken/Spark-X2.5-1.7B/discussions/4)。
