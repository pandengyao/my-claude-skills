---
name: bilibili-subtitle-extractor
description: 从 Bilibili 视频提取字幕并校准整理为 Markdown 文档。当用户提到"提取字幕"、"提取B站字幕"、"Bilibili字幕"、"B站视频字幕"、"视频转文字"、"提取bilibili字幕"、"整理视频字幕"时使用此 skill。
---

# Bilibili 视频字幕提取与整理

从 Bilibili 视频中提取字幕（CC 字幕或 ASR 语音识别），经三引擎交叉校正后输出高质量 Markdown 文档。

## 工作流程

### Step 1: 尝试提取 CC 字幕

```bash
python3 ~/.claude/skills/bilibili-subtitle-extractor/scripts/extract.py "$ARGUMENTS"
```

- 输入: Bilibili 视频 URL（如 `https://www.bilibili.com/video/BVxxx`）或纯 BV 号
- 输出: JSON 格式的字幕数据（含视频元信息 + 带时间戳的字幕条目）
- 如果返回 `"error": "no_subtitle"`，进入 Step 1.5 的 ASR 流程

### Step 1.5: ASR 语音识别（无 CC 字幕时）

当视频无 CC 字幕时，使用三引擎 ASR 转写：

#### 1.5.1 提取音频

```bash
conda run -n aidev yt-dlp -x --audio-format mp3 'https://www.bilibili.com/video/BVxxx' -o '<视频标题>/audio.%(ext)s'
```

#### 1.5.2 三引擎转写

```bash
conda run -n aidev python3 ~/.claude/skills/bilibili-subtitle-extractor/scripts/asr.py <audio_file> [--skip-whisper]
```

**始终运行三引擎**（除非用 `--skip-whisper` 跳过 Whisper 以节省时间）：

| 引擎 | 模型 | 速度(15min) | 特点 |
|------|------|-------------|------|
| SenseVoice-Small | 阿里达摩院 | ~50s | 快速，带情绪/事件标签 |
| Paraformer-large | 阿里达摩院 | ~2min | 带标点恢复，CER~1.95% |
| Whisper large | OpenAI | ~30min(CPU) | 多语言，综合质量最高 |

#### 1.5.3 三引擎交叉校正

拿到三引擎结果后，执行交叉校正：

1. **按语义段对齐**: 将三个引擎的输出按时间/内容对齐到同一段落
2. **多数投票**: 当两个引擎一致而第三个不同时，采用多数版本
3. **LLM 语义判断**: 当三个都不同时，结合上下文选择最合理的版本
4. **专有名词确认**: 术语/人名需结合视频主题上下文确认

**常见错误模式**（基于实战经验）：
- Paraformer 易把"电脑"识别为"电长"、"望着"识别为"抱着"
- SenseVoice 在情绪激烈段落容易漏字
- Whisper 在语速快的口语讨论中偶有幻觉
- 三引擎互补效果显著，交叉校正后准确率远超单引擎

### Step 2: 校准与整理

对字幕（无论来源是 CC 还是 ASR）执行以下处理：

1. **碎片合并**: 将断句的字幕条目合并为完整句子

2. **文字纠错**: 修正 ASR 产生的错误：
   - 同音字/近音字错误
   - 专业术语错误（根据视频上下文推断）
   - 标点符号补全

3. **去冗余/口语转书面**:
   - 删除填充词："嗯"、"啊"、"那个"、"就是说"
   - 删除重复表达（口误重说的部分）
   - 口语化表达改为书面语（保持原意）

4. **分段**: 按语义主题自然分段，每段一个完整意思

### Step 3: 输出到文件

写入 `<视频标题>_<BV号>/<视频标题>_字幕.md`：

```markdown
# 视频标题

> UP主: xxx
> 原视频: https://www.bilibili.com/video/BVxxx
> 时长: MM:SS | 字幕条数: N
> ASR引擎: 三引擎综合校正（Whisper large + Paraformer-large + SenseVoice-Small）
> 校正方式: 多数投票 + LLM语义校准

---

## 整理版

（校准整理后的正文，分段排列）

---

<details>
<summary>原始字幕（点击展开）</summary>

[00:00] 校正后的带时间戳字幕
[00:02] ...

</details>
```

### Step 4: 对话中展示摘要

输出：
- 视频标题、UP主、时长
- 字幕来源（CC / ASR 三引擎校正）
- 整理后正文的前 3 段作为预览
- 文件输出路径

## 关键注意事项

### ASR 相关（重要！）

- **SenseVoice-Small 必须配合 VAD 使用**: 不加 `vad_model` 参数处理长音频（>30秒）会输出乱码！这是已验证的 bug。
- **Whisper 在 Apple Silicon 上很慢**: Python 版不支持 Metal GPU 加速，15分钟音频约需30分钟。提前告知用户。
- **Paraformer 的标点恢复**: 自动添加中文标点，质量较好但偶有错误，整理时需检查。
- **三引擎结果保存**: 将各引擎原始输出保存为 JSON 文件备查（sensevoice_result.json、paraformer_result.json）。

### 内容处理

- 超过 5000 字的内容分批校准整理
- 保持原文信息完整性，不添加原文没有的内容
- 校准时结合上下文理解语义，不机械替换
- 专业内容保留准确术语

## 环境要求

所有工具安装在 `aidev` conda 环境中：

```bash
# 激活环境
conda activate aidev

# 已安装的工具：
# - yt-dlp: 音频/视频下载
# - whisper (OpenAI): Whisper large-v3
# - funasr 1.3.1: Paraformer-large / SenseVoice-Small / FSMN-VAD / CT-Transformer
```

## 环境变量

- `BILIBILI_SESSDATA`: 可选。Bilibili 登录态 cookie，用于获取需要登录的视频字幕。
