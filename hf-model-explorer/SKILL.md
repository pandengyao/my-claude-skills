---
name: hf-model-explorer
description: |
  探索和分析 HuggingFace Transformers 模型结构。查看层级架构、模块名称与类型、
  参数统计（总参数/可训练参数/每层参数/模型大小/数据类型）、生成架构可视化图、
  对比两个模型的结构差异。当用户提到以下内容时使用此技能：
  探索模型结构、分析模型结构、查看模型参数、模型架构、model structure、model parameters、
  model architecture、explore model、模型对比、compare models、模型可视化、
  model visualization、查看模型层、model layers、参数统计、parameter count、
  模型大小、model size、HuggingFace模型、transformers模型。
  当用户提供一个 HuggingFace 模型名称（如 bert-base-uncased、Qwen/Qwen3-30B-A3B）
  并希望了解其架构、参数分布或与其他模型对比时，也应使用此技能。
---

# HuggingFace Model Explorer

探索和分析 HuggingFace Transformers 模型的结构、参数和架构。

## 功能

1. **结构概览** — 查看模型层级架构树、模块名称与类型
2. **参数统计** — 总参数量、可训练参数、每模块参数占比、模型大小、dtype 分布
3. **高级架构检测** — MoE（混合专家）、MLA（多头潜在注意力）、量化配置、多模态子配置
4. **HF 模型卡片** — 从 HuggingFace Hub 获取模型简介、license、所需 transformers 版本
5. **架构可视化** — 生成交互式 HTML 可视化页面（真正树形结构 + 参数量柱状条 + 颜色编码 + 信息卡片）
6. **模型对比** — 两个模型的配置差异、参数量对比、结构差异
7. **降级支持** — Meta device 加载失败时自动从 config 构建合成结构树和参数估算

## 环境要求

使用 Python 3.12 虚拟环境 `~/py312`，所有脚本命令统一使用 `~/py312/bin/python3` 执行。

检查依赖：
```bash
~/py312/bin/python3 -c "import transformers, torch; print('OK')"
```

如未安装：
```bash
~/py312/bin/pip install transformers torch huggingface_hub
```

## 工作流一：模型结构深度分析

当用户想查看某个模型的结构或参数时，按以下步骤执行。最终产出一份与 `models/` 目录下已有文档风格一致的详细分析文档。

### 步骤 1：确认模型标识

获取用户提供的模型名称或本地路径。例如：
- HuggingFace Hub: `bert-base-uncased`, `Qwen/Qwen3-30B-A3B`, `moonshotai/Kimi-K2.6`
- 本地路径: `/path/to/model/`

如模型可能需要认证（Llama、Gemma 等），确认用户是否已通过 `huggingface-cli login` 登录。

### 步骤 2：运行探索脚本

```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/explore_model.py "<MODEL_NAME>" --output full --trust-remote-code --max-depth 4
```

其中 `<SKILL_DIR>` 是此 skill 的安装目录。

**可用选项：**
- `--output structure` — 仅输出结构树
- `--output params` — 仅输出参数统计
- `--output config` — 仅输出配置（最快，不下载权重）
- `--output full` — 全部输出（默认）
- `--config-only` — 仅加载配置，不使用模型权重（适合超大模型快速查看）
- `--trust-remote-code` — 信任远程代码（自定义架构需要）
- `--token TOKEN` — HuggingFace 认证 token
- `--max-depth N` — 树结构最大展示深度（默认 3，深度分析建议用 4）

对于超大模型（>30B 参数），建议先用 `--config-only` 快速查看配置。

### 步骤 3：补充信息收集（可选）

如果脚本输出的信息不够深入，可额外收集以下信息：

**3a. 从 HF 模型卡片获取信息**
脚本已自动获取 `model_card` 字段，包含：
- 模型简介（README 摘要）
- 所需 transformers 版本
- license、标签、下载量

**3b. 从 config.json 补充**
如需查看完整 config：
```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/explore_model.py "<MODEL_NAME>" --output config --trust-remote-code
```
重点关注 JSON 中的 `sub_configs`（多模态子配置）、`moe_info`（MoE 信息）、`mla_info`（MLA 信息）、`quant_info`（量化信息）。

**3c. 从 transformers 源码验证**
对于复杂架构（MoE、MLA、多模态），可查阅 transformers 源码验证结构细节：
- 模型类定义中的 `forward()` 方法
- Attention 类中的权重形状
- MoE Router 的路由策略

### 步骤 4：生成深度分析 Markdown 文档

将 JSON 结果结合补充信息，格式化为详细的中文 Markdown 文档。**必须参考 `models/` 目录下已有的分析文档风格**（如 `Qwen3-VL-30B-A3B-Instruct-Analysis.md`、`Qwen3-Omni-30B-A3B-Instruct-Analysis.md`），产出同等深度和质量的文档。

#### 输出模板

```markdown
# <模型名称> 完整结构详解

> 基于 HuggingFace config.json 和 transformers 源码分析
> 所需 transformers 版本: >=x.x.x

<模型简介，来自 model_card.summary 或 HF 模型卡片>

---

## 一、模型总体架构

\`\`\`
<ASCII 结构树，展示主要子模块的层级关系>
<参考 Qwen3-Omni 文档中的树形风格：>
<ModelForCausalLM>
  ├── model: <TextModel>
  │     ├── embed_tokens: Embedding(vocab, hidden)
  │     ├── layers: N × DecoderLayer
  │     │     ├── self_attn: Attention (GQA/MLA/MHA)
  │     │     └── mlp: MLP / MoE Block
  │     └── norm: RMSNorm
  └── lm_head: Linear(hidden, vocab)
\`\`\`

### 总体参数概览

| 参数 | 值 |
|---|---|
| 架构 | <architectures> |
| 模型类型 | <model_type> |
| 总参数量 | <total_str> |
| 激活参数量 | <active_params>（MoE 模型需标注）|
| 模型大小 | <size_str> |
| 隐藏维度 | <hidden_size> |
| 层数 | <num_hidden_layers> |
| 注意力头数 | <num_attention_heads> / <num_key_value_heads> KV heads |
| 词表大小 | <vocab_size> |
| 最大上下文 | <max_position_embeddings> |
| 精度 | <torch_dtype> |

## 二、Attention 结构详解

### 2.1 关键参数

| 组件 | 权重形状 | 说明 |
|---|---|---|
| q_proj | Linear(hidden, q_dim, bias=?) | N heads × head_dim |
| k_proj | Linear(hidden, kv_dim, bias=?) | N_kv heads × head_dim |
| v_proj | Linear(hidden, kv_dim, bias=?) | N_kv heads × head_dim |
| o_proj | Linear(q_dim, hidden, bias=?) | 输出投影 |

（如果是 MLA：展开 q_a_proj, q_b_proj, kv_a_proj_with_mqa, kv_b_proj 等）

### 2.2 位置编码

| 参数 | 值 |
|---|---|
| rope_theta | <值> |
| rope_scaling | <类型和参数> |
| M-RoPE | <如有，展示 section 分割> |

## 三、FFN / MoE 结构详解

### 标准 Dense FFN（如有）
\`\`\`
gate_proj: Linear(hidden, intermediate, bias=?)
up_proj:   Linear(hidden, intermediate, bias=?)
down_proj: Linear(intermediate, hidden, bias=?)
激活函数: SiLU (SwiGLU)
\`\`\`

### MoE Block（如有）

| 参数 | 值 | 说明 |
|---|---|---|
| 专家总数 | <num_experts> | |
| 每 token 激活 | <num_experts_per_tok> | |
| 专家 FFN 维度 | <moe_intermediate_size> | |
| 共享专家 | <shared_expert> | |
| Dense 层数 | <first_k_dense_replace> | |
| 路由策略 | <topk_method, scoring_func> | |

\`\`\`
Router:
  Linear(hidden, num_experts) → <scoring_func> → top-<k> → 归一化

每个专家 (SwiGLU):
  gate_up_proj: (E, 2×moe_intermediate, hidden)
  down_proj:    (E, hidden, moe_intermediate)
\`\`\`

## 四、[子模块名] 详细结构
（多模态模型的 Vision Encoder、Audio Encoder 等，每个主要子模块一个章节）

### 4.1 关键参数表
### 4.2 结构图
### 4.3 Forward 流程（精确维度追踪）

## N-1. 完整 Decoder Layer (×N)

\`\`\`
输入: hidden_states (B, S, hidden)
  ├─ Norm
  ├─ Attention
  ├─ + residual
  ├─ Norm
  ├─ MLP / MoE
  ├─ + residual
输出: (B, S, hidden)
\`\`\`

## N. 量化信息（如有）

| 参数 | 值 |
|---|---|
| 量化方法 | <method> |
| 位数 | <bits> |
| 量化范围 | <targets> |
| 未量化模块 | <ignore_patterns> |

## N+1. 端到端数据流

\`\`\`
═══════════════════ Forward 完整流程 ═══════════════════
1. input_ids → Embedding → inputs_embeds
2. （多模态编码，如有）
3. N × DecoderLayer
4. Norm → lm_head → logits
\`\`\`

## N+2. 各模块对比总结表（如有多个子模块）

| 特征 | 模块A | 模块B | ... |
|---|---|---|---|
| 层数 | | | |
| 隐藏维度 | | | |
| Attention 类型 | | | |
| FFN 类型 | | | |
| ... | | | |

## N+3. 核心亮点

1. **特点 1** — 描述
2. **特点 2** — 描述
...
```

**关键要求：**
- 所有权重形状必须标注具体维度数字
- Forward 流程需追踪每一步的 tensor shape 变化
- MoE 模型必须区分总参数与激活参数
- MLA 模型需展开 latent attention 的完整投影链
- 多模态模型需逐个分析每个子编码器
- 量化模型需说明哪些模块被量化、哪些未量化

### 步骤 5：保存分析文档

将生成的 Markdown 文档写入 `models/<ModelName>-Analysis.md`。
模型名称中的 `/` 替换为 `-`，例如：
- `Qwen/Qwen3-30B-A3B` → `models/Qwen3-30B-A3B-Analysis.md`
- `moonshotai/Kimi-K2.6` → `models/Kimi-K2.6-Analysis.md`

### 步骤 6：生成 HTML 可视化（可选，用户要求时执行）

```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/visualize_model.py "<MODEL_NAME>" --output models/<ModelName>_architecture.html --open --trust-remote-code --max-depth 4
```

HTML 可视化包含：
- **真正的树形结构**：CSS 连线的可展开折叠树，带彩色图标（Attention=蓝、MLP=绿、MoE=橙、Norm=黄、Embed=紫）
- **参数分布柱状图**：水平条形图，展示 Top 模块参数占比
- **信息卡片**：基础参数、MoE 信息、MLA 信息、量化信息（按需显示）
- **合成树降级**：模型加载失败时用黄色警告横幅标注为估算结果

## 工作流二：架构可视化（独立）

当用户仅要求可视化查看模型结构时执行。

```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/visualize_model.py "<MODEL_NAME>" --output models/<ModelName>_architecture.html --open --trust-remote-code --max-depth 4
```

**可用选项：**
- `--output PATH` — HTML 输出路径
- `--open` — 生成后自动在浏览器中打开
- `--max-depth N` — 展示深度（可视化建议用 4）
- `--config-only` — 仅从配置生成（不加载模型权重）
- `--trust-remote-code` — 信任远程代码
- `--token TOKEN` — HuggingFace 认证 token

生成后告知用户文件路径，并建议在浏览器中打开查看。

## 工作流三：模型对比

当用户想对比两个模型时执行。

```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/compare_models.py "<MODEL_A>" "<MODEL_B>" --trust-remote-code
```

**可用选项：**
- `--config-only` — 仅对比配置
- `--trust-remote-code` — 信任远程代码
- `--token TOKEN` — HuggingFace 认证 token

### 格式化对比结果

```markdown
# <模型A> vs <模型B> 结构对比

## 一、参数量对比

| 指标 | <模型A> | <模型B> |
|---|---|---|
| 总参数量 | <a_total_str> | <b_total_str> |
| 参数比 | 1 | <ratio> |

### 各模块参数对比

| 模块 | <模型A> | <模型B> |
|---|---|---|
| <module> | <a_str> | <b_str> |

## 二、配置差异

| 配置项 | <模型A> | <模型B> |
|---|---|---|
| <key> | <val_a> | <val_b> |

## 三、架构特征对比

| 特征 | <模型A> | <模型B> |
|---|---|---|
| MoE | <info_a> | <info_b> |
| MLA | <info_a> | <info_b> |
| 量化 | <info_a> | <info_b> |
| 子配置 | <info_a> | <info_b> |

## 四、结构差异

- 仅在 <模型A> 中存在的模块: ...
- 仅在 <模型B> 中存在的模块: ...
- 类型变化的模块: ...
```

## 脚本输出 JSON 字段参考

`explore_model.py --output full` 输出的 JSON 包含以下主要字段：

| 字段 | 说明 |
|---|---|
| `model_card` | HF 模型卡片信息：summary, license, tags, transformers_version, required_transformers_version |
| `key_config` | 关键配置：architectures, model_type, hidden_size, num_hidden_layers, vocab_size 等 |
| `moe_info` | MoE 检测结果：is_moe, expert_counts, architecture, routing |
| `mla_info` | MLA 检测结果：is_mla, kv_lora_rank, q_lora_rank, head_dim 分解 |
| `quant_info` | 量化检测结果：is_quantized, method, bits, group_size, ignore_patterns |
| `sub_configs` | 多模态子配置：text_config, vision_config, audio_config 等的关键参数 |
| `tree_text` | 模型结构树的文本表示（来自实际模型或合成树） |
| `tree` | 结构化的树节点列表 |
| `params` | 参数统计：total, trainable, size, top_modules, dtype_dist |
| `estimated_params` | config 估算的参数量（加载失败时） |
| `warning` | 加载过程中的警告信息 |

## 错误处理

脚本输出 JSON 中包含 `error` 字段时，根据情况处理：

| 错误类型 | 处理方式 |
|---|---|
| 缺少依赖 | 显示 `fix` 字段中的 pip install 命令 |
| 认证失败 (401/gated) | 提示运行 `huggingface-cli login` 或使用 `--token` |
| 模型不存在 (404) | 提示检查模型名称 |
| 内存不足 (OOM) | 使用 `--config-only` 重试 |
| Meta device 失败 | 脚本自动回退：从 config 构建合成树 + 参数估算，输出中会包含 `warning` 和 `_synthetic` 标记 |
| transformers 版本不兼容 | 提示升级 transformers：`pip install --upgrade transformers` |

## 注意事项

- 脚本使用 `torch.device("meta")` 加载模型，零内存占用，70B+ 模型也能在普通笔记本上分析
- Meta 加载失败时自动降级为配置估算模式，仍能产出结构树和参数估算
- MoE 模型（如 Qwen3-30B-A3B、Mixtral、DeepSeek-V3）自动检测并区分总参数与激活参数
- MLA 模型（如 DeepSeek-V3、Kimi-K2.6）自动检测 latent attention 结构
- 量化模型自动解析量化配置（compressed-tensors、FP8、GPTQ、AWQ、BitsAndBytes）
- 多模态模型自动检测并分析所有子配置（vision/audio/text/thinker/talker 等）
- 对于自定义架构的模型，需要 `--trust-remote-code` 参数
- 可视化 HTML 是自包含的（无外部依赖），可以保存后随时离线查看
- 生成的 Markdown 分析文档应保存到 `models/` 目录，与已有文档风格保持一致
