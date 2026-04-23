---
name: file-covert-to-markdown
description: 将各种文件格式转换为 Markdown 格式，以便 LLM 处理和文本分析。基于 Microsoft 的 markitdown 工具。
---

# file-covert-to-markdown Skill

将各种文件格式转换为 Markdown，以便 LLM 处理和文本分析。基于 Microsoft 的 markitdown 工具。

## 何时使用

当用户需要：
- 从 PDF 提取文本内容
- 转换 Word/Excel/PowerPoint 文档为 Markdown
- 从图片中提取文字（OCR）
- 转换音频为文字（转录）
- 解析 HTML/CSV/JSON/XML 文件
- 提取 ZIP 文件内容
- 获取 YouTube 视频字幕
- 转换 EPUB 电子书

**不适用于**：
- 需要高保真格式转换供人类阅读（markitdown 优化的是 LLM 处理，而非人类视觉呈现）
- 实时流式转换大型文件（可能内存消耗较大）

## 工作流程

1. **检查依赖**
   - 检查是否安装了 markitdown
   - 如未安装，提供安装命令

2. **确定转换需求**
   - 识别文件类型
   - 确认是否需要特殊功能（如 OCR、语音转录）

3. **执行转换**
   - 使用 CLI 或 Python API
   - 处理输出

4. **返回结果**
   - 展示转换后的 Markdown 内容
   - 如需要，保存到文件

## 安装

基础安装（所有功能）：
```bash
~/py312/bin/pip install 'markitdown[all]'
```

按需安装（特定格式）：
```bash
# 仅 PDF、Word、PowerPoint
~/py312/bin/pip install 'markitdown[pdf,docx,pptx]'

# 可选依赖：
# [pdf] - PDF 文件
# [docx] - Word 文档
# [pptx] - PowerPoint
# [xlsx] - Excel
# [xls] - 旧版 Excel
# [outlook] - Outlook 邮件
# [audio-transcription] - 音频转录
# [youtube-transcription] - YouTube 字幕
# [az-doc-intel] - Azure 文档智能
```

从源码安装：
```bash
git clone https://github.com/microsoft/markitdown.git
cd markitdown
~/py312/bin/pip install -e 'packages/markitdown[all]'
```

## 使用示例

### CLI 使用

基础转换：
```bash
# 转换并输出到 stdout
markitdown path/to/file.pdf

# 输出到文件
markitdown path/to/file.pdf -o output.md

# 管道输入
cat file.pdf | markitdown > output.md
```

启用插件：
```bash
# 列出已安装插件
markitdown --list-plugins

# 使用插件转换
markitdown --use-plugins file.pdf
```

使用 Azure 文档智能：
```bash
markitdown file.pdf -o output.md -d -e "<document_intelligence_endpoint>"
```

### Python API 使用

基础使用：
```python
from markitdown import MarkItDown

# 不启用插件
md = MarkItDown(enable_plugins=False)
result = md.convert("test.xlsx")
print(result.text_content)

# 启用插件
md = MarkItDown(enable_plugins=True)
result = md.convert("test.pdf")
print(result.text_content)
```

使用 LLM 进行图片描述：
```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(
    llm_client=client, 
    llm_model="gpt-4o",
    llm_prompt="optional custom prompt"
)
result = md.convert("example.jpg")
print(result.text_content)
```

使用 Azure 文档智能：
```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

### Docker 使用

```bash
# 构建镜像
docker build -t markitdown:latest .

# 运行转换
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```

## 技术细节

### 支持的文件格式

- **文档**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx, .xls)
- **图片**: 所有常见格式（支持 EXIF 元数据和 OCR）
- **音频**: WAV, MP3（支持 EXIF 元数据和语音转录）
- **网页**: HTML
- **文本格式**: CSV, JSON, XML
- **压缩包**: ZIP（迭代提取内容）
- **其他**: YouTube URLs, EPUB

### 插件系统

markitdown 支持第三方插件扩展功能：
- 搜索 GitHub 标签 `#markitdown-plugin` 查找可用插件
- 参考 `packages/markitdown-sample-plugin` 开发自己的插件

### 依赖版本要求

- Python 3.10 或更高版本
- 推荐使用虚拟环境避免依赖冲突

## 常见问题

**Q: 为什么选择 Markdown？**
A: Markdown 接近纯文本，主流 LLM（如 GPT-4o）原生支持，token 效率高。

**Q: 与 textract 的区别？**
A: markitdown 专注于保留文档结构（标题、列表、表格、链接），更适合 LLM 和文本分析管道。

**Q: 转换质量如何？**
A: 输出通常对人类可读，但主要为文本分析工具优化，不保证高保真度的人类消费体验。

## 实现模板

```python
def convert_file_to_markdown(file_path: str, output_path: str = None) -> str:
    """
    将文件转换为 Markdown
    
    Args:
        file_path: 输入文件路径
        output_path: 输出文件路径（可选）
    
    Returns:
        转换后的 Markdown 文本
    """
    from markitdown import MarkItDown
    
    md = MarkItDown()
    result = md.convert(file_path)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
    
    return result.text_content
```

## 相关链接

- GitHub: https://github.com/microsoft/markitdown
- PyPI: https://pypi.org/project/markitdown/
- MCP 服务器: https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp
- AutoGen 项目: https://github.com/microsoft/autogen

## 注意事项

1. **破坏性变更（0.0.1 到 0.1.0）**：
   - 依赖现在组织为可选功能组
   - `convert_stream()` 现在需要二进制文件对象
   - `DocumentConverter` 接口改为从流读取而非文件路径

2. **安全性**：不要处理不受信任的文件，特别是使用插件时

3. **资源使用**：大文件可能消耗大量内存，考虑分块处理或流式处理

4. **API 密钥**：使用 LLM 图片描述或 Azure 服务时需要相应的认证凭据
