## 第二阶段：多工具提取与交叉验证（Multi-Tool Extraction）

**核心理念**：根据PDF类型智能选择工具组合，用优先级规则融合多源信息，在提取质量和效率间取平衡。所有Python脚本使用 `~/py312/bin/python` 执行。

### ⚠️ 图片提取的第一原则：Closed-Loop（闭环控制）

**Open-loop（开环）= 必定出错**。凭感觉估算坐标（如"取页面上半部分"）的失败率 > 50%。

**Closed-loop（闭环）= 可靠**。必须遵循：
```
分析坐标（PyMuPDF text blocks） → 精确裁剪 → Read 回来视觉验证 → 发现问题则修正重裁
```

**为什么第一遍总是错，反馈后第二遍就对？**
- 第一遍是 open-loop：没有反馈信息，只能猜
- 第二遍是 closed-loop：看到了实际结果，知道哪里多了/少了，能精确修正

**解决方案**：将"看到实际结果"这一步内化到流程中——提取后立即 Read 回来自检，不等人类反馈。这就是"自动视觉验证"，即模拟人类 reviewer 的角色。

**执行约束**：
1. **禁止**使用 `fitz.Rect(margin, "估计y", page_width-margin, "估计y")` 这种凭比例猜测的裁剪
2. **必须**先运行 `get_text("dict")` 获取 text block bbox，找到 caption 精确位置
3. **必须**在所有图片提取完成后，用 Read 工具逐一视觉验证每张图片（模拟人类 reviewer 四边检查）
4. **必须**对验证失败的图片重新分析坐标并修正（最多 2 次重试，之后整页截图兜底）

**视觉验证时的"自我对话"模板**（Read 每张图片后必须逐条回答）：
```
Figure X 视觉验证：
- 上边缘：[图顶部的内容是什么？属于这个图吗？] → ✅/❌
- 下边缘：[图底部的内容是什么？Caption 最后一行完整吗？下面有没有正文？] → ✅/❌
- 左边缘：[最左侧内容完整吗？有没有其他列的内容混入？] → ✅/❌
- 右边缘：[最右侧的标签/文字完整吗？有没有被截断的单词？] → ✅/❌
- 结论：[通过 / 需修正哪条边]
```
如果任何一边 ❌，立即回到坐标分析修正该边界，不要等全部验证完再改。

**强制执行的代码结构要求**（防止跳步）：
- 提取脚本必须分为两个独立的 Python 脚本/Bash 命令：
  - **脚本1：坐标分析脚本** — 仅输出每个 Figure/Table 的精确 crop 坐标（打印为 JSON 或结构化文本），不执行任何裁剪。此脚本必须对每个目标 Figure/Table 执行以下操作：
    1. 定位 caption text block 的完整 bbox（含所有续行）
    2. 定位图形元素上界（`get_images()` / `get_drawings()` / 短文本标签的 min y）
    3. 定位 caption 下方第一个正文 text block 的 y0 作为下界
    4. 输出最终 crop rect
  - **脚本2：裁剪脚本** — 基于脚本1的输出执行裁剪和保存
- 这种分离确保坐标分析不会被跳过——如果没有脚本1的输出，脚本2无法运行

**常见失败模式及预防**（来自实际错误案例）：
| 失败模式 | 表现 | 预防方法 |
|---------|------|---------|
| 顶部混入无关内容 | Figure 1 截入论文标题/作者 | 必须用 `get_images()`/`get_drawings()` 定位图形元素的精确 y0，而非使用页面顶部 |
| 底部混入正文 | Table 截入下一节标题 | 必须找到 caption 下方第一个正文 block 的 y0 作为硬性下界 |
| 使用整个页面区域 | 右栏图片裁出左栏内容 | 必须使用目标栏的 x 范围，双栏论文 x 分界通常在 ~295-310 |
| Caption 不完整 | 多行 caption 只截了第一行 | 搜索 caption 起始 block 之后的连续 block，直到遇到正文 |
| 图内标签被截断 | 图右侧的方法名/公式标注不完整 | x 范围不能仅用列宽，必须检查图区域内所有 text span 的实际 x1，取 max 后外扩 5pt |

### 工具箱

| 工具 | 用途 | 适用场景 | Python包 |
|------|------|----------|---------|
| **Read工具** | Claude原生PDF读取 | 所有PDF（必选） | 内置 |
| **PyMuPDF** | 高精度文字提取 | 所有PDF（必选） | `fitz` |
| **pdf2image + VLM** | 转图片后视觉理解 | 含图表/公式/架构图的页面（必选） | `pdf2image` |
| **pdfplumber** | 表格提取 | Word/排版工具生成的PDF（含线框表格） | `pdfplumber` |
| **camelot** | 专业表格提取 | 同上，与pdfplumber互补 | `camelot` |
| **marker-pdf** | ML全能转换 | 所有PDF（可选，有模型时启用） | `marker` |
| **Surya** | 布局检测（Figure精确定位） | 所有PDF（图片提取优先方案） | `surya-ocr` |

### Step 0：PDF 类型判断与工具选择

用 PyMuPDF 快速扫描前几页，判断 PDF 类型：

```python
# ~/py312/bin/python
import fitz
doc = fitz.open("path/to/paper.pdf")
page = doc[0]
text = page.get_text("text")
# 检查特征：LaTeX标记（如 arXiv ID、\begin）、字体嵌入、表格线框
```

**判断规则**：
- **LaTeX学术论文**（arXiv等）→ 核心三件套：Read + PyMuPDF + pdf2image。跳过 pdfplumber/camelot（LaTeX表格无线框，提取率接近0%）
- **Word/排版工具生成的PDF** → 全工具：在核心三件套基础上启用 pdfplumber + camelot（表格有线框，提取效果好）
- **扫描件/图片PDF** → Read（可能失败）+ pdf2image（全页转图，视觉理解为主）+ marker-pdf（OCR能力）

**marker-pdf**：所有类型均可启用，但作为补充而非必选。若 marker 模型未下载或执行失败，跳过不阻塞。

### 提取流程

#### Step 1：Read工具直读（必选）
- 使用Read工具读取PDF全文（大型PDF分批，每次≤20页）
- 记录为 **基准文本 A**

#### Step 2：PyMuPDF 文字提取（必选）
- 运行Python脚本提取文字和结构：
```python
# ~/py312/bin/python
import fitz
doc = fitz.open("path/to/paper.pdf")
for page in doc:
    text = page.get_text("text")
    blocks = page.get_text("dict")  # 带位置和字体信息
```
- 记录为 **文本 B**
- 将PyMuPDF全文保存到 `/tmp/paper_pymupdf_text.txt`，后续作为精读参考源（避免反复调用工具）

#### Step 3：关键页面转图片 + 视觉理解（必选）
- 识别包含重要图表、公式推导、架构图的页面
- **注意**：运行前需确保 poppler 在 PATH 中：
```bash
export PATH="/opt/homebrew/bin:$PATH"  # macOS Homebrew
~/py312/bin/python -c "
from pdf2image import convert_from_path
images = convert_from_path('path/to/paper.pdf', dpi=200, first_page=N, last_page=M)
for i, img in enumerate(images):
    img.save(f'/tmp/paper_page_{i}.png')
"
```
- 用Read工具读取图片，视觉理解图表、公式、架构图
- 记录为 **视觉理解 E**

##### 图片保留到笔记
- **优先方案：Surya 布局检测（Figure + Caption 精确组合）**。Surya 同时输出 Figure/Picture 和 Caption 两种标签，将 Figure 区域与其紧邻的 Caption 精确组合，排除 caption 下方的正文：
```python
# ~/py312/bin/python
import fitz, os, base64
from surya.layout import LayoutPredictor
from PIL import Image

# 初始化模型（首次运行自动下载约1GB模型）
# surya-ocr >= 0.17: 需要先创建 FoundationPredictor
from surya.foundation import FoundationPredictor
foundation = FoundationPredictor(device="mps")  # macOS用mps，Linux用cuda
layout_predictor = LayoutPredictor(foundation)

doc = fitz.open("path/to/paper.pdf")
output_dir = "papers/images/{paper_id}"
os.makedirs(output_dir, exist_ok=True)

fig_count = 0
for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=144)
    page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    layout_result = layout_predictor([page_img])
    page_layout = layout_result[0]

    # 分离 Figure/Picture 和 Caption 区域
    figures = [b for b in page_layout.bboxes if b.label in ("Figure", "Picture")]
    captions = [b for b in page_layout.bboxes if b.label == "Caption"]

    for fig_box in figures:
        fig_count += 1
        fx0, fy0, fx1, fy1 = fig_box.bbox  # 图片区域（像素坐标，144dpi）

        # 找到与此 Figure 关联的 Caption（紧邻下方或上方，x 重叠）
        best_caption = None
        min_dist = float('inf')
        for cap in captions:
            cx0, cy0, cx1, cy1 = cap.bbox
            # Caption 应与 Figure 有 x 轴重叠
            x_overlap = min(fx1, cx1) - max(fx0, cx0)
            if x_overlap < (fx1 - fx0) * 0.3:
                continue
            # Caption 在 Figure 下方（最常见）或上方
            if cy0 >= fy1 - 5:  # caption 在下方
                dist = cy0 - fy1
            elif cy1 <= fy0 + 5:  # caption 在上方
                dist = fy0 - cy1
            else:
                dist = 0  # caption 与 figure 重叠
            if dist < min_dist and dist < 100:  # 100px 容忍阈值
                min_dist = dist
                best_caption = cap

        # 裁剪区域 = Figure + Caption 的 union（不多不少）
        if best_caption:
            cx0, cy0, cx1, cy1 = best_caption.bbox
            crop_x0 = min(fx0, cx0)
            crop_y0 = min(fy0, cy0)
            crop_x1 = max(fx1, cx1)
            crop_y1 = max(fy1, cy1)
        else:
            # 没找到 caption，仅裁剪 figure 本身
            crop_x0, crop_y0, crop_x1, crop_y1 = fx0, fy0, fx1, fy1

        # 转换为 PDF 点坐标并高清渲染
        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height
        clip = fitz.Rect(
            crop_x0 * scale_x, crop_y0 * scale_y,
            crop_x1 * scale_x, crop_y1 * scale_y
        )
        hires_pix = page.get_pixmap(clip=clip, dpi=150)
        hires_pix.save(f"{output_dir}/fig_{fig_count}.png")
```
- **退回方案A：PyMuPDF Caption定位 + 列边界检测 + 多源区域融合**。当 Surya 不可用时，采用以下经过验证的精确裁剪方法：

**核心思路**：先检测页眉位置（排除裁剪区域），再定位所有 Figure caption 的精确位置，根据 caption 推断所在列的边界，最后在该列内通过嵌入图片/矢量图/文本间隙三种方式确定 figure 的上边界。

```python
# ~/py312/bin/python
import fitz, os, re

doc = fitz.open("path/to/paper.pdf")
output_dir = "papers/images/{paper_id}"
os.makedirs(output_dir, exist_ok=True)

# 0. 检测页眉（running header）位置，确定裁剪安全起点
# 学术论文通常有页眉（论文标题或章节名）+ 下划线，位于页面顶部
def detect_header_bottom(doc, sample_pages=3):
    """检测页眉底部y坐标，返回裁剪的安全起点。"""
    header_bottom = 0
    for page_num in range(min(sample_pages, len(doc))):
        page = doc[page_num]
        # 方法1: 查找页面顶部的横线（页眉下划线）
        drawings = page.get_drawings()
        for d in drawings:
            if d['rect'].y0 < 80 and d['rect'].width > page.rect.width * 0.6:
                header_bottom = max(header_bottom, d['rect'].y1)
        # 方法2: 查找顶部小字体文本块（通常是页眉文字）
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            if block["bbox"][1] < 70 and block["bbox"][3] < 80:
                # 检查是否是跨页面宽度的页眉文字
                if block["bbox"][2] - block["bbox"][0] > page.rect.width * 0.4:
                    header_bottom = max(header_bottom, block["bbox"][3])
    # 添加安全边距
    return header_bottom + 5 if header_bottom > 0 else 0

HEADER_BOTTOM = detect_header_bottom(doc)

# 1. 定位所有独立的 Figure caption（排除正文中的行内引用）
figure_captions = []
for page_num, page in enumerate(doc):
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" not in block:
            continue
        block_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                block_text += span["text"]
        # 匹配独立 caption（以"Figure N."开头，且文本足够长）
        m = re.match(r"^Figure\s+(\d+[a-z]?)\.\s*(.+)", block_text.strip())
        if m and len(block_text) > 15:
            figure_captions.append({
                "page": page_num,
                "fig_id": m.group(1),
                "bbox": block["bbox"],
                "text": block_text.strip()
            })

# 1.5. 检测论文是否为双栏布局
def is_two_column(doc, sample_pages=8):
    """检测论文是否为双栏布局。
    采用两级检测：block 级 + line 级，采样更多页面以避免前几页全宽内容干扰。
    对含大量数学定义的论文（如 ICLR 格式），前几页可能全是全宽公式，
    需要看更多页才能发现双栏正文。"""
    pw = doc[0].rect.width
    mid_x = pw / 2
    left_blocks = 0
    right_blocks = 0
    left_lines = 0
    right_lines = 0
    for page_num in range(min(sample_pages, len(doc))):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            bx0, bx1 = block["bbox"][0], block["bbox"][2]
            block_width = bx1 - bx0
            # Block 级检测（原逻辑）
            if block_width < pw * 0.55 and block_width > pw * 0.15:
                block_center = (bx0 + bx1) / 2
                if block_center < mid_x - 10:
                    left_blocks += 1
                elif block_center > mid_x + 10:
                    right_blocks += 1
            # Line 级检测：即使 block 被合并为全宽，单行可能仅占半栏
            for line in block["lines"]:
                lx0 = line["bbox"][0]
                lx1 = line["bbox"][2]
                line_width = lx1 - lx0
                if line_width < pw * 0.48 and line_width > pw * 0.15:
                    line_center = (lx0 + lx1) / 2
                    if line_center < mid_x - 15:
                        left_lines += 1
                    elif line_center > mid_x + 15:
                        right_lines += 1
    # 双栏布局：block 级或 line 级任一满足条件即可
    block_two_col = left_blocks > 5 and right_blocks > 5
    line_two_col = left_lines > 10 and right_lines > 10
    return block_two_col or line_two_col

TWO_COLUMN = is_two_column(doc)

# 2. 对每个 caption，确定其所在列的 x 边界
def get_column_bounds(page, caption_bbox):
    """根据 caption 位置判断所在列（两栏布局）或全宽。
    即使 is_two_column 判断为单栏，也会检查 caption 是否明确在半页内。
    这防止含大量全宽公式/定义的论文被误判为单栏后裁入相邻列正文。"""
    pw = page.rect.width
    mid_x = pw / 2
    cap_left, cap_right = caption_bbox[0], caption_bbox[2]
    cap_width = cap_right - cap_left
    cap_center = (cap_left + cap_right) / 2

    # 全宽 figure（caption 跨越页面 60% 以上宽度）
    if cap_width > pw * 0.6:
        return 30, pw - 30

    if TWO_COLUMN:
        # 双栏论文：判断在左栏还是右栏
        if cap_center < mid_x:
            return 30, mid_x - 10   # 左栏
        else:
            return mid_x + 10, pw - 30  # 右栏

    # 即使判定为单栏，若 caption 右边界 < mid_x（明确偏左半页），
    # 且同页存在右侧独立文本块，则视为实际双栏，限制右边界
    if cap_right < mid_x - 20:
        # 检查同页是否存在右半侧的独立文本块
        blocks = page.get_text("dict")["blocks"]
        right_text_exists = False
        for block in blocks:
            if "lines" not in block:
                continue
            bx0 = block["bbox"][0]
            if bx0 > mid_x:
                right_text_exists = True
                break
        if right_text_exists:
            return 30, mid_x - 10  # 实际是左栏

    # 单栏论文：使用全页宽度
    return 30, pw - 30

# 3. 确定 figure 上边界（核心逻辑）
def find_figure_top(page, caption_bbox, col_left, col_right, upper_bound=None):
    """综合三种方法确定 figure 区域的上边界。
    upper_bound: 搜索的上界（同列中上方最近 figure caption 的底部，或 HEADER_BOTTOM）。
    返回值不得小于 upper_bound。"""
    if upper_bound is None:
        upper_bound = HEADER_BOTTOM
    caption_y_top = caption_bbox[1]
    candidate_rects = []

    # 方法1: 嵌入位图 (get_images + get_image_bbox)
    for img_info in page.get_images(full=True):
        try:
            img_bbox = page.get_image_bbox(img_info)
            if img_bbox and img_bbox.y1 <= caption_y_top + 5:
                # 必须在同一列范围内，且不在上界以上
                if (img_bbox.x0 >= col_left - 20 and img_bbox.x1 <= col_right + 20
                    and img_bbox.y0 >= upper_bound):
                    candidate_rects.append(img_bbox)
        except:
            continue

    # 方法2: 矢量图 (get_drawings + cluster_drawings)
    drawings = page.get_drawings()
    if drawings:
        try:
            figure_rects = page.cluster_drawings(
                drawings=drawings, x_tolerance=5, y_tolerance=5
            )
            for r in figure_rects:
                if r.y1 <= caption_y_top + 5 and r.height > 30:
                    if (r.x0 >= col_left - 20 and r.x1 <= col_right + 20
                        and r.y0 >= upper_bound):
                        candidate_rects.append(r)
        except:
            pass

    # 从候选区域中确定上边界
    if candidate_rects:
        close_rects = [r for r in candidate_rects if r.y0 < caption_y_top]
        if close_rects:
            top = min(r.y0 for r in close_rects) - 5
            return max(top, upper_bound)

    # 方法3: 文本间隙推断（在同一列内找 caption 上方最近的正文块底部）
    blocks = page.get_text("dict")["blocks"]
    text_above = []
    for block in blocks:
        if "lines" in block and block["bbox"][3] < caption_y_top - 10:
            if block["bbox"][1] < upper_bound:
                continue  # 跳过上界以上的文本
            bx = (block["bbox"][0] + block["bbox"][2]) / 2
            if col_left - 10 <= bx <= col_right + 10:
                text_above.append(block["bbox"])
    if text_above:
        nearest = max(text_above, key=lambda b: b[3])
        return nearest[3] + 2

    return max(upper_bound, caption_y_top - 200)  # 最终退回

# 4. 验证列边界（基于图形内容实际 x 范围）
def validate_column_bounds(page, col_left, col_right, caption_bbox, upper_bound):
    """用 drawings/images 的实际 x 范围验证并修正列边界。
    防止 caption 在某列但图形内容宽度不同（如窄 caption 被误判为全宽）。"""
    caption_y_top = caption_bbox[1]
    pw = page.rect.width
    mid_x = pw / 2
    graphic_x_ranges = []

    # 收集 caption 上方同列区域内的所有图形元素 x 范围
    for img_info in page.get_images(full=True):
        try:
            bbox = page.get_image_bbox(img_info)
            if bbox and bbox.y0 >= upper_bound and bbox.y1 <= caption_y_top + 5:
                if bbox.x0 >= col_left - 30 and bbox.x1 <= col_right + 30:
                    graphic_x_ranges.append((bbox.x0, bbox.x1))
        except:
            continue

    drawings = page.get_drawings()
    if drawings:
        try:
            clusters = page.cluster_drawings(drawings=drawings, x_tolerance=5, y_tolerance=5)
            for r in clusters:
                if r.y0 >= upper_bound and r.y1 <= caption_y_top + 5 and r.height > 30:
                    if r.x0 >= col_left - 30 and r.x1 <= col_right + 30:
                        graphic_x_ranges.append((r.x0, r.x1))
        except:
            pass

    if not graphic_x_ranges:
        return col_left, col_right  # 无图形元素，保持原边界

    # 检查图形内容是否仅在一栏内（双栏论文）
    gx_min = min(x[0] for x in graphic_x_ranges)
    gx_max = max(x[1] for x in graphic_x_ranges)

    if TWO_COLUMN and (col_right - col_left) > pw * 0.55:
        # 当前设为全宽，但检查图形是否实际仅在一栏
        if gx_max < mid_x + 10:
            return 30, mid_x - 10  # 图形仅在左栏
        elif gx_min > mid_x - 10:
            return mid_x + 10, pw - 30  # 图形仅在右栏

    return col_left, col_right

# 5. 跨页 figure 内容检测
def find_figure_page(doc, fi, col_left, col_right, upper_bound):
    """验证 figure 内容是否在 caption 所在页，若无则检查前一页。
    返回 (page, upper_bound) 元组。"""
    page = doc[fi["page"]]
    caption_y_top = fi["bbox"][1]
    # 检查 caption 所在页是否有对应图形元素
    has_graphics = False
    for img_info in page.get_images(full=True):
        try:
            bbox = page.get_image_bbox(img_info)
            if bbox and bbox.y1 <= caption_y_top + 5 and bbox.y0 >= upper_bound:
                if bbox.x0 >= col_left - 20 and bbox.x1 <= col_right + 20:
                    has_graphics = True
                    break
        except:
            continue
    if not has_graphics:
        drawings = page.get_drawings()
        if drawings:
            try:
                clusters = page.cluster_drawings(drawings=drawings, x_tolerance=5, y_tolerance=5)
                for r in clusters:
                    if r.y1 <= caption_y_top + 5 and r.y0 >= upper_bound and r.height > 30:
                        if r.x0 >= col_left - 20 and r.x1 <= col_right + 20:
                            has_graphics = True
                            break
            except:
                pass

    if not has_graphics and fi["page"] > 0:
        # Caption 所在页无图形内容 → 检查前一页同列底部
        prev_page = doc[fi["page"] - 1]
        prev_ph = prev_page.rect.height
        # 在前一页下半部分同列区域搜索图形
        for img_info in prev_page.get_images(full=True):
            try:
                bbox = prev_page.get_image_bbox(img_info)
                if bbox and bbox.y0 > prev_ph * 0.3:
                    if bbox.x0 >= col_left - 20 and bbox.x1 <= col_right + 20:
                        return prev_page, HEADER_BOTTOM
            except:
                continue
        drawings = prev_page.get_drawings()
        if drawings:
            try:
                clusters = prev_page.cluster_drawings(drawings=drawings, x_tolerance=5, y_tolerance=5)
                for r in clusters:
                    if r.y0 > prev_ph * 0.3 and r.height > 30:
                        if r.x0 >= col_left - 20 and r.x1 <= col_right + 20:
                            return prev_page, HEADER_BOTTOM
            except:
                pass

    return page, upper_bound  # 默认：figure 在 caption 同页

# 6. 预处理 caption 列表，计算同列中上方 caption 的 upper_bound
def compute_upper_bounds(figure_captions, doc):
    """为每个 figure 计算 upper_bound：同页同列中上方最近 caption 的底部 y。"""
    mid_x = doc[0].rect.width / 2
    # 按 (page, col) 分组并按 y 排序
    groups = {}
    for fi in figure_captions:
        col_id = "left" if (fi["bbox"][0] + fi["bbox"][2]) / 2 < mid_x else "right"
        key = (fi["page"], col_id)
        groups.setdefault(key, []).append(fi)
    for key in groups:
        groups[key].sort(key=lambda x: x["bbox"][1])

    upper_bounds = {}
    for key, caps in groups.items():
        for i, fi in enumerate(caps):
            if i == 0:
                upper_bounds[id(fi)] = HEADER_BOTTOM
            else:
                # 上方最近 caption 的底部 y 作为当前 figure 的搜索上界
                upper_bounds[id(fi)] = caps[i - 1]["bbox"][3] + 2
    return upper_bounds

# 7. 主提取循环
upper_bounds = compute_upper_bounds(figure_captions, doc)

for fi in figure_captions:
    upper_bound = upper_bounds.get(id(fi), HEADER_BOTTOM)
    col_left, col_right = get_column_bounds(doc[fi["page"]], fi["bbox"])

    # 跨页检测：验证 figure 内容是否在 caption 所在页
    page, upper_bound = find_figure_page(doc, fi, col_left, col_right, upper_bound)

    # 列边界验证：基于图形内容实际 x 范围修正
    col_left, col_right = validate_column_bounds(
        page, col_left, col_right, fi["bbox"], upper_bound
    )

    # 确定上边界
    top_y = find_figure_top(page, fi["bbox"], col_left, col_right, upper_bound)

    clip = fitz.Rect(col_left, top_y, col_right, fi["bbox"][3] + 3)
    hires_pix = page.get_pixmap(clip=clip, dpi=150)
    hires_pix.save(f"{output_dir}/fig_{fi['fig_id']}.png")

doc.close()
```

##### Programmatic Sanity Check（提取后立即执行，不可跳过）

**核心理念**：在视觉验证之前，先用纯坐标/尺寸逻辑自动发现明显错误并修正。这是 closed-loop 的关键一环——不依赖人眼，用确定性规则捕获常见问题。

```python
# ~/py312/bin/python
# 在主提取循环之后立即运行
import fitz, os

doc = fitz.open("path/to/paper.pdf")
output_dir = "papers/images/{paper_id}"
pw = doc[0].rect.width
mid_x = pw / 2

issues = []  # 收集所有发现的问题

for fi in figure_captions:
    fig_id = fi["fig_id"]
    fig_path = f"{output_dir}/fig_{fig_id}.png"
    if not os.path.exists(fig_path):
        issues.append(f"Fig {fig_id}: 文件不存在")
        continue

    cap_bbox = fi["bbox"]
    cap_width = cap_bbox[2] - cap_bbox[0]
    cap_center = (cap_bbox[0] + cap_bbox[2]) / 2
    page = doc[fi["page"]]

    # 读取实际图片尺寸
    from PIL import Image
    img = Image.open(fig_path)
    img_w, img_h = img.width, img.height

    # === Check 1: 宽度异常（裁入相邻列）===
    # 将图片像素宽度换算回 PDF 点坐标宽度
    # dpi=150 时，1pt = 150/72 ≈ 2.083 px
    scale = 150 / 72
    clip_width_pt = img_w / scale

    # 如果 caption 明确在半页内，但截取宽度超过了页面一半，说明裁入了相邻列
    if cap_center < mid_x - 20 and clip_width_pt > mid_x:
        issues.append(f"Fig {fig_id}: ⚠️ 宽度异常！caption在左栏(center={cap_center:.0f})但截取宽度={clip_width_pt:.0f}pt > mid_x={mid_x:.0f}。可能裁入右栏。")
    elif cap_center > mid_x + 20 and clip_width_pt > mid_x:
        issues.append(f"Fig {fig_id}: ⚠️ 宽度异常！caption在右栏(center={cap_center:.0f})但截取宽度={clip_width_pt:.0f}pt > mid_x={mid_x:.0f}。可能裁入左栏。")

    # === Check 2: 截取区域内是否包含相邻列的文本块 ===
    # 重建此图的 clip 区域
    col_left, col_right = get_column_bounds(page, cap_bbox)
    upper_bound = upper_bounds.get(id(fi), HEADER_BOTTOM)
    top_y = find_figure_top(page, cap_bbox, col_left, col_right, upper_bound)
    clip_rect = fitz.Rect(col_left, top_y, col_right, cap_bbox[3] + 3)

    # 检查 clip 区域内是否有明确属于另一栏的文本
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" not in block:
            continue
        bx0, by0, bx1, by1 = block["bbox"]
        # 文本块必须与 clip 在 y 方向上重叠
        if by1 < clip_rect.y0 or by0 > clip_rect.y1:
            continue
        # 检查文本块是否在 figure 内容同侧之外
        block_center = (bx0 + bx1) / 2
        block_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                block_text += span["text"]
        # 排除 figure 自身的标签文字（通常很短，< 30 字符）
        if len(block_text) < 30:
            continue
        # 如果 caption 在左栏但 clip 内包含右栏的长文本块
        if cap_center < mid_x and block_center > mid_x + 20:
            issues.append(f"Fig {fig_id}: ⚠️ clip 内含右栏文本: '{block_text[:40]}...'")
        elif cap_center > mid_x and block_center < mid_x - 20:
            issues.append(f"Fig {fig_id}: ⚠️ clip 内含左栏文本: '{block_text[:40]}...'")

    # === Check 3: 高度异常（可能包含多个 figure 或过多正文）===
    clip_height_pt = img_h / scale
    if clip_height_pt > page.rect.height * 0.7:
        issues.append(f"Fig {fig_id}: ⚠️ 高度异常！截取高度={clip_height_pt:.0f}pt 超过页面70%。可能包含多个figure或正文。")

    # === Check 4: 尺寸过小（可能截断或定位失败）===
    if img_w < 100 or img_h < 60:
        issues.append(f"Fig {fig_id}: ⚠️ 尺寸过小 ({img_w}x{img_h}px)。可能截断或定位失败。")

    # === Check 5: caption 与 clip 的 x 范围一致性 ===
    # caption 左边界不应在 clip 左边界之外（意味着 caption 本身被截断了）
    if cap_bbox[0] < clip_rect.x0 - 5:
        issues.append(f"Fig {fig_id}: ⚠️ caption左边界({cap_bbox[0]:.0f}) < clip左边界({clip_rect.x0:.0f})。caption可能被截断。")
    if cap_bbox[2] > clip_rect.x1 + 5:
        issues.append(f"Fig {fig_id}: ⚠️ caption右边界({cap_bbox[2]:.0f}) > clip右边界({clip_rect.x1:.0f})。caption可能被截断。")

# === 输出诊断结果并自动修正 ===
if issues:
    print("🔍 Sanity Check 发现以下问题：")
    for issue in issues:
        print(f"  {issue}")
    print("\n需要针对上述问题重新裁剪。")
else:
    print("✅ Sanity Check 全部通过，无明显坐标异常。")

doc.close()
```

**自动修正流程**（当 Sanity Check 发现问题时）：

| Check 失败 | 自动修正动作 |
|------------|-------------|
| Check 1/2: 裁入相邻列 | 强制 `col_right = mid_x - 10`（左栏）或 `col_left = mid_x + 10`（右栏），重新裁剪 |
| Check 3: 高度异常 | 检查 `upper_bound` 是否正确计算，重新定位同列上方最近的 caption/text block |
| Check 4: 尺寸过小 | 改用 pdf2image 整页截图作为退回 |
| Check 5: caption 截断 | 扩展 clip 的 x 范围至完整包含 caption bbox |

**关键原则**：Sanity Check 必须在视觉验证之前运行。它能捕获 80% 的常见错误（列边界错误、高度溢出），不需要人工介入。只有 Sanity Check 通过后，才进入视觉验证环节处理剩余的微妙问题（如标签被微量截断 5px 等）。
1. **页眉排除是第一步**：学术论文几乎都有 running header（论文标题/章节名 + 下划线），必须先检测页眉底部y坐标（`HEADER_BOTTOM`），所有figure裁剪的上边界不得超过此值。典型页眉高度约55-60pt。
2. **单栏/双栏检测是列边界的前提，但容易误判**：`is_two_column()` 需要看足够多页面（8页），并使用 block 级 + line 级双重检测。含大量全宽公式/定义的论文（如 ICLR 格式）前几页可能全是全宽内容，仅看 3 页会误判为单栏。即使最终判定为单栏，`get_column_bounds` 仍需后验检查：若 caption 右边界 < mid_x 且同页存在右侧独立文本块，则强制使用左栏边界。
3. **列边界检测是精确裁剪的基础（仅双栏论文）**：两栏论文中 figure 只应包含所在列的内容，避免裁入相邻列的正文
4. **Caption 必须是"独立 caption"**：正文中行内引用（如 "Figure 6(a) shows..."）会被误匹配，需通过文本长度和起始位置过滤
5. **同一列多图问题（关键！）**：当一列中有多个 figure 时，`find_figure_top` 的 `upper_bound` 参数必须设为同一列中上方最近 figure caption 的底部，防止搜索范围延伸到上方 figure 的区域。`compute_upper_bounds()` 函数自动为每个 figure 计算此约束
6. **Figure 内容可能与 caption 不在同一页**：`find_figure_page()` 会检测 caption 所在页面是否存在对应图形元素（drawings/images）。若 caption 上方没有任何图形元素，自动搜索前一页同列下半部分的图形内容
7. **列边界必须基于图形内容验证，不能仅看 caption 宽度**：`validate_column_bounds()` 用 drawings/images 的实际 x 范围修正 `get_column_bounds` 的初始判断。防止全宽 caption 误导致裁入相邻列正文，或窄 caption 被误判为半栏
8. **视觉验证+手动修正**：首次提取后，用 Read 工具逐一查看图片，发现截断时微调 clip 参数。常见问题：
   - 页眉被包含 → 检查 `HEADER_BOTTOM` 是否正确检测
   - 顶部标签截断 → 向上扩展 10-15pt（但不超过 `upper_bound`）
   - 缺少侧边标注文字 → 扩展列边界
   - 包含其他 figure 内容 → 以上方 figure 的 caption 底部作为当前 figure 的搜索起点
   - **截入了相邻列的正文** → 检查图形元素（drawings/images）的实际 x 范围，收窄到仅包含图形内容的列。**最常见根因**：`is_two_column()` 误判为单栏（含大量全宽公式/定义的论文前几页 right_blocks=0），导致 `get_column_bounds` 返回全页宽度。修复方法：检查 caption 是否明确在半页内（右边界 < mid_x），若是则强制使用栏边界
   - **截取的是纯正文而非图表** → figure 内容可能在前一页或后一页，需跨页搜索

- **退回方案B**：若上述方案仍有图被截断（通过视觉验证发现），对特定 figure 手动指定 clip 坐标修正，或改用整页截图并在笔记中标注页码

##### 多工具交叉截取与自动化验证（必做，不可跳过）

**核心理念**：用多种工具独立截取同一图/表，交叉比对结果差异，自动修正直到全部通过质量检查。

**Phase 1：多工具独立截取**

对同一论文，按以下优先级尝试多种截取方案，保留各方案的结果供比对：

| 方案 | 工具 | 输出 | 适用条件 |
|------|------|------|----------|
| A（主） | Surya 布局检测 | `fig_A_{id}.png` | Surya 可用时 |
| B（副） | PyMuPDF Caption定位 + 多源区域融合 | `fig_B_{id}.png` | 始终执行 |
| C（退回） | pdf2image 整页截图 | `page_{n}.png` | A、B 均失败时 |

当 A 和 B 都成功时，对每张图进行自动比对：
```python
# ~/py312/bin/python
from PIL import Image
import os

def compare_extractions(dir_a, dir_b, paper_id):
    """比对两种方案的截取结果，选择更优的。"""
    results = {}
    for fname in os.listdir(dir_a):
        if not fname.endswith('.png'):
            continue
        fig_id = fname.replace('fig_A_', '').replace('.png', '')
        path_a = os.path.join(dir_a, fname)
        path_b = os.path.join(dir_b, f"fig_B_{fig_id}.png")
        if not os.path.exists(path_b):
            results[fig_id] = {'winner': 'A', 'reason': 'B方案未提取到'}
            continue
        img_a = Image.open(path_a)
        img_b = Image.open(path_b)
        # 比对维度1：面积合理性（太大可能裁入多余内容，太小可能截断）
        area_a = img_a.width * img_a.height
        area_b = img_b.width * img_b.height
        # 比对维度2：宽高比差异（异常的宽高比通常意味着问题）
        ratio_a = img_a.width / img_a.height if img_a.height > 0 else 0
        ratio_b = img_b.width / img_b.height if img_b.height > 0 else 0
        results[fig_id] = {
            'size_a': (img_a.width, img_a.height),
            'size_b': (img_b.width, img_b.height),
            'area_ratio': area_a / area_b if area_b > 0 else float('inf')
        }
    return results
```

**选择规则**：
- 若 A、B 面积差异 < 15%，优先选 A（Surya 的 Figure 标签更精确）
- 若 A 明显大于 B（面积比 > 1.3），检查 A 是否裁入了多余内容 → 选 B
- 若 B 明显大于 A（面积比 < 0.7），检查 A 是否截断了内容 → 选 B
- 若任一方案尺寸异常（宽度 < 50px 或高度 < 30px），视为失败，选另一方案

**Phase 2：完备性检查（图例交叉验证）**

从正文中提取所有图表引用，与截取结果比对：
```python
# ~/py312/bin/python
import fitz, re

doc = fitz.open("path/to/paper.pdf")
# 提取所有 Figure/Table caption（独立出现的）
all_fig_ids = set()
all_tab_ids = set()
for page in doc:
    text = page.get_text("text")
    # 匹配独立 caption 行
    for m in re.finditer(r'^(Figure|Fig\.?)\s+(\d+[a-z]?)[.:]', text, re.MULTILINE):
        all_fig_ids.add(m.group(2))
    for m in re.finditer(r'^Table\s+(\d+)[.:]', text, re.MULTILINE):
        all_tab_ids.add(m.group(2))

# 对比提取的文件数量
extracted_figs = [f for f in os.listdir(output_dir) if f.startswith('fig_')]
extracted_tabs = [f for f in os.listdir(output_dir) if f.startswith('table_')]

missing_figs = all_fig_ids - {f.split('_')[1].split('.')[0] for f in extracted_figs}
missing_tabs = all_tab_ids - {f.split('_')[1].split('.')[0] for f in extracted_tabs}

if missing_figs:
    print(f"⚠️ 缺失 Figure: {sorted(missing_figs)}")
if missing_tabs:
    print(f"⚠️ 缺失 Table: {sorted(missing_tabs)}")
```

对缺失的图/表：定位其所在页面，用整页截图（pdf2image）作为退回方案补全。

**Phase 3：自动化 review 循环（MANDATORY — 不可跳过，即使时间紧迫也必须执行）**

**本阶段是区分"正确提取"和"盲猜提取"的关键**。跳过此步骤 = 50%+ 概率产出错误图片。

**重要执行顺序**：
1. 先运行上方的 **Programmatic Sanity Check** 脚本（纯坐标逻辑，零人工介入）
2. 修正 Sanity Check 发现的所有问题（自动修正，不需要视觉确认）
3. **然后必须进入下方的视觉 review 循环**——用 Read 工具逐一查看每张提取的图片

**为什么这步不可省略？**
- Sanity Check 能自动捕获 ~80% 的严重错误（裁入相邻列、高度溢出等）
- 剩余 ~20% 的问题（如 caption 续行被截断 5px、坐标轴标签微量截断）只有视觉验证才能发现
- **历史教训**：每次跳过视觉验证，用户都会反馈图片截取不准确，然后需要重做
- **闭环控制原理**：提取后 Read 回来 = 将人类反馈内化为自动流程，消除 open-loop 的系统性错误

```
REPEAT:
    pass_count = 0
    total_count = len(all_figures) + len(all_tables)

    FOR each extracted image:
        用 Read 工具查看图片
        执行 5 项自动检查：
            ☐ 顶部无页眉内容（无 running header 文字/横线）
            ☐ 图片内容完整（无标签/坐标轴/子图编号截断）
            ☐ 底部不超出 caption 区域
            ☐ 无相邻列文字混入
            ☐ 无其他 figure/table 的内容混入

        IF 全部通过:
            pass_count += 1
        ELSE:
            运行坐标诊断脚本（见下）
            根据诊断结果重新裁剪
            替换原图片文件

    IF pass_count == total_count:
        BREAK  // 全部通过，退出循环
    IF 已循环 3 次仍有未通过:
        对未通过的图片改用整页截图
        BREAK  // 兜底退出，避免无限循环
```

**坐标诊断脚本**（review 循环内使用）：
```python
# 诊断特定页面的元素分布，定位问题
page = doc[PAGE_NUM]
print(f"=== Page {PAGE_NUM} 元素分布 ===")
print(f"HEADER_BOTTOM = {HEADER_BOTTOM}")
# 文本块
for block in page.get_text("dict")["blocks"]:
    if "lines" in block:
        first_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                first_text += span["text"]
        print(f"TEXT y={block['bbox'][1]:.1f}-{block['bbox'][3]:.1f} x={block['bbox'][0]:.1f}-{block['bbox'][2]:.1f}: {first_text[:60]}")
# Drawing 元素
for d in page.get_drawings():
    if d['rect'].width > 20 and d['rect'].height > 5:  # 过滤微小元素
        print(f"DRAW y={d['rect'].y0:.1f}-{d['rect'].y1:.1f} x={d['rect'].x0:.1f}-{d['rect'].x1:.1f} w={d['rect'].width:.1f}")
# 嵌入图片
for img in page.get_images(full=True):
    try:
        bbox = page.get_image_bbox(img)
        print(f"IMG  y={bbox.y0:.1f}-{bbox.y1:.1f} x={bbox.x0:.1f}-{bbox.x1:.1f}")
    except:
        pass
```

**常见问题 → 自动修正映射**：
| 检查项失败 | 诊断依据 | 自动修正 |
|------------|----------|----------|
| 含页眉 | 图片顶部有小字体文字行或横线 | `top_y = max(top_y, HEADER_BOTTOM + 5)` |
| 顶部截断 | 诊断脚本显示 figure 上方有属于该图的元素 | `top_y -= 15`（向上扩展） |
| 底部超出 | 图片含 caption 下方的正文 | `bottom_y = caption_bbox[3] + 3` |
| 混入相邻列 | 图片宽度接近整页宽 | 重新计算列边界，使用更严格的 `col_right` |
| 多图粘连 | 图片中出现两个 caption | 以第二个 caption 的 y0 作为分割点 |
| 尺寸异常小 | 图片宽或高 < 100px | 改用整页截图裁剪 |

##### 图片尺寸与压缩策略
- **渲染DPI**：使用 150dpi，保证文字清晰可读
- **禁止有损压缩**：不使用 pngquant、PIL quantize 等颜色量化工具。直接保存 PyMuPDF 渲染的原始 PNG（`pixmap.save()` 输出即为最终文件）
- **允许 resize**：若图片像素尺寸过大，可通过 PIL `resize()` 等比缩放到合适尺寸，但不做颜色/画质压缩
- **保存方式**：`page.get_pixmap(clip=clip, dpi=150)` → `pix.save(output_path)` 即可，无需额外处理

##### 图片嵌入方式（自包含 Markdown）
- **默认使用 base64 嵌入**，使 Markdown 文件自包含，可直接复制到任何平台（Notion、飞书、语雀等）无需额外带图片文件：
```python
import base64
with open(f"{output_dir}/fig_{fig_num}.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
# 在 markdown 中使用：
# ![Figure 1: 描述](data:image/png;base64,{b64})
```
- 在笔记中的引用格式（左对齐，图片下方加粗标题）：
```markdown
<img src="data:image/png;base64,{base64_string}" alt="Figure X: 中文caption" />

**图 X：中文翻译的完整caption**
```
- **图/表标题翻译**：每张图片下方必须附加一行加粗的中文标题，翻译原文 caption 的完整内容（含变量说明和实验条件）。`alt` 属性保留中文翻译，图片正下方单独一行用 `**...**` 格式呈现完整中文标题
- 同时保留 `papers/images/{paper_id}/` 目录下的图片文件作为备份，方便单独查看或引用

##### 表格图片提取与嵌入（所有PDF类型）

论文中的 Table 也以图片形式提取并嵌入笔记（与 Figure 处理方式一致），保留原始排版格式。

**提取方法：PyMuPDF `find_tables()` + Caption 定位**

```python
# ~/py312/bin/python
import fitz, os, re, base64

doc = fitz.open("path/to/paper.pdf")
output_dir = "papers/images/{paper_id}"
os.makedirs(output_dir, exist_ok=True)

# 0. 检测页眉位置（与 Figure 提取共用同一逻辑）
def detect_header_bottom(doc, sample_pages=3):
    header_bottom = 0
    for page_num in range(min(sample_pages, len(doc))):
        page = doc[page_num]
        drawings = page.get_drawings()
        for d in drawings:
            if d['rect'].y0 < 80 and d['rect'].width > page.rect.width * 0.6:
                header_bottom = max(header_bottom, d['rect'].y1)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            if block["bbox"][1] < 70 and block["bbox"][3] < 80:
                if block["bbox"][2] - block["bbox"][0] > page.rect.width * 0.4:
                    header_bottom = max(header_bottom, block["bbox"][3])
    return header_bottom + 5 if header_bottom > 0 else 0

HEADER_BOTTOM = detect_header_bottom(doc)

# 遍历所有页面
for page_num in range(len(doc)):
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height

    # 1. 用 find_tables() 检测表格体的精确 bbox
    detected = page.find_tables()
    table_bboxes = [tab.bbox for tab in detected.tables]

    # 2. 用文本匹配定位 Table caption（支持多种格式）
    blocks = page.get_text('dict')['blocks']
    captions = []
    for block in blocks:
        if 'lines' not in block:
            continue
        block_text = ''
        for line in block['lines']:
            for span in line['spans']:
                block_text += span['text']
        m = re.match(r'^Table\s+(\d+)[.:]\s*', block_text.strip())
        if m:
            captions.append({'id': m.group(1), 'bbox': block['bbox'], 'text': block_text.strip()[:80]})

    # 3. 将 caption 与最近的下方 table body 匹配
    for cap in captions:
        cap_bottom = cap['bbox'][3]
        cap_top = cap['bbox'][1]
        cap_cx = (cap['bbox'][0] + cap['bbox'][2]) / 2
        best_body, best_dist = None, float('inf')

        for tb in table_bboxes:
            tb_cx = (tb[0] + tb[2]) / 2
            if abs(tb_cx - cap_cx) < pw * 0.3:  # 同列
                dist = tb[1] - cap_bottom
                if -5 <= dist < best_dist:  # 允许轻微重叠（-5pt）
                    best_dist = dist
                    best_body = tb

        if best_body:
            # clip = caption顶部 到 table body底部
            # 注意：find_tables() 的 bbox 可能不包含表格底部的rule线和带颜色背景的最后行
            # 因此需要向下额外扩展，同时确保不超过下一个正文 text block 的起始位置
            table_bottom = best_body[3] + 15  # 默认向下扩展15pt以包含底部rule和最后行
            # 查找 table body 下方最近的正文 text block，避免裁入正文
            for block in blocks:
                if "lines" not in block:
                    continue
                if block["bbox"][1] > best_body[3] + 5:
                    # 找到下方最近的文本块
                    block_text = ""
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"]
                    # 跳过可能是表格注释/footnote的短文本（通常紧跟表格）
                    if len(block_text.strip()) > 50 and not block_text.strip().startswith("*"):
                        table_bottom = min(table_bottom, block["bbox"][1] - 3)
                        break
            clip = fitz.Rect(
                max(0, min(cap['bbox'][0], best_body[0]) - 5),
                max(HEADER_BOTTOM, cap['bbox'][1] - 3),
                min(pw, max(cap['bbox'][2], best_body[2]) + 5),
                min(ph, table_bottom)
            )
        else:
            # 退回方案：caption 与 body 在同一 block，或 find_tables 未检测到
            # 尝试找 caption 下方到下一个 text block 之间的区域
            found = False
            for tb in table_bboxes:
                tb_cx = (tb[0] + tb[2]) / 2
                # 放宽匹配：body 可能与 caption 部分重叠
                if abs(tb_cx - cap_cx) < pw * 0.3:
                    if tb[3] > cap_top:  # body 底部在 caption 上方以下
                        clip = fitz.Rect(
                            max(0, min(cap['bbox'][0], tb[0]) - 5),
                            max(HEADER_BOTTOM, min(cap_top, tb[1]) - 3),
                            min(pw, max(cap['bbox'][2], tb[2]) + 5),
                            min(ph, tb[3] + 5)
                        )
                        found = True
                        break
            if not found:
                continue  # 无法匹配，跳过

        hires_pix = page.get_pixmap(clip=clip, dpi=150)
        hires_pix.save(f"{output_dir}/table_{cap['id']}.png")

doc.close()
```

**关键设计决策**：
1. **`find_tables()` 提供参考性 body 边界但不完全可靠**：PyMuPDF >= 1.23.0 内置表格检测可自动识别行列结构，但其 bbox 底部边界常不包含最后一行的彩色背景和底部rule线。因此需要向下扩展 15pt 作为安全边距，同时用"下方最近正文 block"作为截止约束，避免裁入无关内容
2. **Caption 在表格上方**：学术论文的 Table caption 总在表格体上方（与 Figure caption 在下方相反），裁剪区域 = caption 顶部 → body 底部
3. **页眉排除**：与 Figure 提取一致，使用 `HEADER_BOTTOM` 防止裁入页眉内容
4. **放宽 caption-body 匹配容差**：允许 caption 底部与 body 顶部有 -5pt 到 0pt 的重叠（PyMuPDF 的 bbox 计算有时不完全分离）
5. **退回方案增强**：当 `dist < 0`（caption 与 body 重叠/在同一 block）时，用 `tb[3] > cap_top` 放宽条件，确保能匹配到正确的 body
6. **嵌入方式**：与 Figure 完全一致（原始 PNG + base64 嵌入），格式为：
```markdown
<img src="data:image/png;base64,{base64_string}" alt="Table X: 中文caption" />

**表 X：中文翻译的完整caption（含变量说明和实验条件）**
```

**表格的多工具交叉验证**：
- Table 提取同样纳入上述 Phase 2（完备性检查）和 Phase 3（自动化 review 循环）的统一流程
- Table 特有的检查项：caption 是否完整包含在裁剪区域内（Table caption 在上方）、表格底部是否被截断（末行数据被切掉）、跨页表格是否需要分段截取
- 若 `find_tables()` 未检测到某个 Table 但正文中有对应 caption，用 pdf2image 对该页整页截图并手动裁剪

**表格放置原则**：
- 与 Figure 相同，就近插入到笔记中引用该表格数据的段落附近
- 笔记中若已有对应的 markdown 格式表格（文字版），保留文字版（提供可搜索性），在其前方插入图片版（提供原始排版）
- 典型放置位置：Notation table → 方法概述章节；实验数据 table → 对应实验小节；模型配置 table → 实验设置章节

#### Step 4：pdfplumber 表格提取（仅 Word/排版PDF）
- 仅在 Step 0 判断为非LaTeX PDF时执行：
```python
# ~/py312/bin/python
import pdfplumber
pdf = pdfplumber.open("path/to/paper.pdf")
for page in pdf.pages:
    tables = page.extract_tables()
```
- 记录为 **表格集 C**

#### Step 5：camelot 表格精提取（仅 Word/排版PDF）
- 仅在 Step 4 有结果但不完整时执行：
```python
# ~/py312/bin/python
import camelot
tables = camelot.read_pdf("path/to/paper.pdf", pages="all", flavor="lattice")
if len(tables) == 0:
    tables = camelot.read_pdf("path/to/paper.pdf", pages="all", flavor="stream")
```
- 记录为 **表格集 D**

#### Step 6：marker-pdf 全能转换（可选）
- 使用 `marker_single` CLI 转为Markdown：
```bash
~/py312/bin/marker_single path/to/paper.pdf --output_dir /tmp/marker_output
```
- 读取输出的 Markdown 文件，记录为 **Markdown文本 F**
- 特别关注：marker自动还原的LaTeX公式和表格
- 注意：模型缓存在 `~/Library/Caches/datalab/models/`（macOS），首次运行需下载约3GB模型。若模型未下载或执行失败，跳过此步骤

### 信息融合优先级规则

提取完成后，按以下优先级规则融合（不需要逐cell程序化比对，按优先级采信即可）：

1. **图表和公式** → 视觉理解 E 优先级最高（最接近原始渲染）。文字提取 A/B/F 作为补充
2. **正文文本** → PyMuPDF文本 B 为主（结构最完整），Read文本 A 和 marker文本 F 补充遗漏段落
3. **表格数据** → 若有 pdfplumber/camelot 结果（C/D），以提取精度更高的为准；若无，从文字提取中手工解析或以视觉理解 E 为准
4. **遇到分歧** → 以视觉理解 E 为最终裁判（回源原始PDF图像）
5. **信息补充** → 任何工具独有的非冗余信息，只要不与其他源矛盾，均纳入信息全集

### Context 预算控制

多工具提取会产生大量中间文本，需控制规模防止 context 溢出：

- PyMuPDF 全文保存到 `/tmp/paper_pymupdf_text.txt`，按需分段读取，**不要**一次性全量灌入对话
- pdf2image 仅转换关键页面（含图表/公式/架构图），通常不超过 10 页
- marker 输出保存到 `/tmp/marker_output/`，仅在需要核对公式/表格时按需读取
- 进入精读阶段前，清理中间变量，仅保留融合后的 **信息全集** 摘要（关键数据点、公式、图表语义），而非全部原始提取文本

### 注意事项
- 如果某个工具执行失败，跳过该工具继续，不阻塞整体流程
- 临时文件统一放在 `/tmp/` 下，不污染项目目录。**笔记生成完成后，清理本次产生的临时文件**：
```bash
rm -f /tmp/paper_pymupdf_text.txt /tmp/paper_page_*.png
rm -rf /tmp/marker_output/
```
- 提取的论文图片保存到 `papers/images/{paper_id}/`，与笔记文件配套
- 所有代码示例中的 `path/to/paper.pdf` 应替换为实际PDF路径
