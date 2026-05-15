---
name: hf-model-explorer
description: |
  探索和分析 HuggingFace Transformers 模型结构。查看层级架构、模块名称与类型、
  参数统计（总参数/可训练参数/每层参数/模型大小/数据类型）、
  对比两个模型的结构差异。当用户提到以下内容时使用此技能：
  探索模型结构、分析模型结构、查看模型参数、模型架构、model structure、model parameters、
  model architecture、explore model、模型对比、compare models、
  查看模型层、model layers、参数统计、parameter count、
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
4. **HF 模型卡片（完整）** — 从 HuggingFace Hub 获取模型的所有元信息（README 全文、card_data、文件列表、datasets、language、base_model、评测指标等）
5. **仓库文件下载与分析** — 下载仓库中除权重外的所有配置文件（config.json、tokenizer_config.json、generation_config.json、preprocessor_config.json 等），作为分析的参考依据
6. **config.json 校对** — 所有结构信息必须与 config.json 原始值严格一致，自动交叉验证并标注差异
7. **模型对比** — 两个模型的配置差异、参数量对比、结构差异
8. **降级支持** — Meta device 加载失败时自动从 config 构建合成结构树和参数估算

## 核心原则：100% 准确性

**所有输出信息必须可溯源、可验证：**
- 结构参数必须来自 config.json 原始字段，不得猜测或假设
- 每个数值必须标注来源（config.json 字段名 or 模型实际加载）
- 当 config.json 中不存在某字段时，必须明确标注"未在 config 中指定"
- 参数量估算公式必须公开列出，便于读者自行验证
- 如有不确定项，标注 ⚠️ 并说明原因

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

### 步骤 3：下载仓库配置文件并校对

**此步骤为强制步骤，不可跳过。**

脚本会自动下载仓库中除权重文件外的所有文件，用于分析参考：

```bash
~/py312/bin/python3 <SKILL_DIR>/scripts/explore_model.py "<MODEL_NAME>" --output config --trust-remote-code --download-repo-files
```

**自动下载的文件类型（排除权重文件）：**
- `config.json` — 模型配置（核心校对依据）
- `tokenizer_config.json` — 分词器配置
- `tokenizer.json` — 分词器定义
- `special_tokens_map.json` — 特殊 token 映射
- `generation_config.json` — 生成配置
- `preprocessor_config.json` — 预处理器配置（视觉/音频模型）
- `chat_template.jinja` / `chat_template.json` — 对话模板
- `vocab.json` / `merges.txt` / `added_tokens.json` — 词表文件
- 其他 `.json`、`.txt`、`.jinja`、`.yaml`、`.md` 等非权重文件

**排除的权重文件模式：**
- `*.safetensors`, `*.bin`, `*.gguf`, `*.pth`, `*.pt`, `*.h5`
- `*.msgpack`

**校对规则：**
1. 逐一比对步骤 2 产出的每个数值与 config.json 原始字段
2. 如发现不一致，以 config.json 为准，在文档中修正并标注
3. 特别注意以下容易出错的字段：
   - `num_key_value_heads` vs `num_attention_heads`（GQA 时不同）
   - `intermediate_size` vs `moe_intermediate_size`（MoE 模型两者不同）
   - `tie_word_embeddings`（影响总参数量计算）
   - `head_dim`（可能与 `hidden_size / num_attention_heads` 不同）
   - 子配置中的字段（`text_config.*`, `vision_config.*` 等）
4. 参考 `generation_config.json` 补充生成相关参数
5. 参考 `tokenizer_config.json` 补充分词器信息（vocab_size 验证、special tokens 等）
6. 参考 `preprocessor_config.json` 补充视觉/音频预处理信息
7. 校对结果写入输出 JSON 的 `validation` 字段

### 步骤 4：获取完整模型卡片信息

脚本已自动获取完整模型卡片，`model_card` 字段包含：
- **基本信息**：model_id, author, sha, created_at, last_modified, private, gated, disabled
- **统计数据**：downloads, likes, trending_score
- **分类标签**：tags, pipeline_tag, library_name
- **元数据（card_data）**：license, language, datasets, metrics, base_model, model_name, co2_eq_emissions, eval_results
- **文件列表**：siblings（模型仓库中的所有文件名和大小）
- **README 内容**：完整 README.md 文本（含模型介绍、用法、评测结果等）
- **所需版本**：transformers_version, required_transformers_version

**使用 model_card 时，确保以下信息在最终文档中体现：**
- 模型介绍段落（来自 README）
- License 信息
- 训练数据集（如有）
- 基座模型（base_model，如有）
- 评测结果（eval_results，如有）
- 所需 transformers 最低版本
- 生成配置（来自 generation_config.json）
- 分词器信息（来自 tokenizer_config.json）

### 步骤 5：生成深度分析 Markdown 文档

将 JSON 结果结合校对后的数据，格式化为详细的中文 Markdown 文档。**必须参考 `models/` 目录下已有的分析文档风格**（如 `Qwen3-VL-30B-A3B-Instruct-Analysis.md`、`Qwen3-Omni-30B-A3B-Instruct-Analysis.md`），产出同等深度和质量的文档。

#### 输出模板

```markdown
# <模型名称> 完整结构详解

> HuggingFace: https://huggingface.co/<model_id>
> 基于 HuggingFace config.json 和 transformers 源码分析
> 所需 transformers 版本: >=x.x.x
> License: <license>
> 基座模型: <base_model>（如有）

<模型简介，来自 README>

## 一、模型元信息

| 项目 | 值 |
|---|---|
| 模型 ID | <model_id> |
| 作者 | <author> |
| License | <license> |
| 基座模型 | <base_model> |
| 训练数据 | <datasets> |
| 语言 | <language> |
| 下载量 | <downloads> |
| Pipeline | <pipeline_tag> |
| 所需 transformers | >=<version> |
| 仓库文件 | <主要文件列表及大小> |

### 生成配置（来自 generation_config.json）

| 参数 | 值 |
|---|---|
| max_new_tokens | <值> |
| temperature | <值> |
| top_p | <值> |
| top_k | <值> |
| do_sample | <值> |
| repetition_penalty | <值> |
| eos_token_id | <值> |
| ... | ... |

### 分词器信息（来自 tokenizer_config.json）

| 参数 | 值 |
|---|---|
| tokenizer_class | <值> |
| vocab_size | <值> |
| model_max_length | <值> |
| special_tokens | <列出所有 special tokens> |
| chat_template | <是否有，简述格式> |
| ... | ... |

## 二、模型总体架构

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

| 参数 | 值 | config.json 字段 |
|---|---|---|
| 架构 | <architectures> | `architectures` |
| 模型类型 | <model_type> | `model_type` |
| 总参数量 | <total_str> | 计算得出 |
| 激活参数量 | <active_params>（MoE 模型需标注）| 计算得出 |
| 模型大小 | <size_str> | 基于 `torch_dtype` 计算 |
| 隐藏维度 | <hidden_size> | `hidden_size` |
| 层数 | <num_hidden_layers> | `num_hidden_layers` |
| 注意力头数 | <num_attention_heads> / <num_key_value_heads> KV heads | `num_attention_heads` / `num_key_value_heads` |
| 词表大小 | <vocab_size> | `vocab_size` |
| 最大上下文 | <max_position_embeddings> | `max_position_embeddings` |
| 精度 | <torch_dtype> | `torch_dtype` |

> ⚠️ 校验说明：以上所有数值均已与 config.json 原始值逐一核对。

## 三、Attention 结构详解

### 2.1 关键参数

| 组件 | 权重形状 | 说明 | config.json 依据 |
|---|---|---|---|
| q_proj | Linear(hidden, q_dim, bias=?) | N heads × head_dim | `num_attention_heads` × `head_dim` |
| k_proj | Linear(hidden, kv_dim, bias=?) | N_kv heads × head_dim | `num_key_value_heads` × `head_dim` |
| v_proj | Linear(hidden, kv_dim, bias=?) | N_kv heads × head_dim | `num_key_value_heads` × `head_dim` |
| o_proj | Linear(q_dim, hidden, bias=?) | 输出投影 | |

（如果是 MLA：展开 q_a_proj, q_b_proj, kv_a_proj_with_mqa, kv_b_proj 等）

### 2.2 位置编码

| 参数 | 值 | config.json 字段 |
|---|---|---|
| rope_theta | <值> | `rope_theta` |
| rope_scaling | <类型和参数> | `rope_scaling` |
| M-RoPE | <如有，展示 section 分割> | `rope_scaling.mrope_section` |

## 四、FFN / MoE 结构详解

### 标准 Dense FFN（如有）
\`\`\`
gate_proj: Linear(hidden, intermediate, bias=?)
up_proj:   Linear(hidden, intermediate, bias=?)
down_proj: Linear(intermediate, hidden, bias=?)
激活函数: SiLU (SwiGLU)
\`\`\`
config.json 依据: `intermediate_size` = <值>

### MoE Block（如有）

| 参数 | 值 | config.json 字段 |
|---|---|---|
| 专家总数 | <num_experts> | `n_routed_experts` / `num_local_experts` |
| 每 token 激活 | <num_experts_per_tok> | `num_experts_per_tok` |
| 专家 FFN 维度 | <moe_intermediate_size> | `moe_intermediate_size` |
| 共享专家 | <shared_expert> | `n_shared_experts` |
| Dense 层数 | <first_k_dense_replace> | `first_k_dense_replace` |
| 路由策略 | <topk_method, scoring_func> | `topk_method`, `scoring_func` |

\`\`\`
Router:
  Linear(hidden, num_experts) → <scoring_func> → top-<k> → 归一化

每个专家 (SwiGLU):
  gate_up_proj: (E, 2×moe_intermediate, hidden)
  down_proj:    (E, hidden, moe_intermediate)
\`\`\`

## 五、[子模块名] 详细结构
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

## N+3. 评测结果（如有）

来自模型卡片 eval_results：
| Benchmark | Score |
|---|---|
| ... | ... |

## N+4. 参数量计算验证

列出参数量估算公式，确保读者可自行验证：
\`\`\`
Embedding: vocab_size × hidden_size = ...
每层 Attention: ...
每层 MLP: ...
总计: ...
\`\`\`

## N+5. 核心亮点

1. **特点 1** — 描述
2. **特点 2** — 描述
...
```

**关键要求：**
- 所有权重形状必须标注具体维度数字，且标注来源 config.json 字段
- Forward 流程需追踪每一步的 tensor shape 变化
- MoE 模型必须区分总参数与激活参数
- MLA 模型需展开 latent attention 的完整投影链
- 多模态模型需逐个分析每个子编码器
- 量化模型需说明哪些模块被量化、哪些未量化
- **每个数值旁必须标注对应的 config.json 字段名**
- **参数量计算必须列出完整公式**
- **generation_config.json 和 tokenizer_config.json 的信息必须体现**

### 步骤 6：保存分析文档

将生成的 Markdown 文档写入 `models/<ModelName>-Analysis.md`。
模型名称中的 `/` 替换为 `-`，例如：
- `Qwen/Qwen3-30B-A3B` → `models/Qwen3-30B-A3B-Analysis.md`
- `moonshotai/Kimi-K2.6` → `models/Kimi-K2.6-Analysis.md`

## 工作流二：模型对比

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
| `model_card` | HF 模型卡片完整信息（见下方详细列表） |
| `key_config` | 关键配置：architectures, model_type, hidden_size, num_hidden_layers, vocab_size 等 |
| `raw_config` | config.json 原始完整 JSON（`--dump-raw-config` 时输出） |
| `repo_files` | 下载的仓库配置文件内容（`--download-repo-files` 时输出） |
| `moe_info` | MoE 检测结果：is_moe, expert_counts, architecture, routing |
| `mla_info` | MLA 检测结果：is_mla, kv_lora_rank, q_lora_rank, head_dim 分解 |
| `quant_info` | 量化检测结果：is_quantized, method, bits, group_size, ignore_patterns |
| `sub_configs` | 多模态子配置：text_config, vision_config, audio_config 等的关键参数 |
| `tree_text` | 模型结构树的文本表示（来自实际模型或合成树） |
| `tree` | 结构化的树节点列表 |
| `params` | 参数统计：total, trainable, size, top_modules, dtype_dist |
| `estimated_params` | config 估算的参数量（加载失败时） |
| `validation` | config.json 校对结果：checked_fields, mismatches, warnings |
| `warning` | 加载过程中的警告信息 |

### model_card 字段详细内容

| 子字段 | 说明 |
|---|---|
| `model_id` | 模型 ID |
| `author` | 作者/组织 |
| `sha` | 最新 commit SHA |
| `created_at` | 创建时间 |
| `last_modified` | 最后修改时间 |
| `private` | 是否私有 |
| `gated` | 是否需要申请访问 |
| `disabled` | 是否被禁用 |
| `tags` | 标签列表 |
| `pipeline_tag` | Pipeline 类型 |
| `library_name` | 库名称 |
| `license` | License |
| `downloads` | 下载量 |
| `likes` | 点赞数 |
| `trending_score` | 热度分 |
| `card_data` | 完整 card_data（language, datasets, metrics, base_model, eval_results 等） |
| `siblings` | 文件列表（含文件名和大小） |
| `readme_content` | README.md 完整内容 |
| `introduction` | 模型简介段落（从 README 提取） |
| `required_transformers_version` | 所需 transformers 版本 |

### repo_files 字段内容

下载的仓库非权重文件，每个文件作为一个 key-value 对：

| key（文件名） | value（内容） |
|---|---|
| `config.json` | 模型配置 JSON（原始完整内容） |
| `tokenizer_config.json` | 分词器配置 |
| `generation_config.json` | 生成配置 |
| `preprocessor_config.json` | 预处理器配置 |
| `special_tokens_map.json` | 特殊 token 映射 |
| `chat_template.jinja` | 对话模板 |
| 其他非权重文件... | 文件内容 |

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
- 生成的 Markdown 分析文档应保存到 `models/` 目录，与已有文档风格保持一致
- **所有数值必须与 config.json 交叉验证后才能写入最终文档**
- **仓库中的非权重文件（tokenizer_config、generation_config 等）都必须下载并参考**
