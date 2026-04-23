#!/usr/bin/env python3
"""
KU 文档 JSON -> Markdown 转换器（可复制同步版本）。

设计目标:
1. 作为独立脚本文件，便于在不同 Skill 之间直接复制更新
2. 尽量覆盖常见 block type，避免内容静默丢失
3. 对未知结构提供兜底文本提取
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote


class KuJsonToMarkdown:
    """知识库文档 JSON 转 Markdown 转换器"""

    def __init__(self, source_path: Optional[str] = None):
        self.lines: List[str] = []
        self.source_path = source_path
        self.image_urls: List[str] = []

    def convert(self, raw: Any, add_title: bool = True) -> str:
        """将 JSON 转为 Markdown"""
        content, title = self._extract_content_and_title(raw)
        if add_title and title:
            self.lines.append(f"# {title}")
            self.lines.append("")
        self._render_blocks(content)
        return self._cleanup("\n".join(self.lines))

    def _extract_content_and_title(self, raw: Any) -> Tuple[List[Any], Optional[str]]:
        title: Optional[str] = None
        content: Any = raw

        if isinstance(raw, dict):
            result = raw.get("result")
            if isinstance(result, dict):
                content = result.get("content", [])
                doc_info = result.get("docInfo", {})
                if isinstance(doc_info, dict):
                    title = doc_info.get("title") or title
                title = result.get("title") or title
            elif "content" in raw:
                content = raw.get("content", [])

        if isinstance(content, dict):
            content = [content]
        if not isinstance(content, list):
            raise ValueError("Unsupported JSON format: content should be list/dict")
        return content, title

    def _render_blocks(self, blocks: List[Any]) -> None:
        for block in blocks:
            self._render_block(block)

    def _render_block(self, block: Any) -> None:
        if not isinstance(block, dict):
            return

        btype = block.get("type")

        if btype == "title":
            text = self._inline_text(block.get("children", []))
            if text:
                self._add_line(f"# {text}")
                self._add_blank()
            return

        if btype == "heading":
            level = int(block.get("level", 1) or 1)
            level = max(1, min(level, 6))
            order = (block.get("order") or "").strip()
            text = self._inline_text(block.get("children", []))
            if text:
                prefix = f"{order} " if order and not text.startswith(order) else ""
                self._add_line(f"{'#' * level} {prefix}{text}".rstrip())
                self._add_blank()
            return

        if btype == "paragraph":
            text = self._inline_text(block.get("children", []))
            if text:
                self._add_line(text)
                self._add_blank()
            return

        if btype == "ordered-list-item":
            depth = int(block.get("depth", 0) or 0)
            index = int(block.get("index", 1) or 1)
            text = self._inline_text(block.get("children", []))
            if text:
                indent = "  " * max(0, depth)
                marker = self._ordered_marker(depth, index)
                self._add_line(f"{indent}{marker} {text}")
            return

        if btype == "unordered-list-item":
            depth = int(block.get("depth", 0) or 0)
            text = self._inline_text(block.get("children", []))
            if text:
                indent = "  " * max(0, depth)
                self._add_line(f"{indent}- {text}")
            return

        if btype == "blockquote":
            quote_text = self._block_text(block.get("children", []))
            if quote_text:
                for line in quote_text.splitlines():
                    self._add_line(f"> {line}" if line else ">")
                self._add_blank()
            return

        if btype == "callout":
            quote_text = self._block_text(block.get("children", []))
            if quote_text:
                theme = (block.get("theme") or "").strip()
                label = {
                    "danger": "注意",
                    "warning": "注意",
                    "success": "提示",
                    "primary": "提示",
                }.get(theme, "提示")
                self._add_line(f"> **{label}**")
                for line in quote_text.splitlines():
                    self._add_line(f"> {line}" if line else ">")
                self._add_blank()
            return

        if btype == "image":
            src = (block.get("src") or "").strip()
            alt = self._inline_text(block.get("children", [])) or "image"
            if src:
                self.image_urls.append(src)
                self._add_line(f"![{alt}]({src})")
                self._add_blank()
            return

        if btype == "image-gallery":
            self._render_blocks(block.get("children", []))
            self._add_blank()
            return

        if btype == "table":
            self._render_table(block)
            self._add_blank()
            return

        if btype == "mention":
            mention = self._render_mention(block)
            if mention:
                self._add_line(mention)
                self._add_blank()
            return

        if btype == "diagram":
            diagram_id = (block.get("id") or "").strip()
            if diagram_id:
                self._add_line(f"> [流程图节点: {diagram_id}]")
                self._add_blank()
            return

        if btype == "block-code":
            language = (block.get("language") or "").strip()
            title = (block.get("title") or "").strip()
            lines = self._extract_code_lines(block.get("children", []))
            if title:
                self._add_line("```text")
                self._add_line(f"[{title}]")
                self._add_line("```")
            self._add_line(f"```{language}")
            for line in lines:
                self._add_line(line)
            self._add_line("```")
            self._add_blank()
            return

        if btype == "embed":
            embed_content = self._load_embed_content(block)
            if embed_content:
                self._add_line("```markdown")
                for line in embed_content.rstrip("\n").splitlines():
                    self._add_line(line)
                self._add_line("```")
            else:
                block_id = (block.get("blockId") or "").strip()
                if block_id:
                    self._add_line(f"> [嵌入内容: {block_id}]")
                else:
                    self._add_line("> [嵌入内容]")
            self._add_blank()
            return

        children = block.get("children")
        if isinstance(children, list):
            self._render_blocks(children)
            return

        fallback = self._fallback_text(block)
        if fallback:
            self._add_line(fallback)
            self._add_blank()

    def _render_mention(self, node: Dict[str, Any]) -> str:
        name = (node.get("mentionName") or "").strip() or "mention"
        token = (node.get("mentionToken") or "").strip()
        if token.startswith("zsk$$"):
            url = unquote(token.replace("zsk$$", "", 1))
            return f"[{name}]({url})"
        return name

    def _inline_text(self, children: Any, block_mode: bool = False) -> str:
        if isinstance(children, str):
            return children.strip()
        if isinstance(children, dict):
            return self._inline_text([children])
        if not isinstance(children, list):
            return ""

        parts: List[str] = []
        for child in children:
            ctype = child.get("type") if isinstance(child, dict) else None
            rendered = self._inline_node(child)
            if not rendered:
                continue
            is_image = isinstance(child, dict) and child.get("type") == "image"
            is_block = ctype in {
                "paragraph",
                "heading",
                "ordered-list-item",
                "unordered-list-item",
                "blockquote",
                "table",
                "image",
                "block-code",
            }
            if parts and (is_image or (block_mode and is_block)):
                parts.append("\n")
            parts.append(rendered)

        text = "".join(parts)
        return text.replace("\u00a0", " ").strip()

    def _inline_node(self, node: Any) -> str:
        if isinstance(node, str):
            return node
        if not isinstance(node, dict):
            return ""

        ntype = node.get("type")
        if ntype == "mention":
            return self._render_mention(node)
        if ntype == "link":
            href = (node.get("href") or "").strip()
            text = self._inline_text(node.get("children", [])) or href
            return f"[{text}]({href})" if href else text
        if ntype == "image":
            src = (node.get("src") or "").strip()
            if not src:
                return ""
            self.image_urls.append(src)
            alt = self._inline_text(node.get("children", [])) or "image"
            return f"![{alt}]({src})"
        if ntype == "ordered-list-item":
            depth = int(node.get("depth", 0) or 0)
            index = int(node.get("index", 1) or 1)
            text = self._inline_text(node.get("children", []), block_mode=True).strip()
            if not text:
                return ""
            marker = self._ordered_marker(depth, index)
            indent = "&nbsp;&nbsp;" * max(0, depth)
            return f"{indent}{marker} {text}"
        if ntype == "unordered-list-item":
            depth = int(node.get("depth", 0) or 0)
            text = self._inline_text(node.get("children", []), block_mode=True).strip()
            if not text:
                return ""
            indent = "&nbsp;&nbsp;" * max(0, depth)
            return f"{indent}- {text}"
        if ntype == "block-code-line":
            return self._plain_text(node.get("children", []))

        if "text" in node:
            return self._apply_marks(node, str(node.get("text", "")))

        children = node.get("children")
        if isinstance(children, list):
            return self._inline_text(children, block_mode=True)
        return ""

    def _apply_marks(self, leaf: Dict[str, Any], text: str) -> str:
        if not text:
            return ""
        out = text
        if leaf.get("bold"):
            out = f"**{out}**"
        if leaf.get("italic"):
            out = f"*{out}*"
        if leaf.get("code"):
            out = f"`{out}`"
        if leaf.get("strikethrough"):
            out = f"~~{out}~~"
        return out

    def _ordered_marker(self, depth: int, index: int) -> str:
        if depth % 2 == 1:
            idx = max(1, index)
            if idx <= 26:
                return f"{chr(ord('a') + idx - 1)}."
            return f"a{idx}."
        return f"{max(1, index)}."

    def _plain_text(self, children: Any) -> str:
        if isinstance(children, str):
            return children
        if isinstance(children, dict):
            if "text" in children:
                return str(children.get("text", ""))
            nested = children.get("children")
            if isinstance(nested, list):
                return self._plain_text(nested)
            return ""
        if not isinstance(children, list):
            return ""
        return "".join(self._plain_text(child) for child in children)

    def _extract_code_lines(self, children: Any) -> List[str]:
        lines: List[str] = []
        if not isinstance(children, list):
            return lines
        for child in children:
            if not isinstance(child, dict):
                continue
            ctype = child.get("type")
            if ctype == "block-code-line":
                lines.append(self._plain_text(child.get("children", [])))
            elif "text" in child:
                lines.append(str(child.get("text", "")))
            else:
                nested = child.get("children")
                if isinstance(nested, list):
                    text = self._plain_text(nested)
                    if text:
                        lines.append(text)
        return lines

    def _load_embed_content(self, block: Dict[str, Any]) -> str:
        block_id = (block.get("blockId") or "").strip()
        if not self.source_path or not block_id:
            return ""
        source = Path(self.source_path)
        if not source.exists():
            return ""

        candidates = [
            source.with_suffix("").as_posix() + f"_{block_id}.md",
            source.as_posix().replace(".wiki", "") + f"_{block_id}.md",
        ]
        for candidate in candidates:
            p = Path(candidate)
            if p.exists() and p.is_file():
                try:
                    return p.read_text(encoding="utf-8")
                except Exception:
                    continue
        return ""

    def _fallback_text(self, block: Dict[str, Any]) -> str:
        if "text" in block and str(block.get("text", "")).strip():
            return str(block.get("text", "")).strip()
        href = str(block.get("href", "")).strip()
        if href:
            title = str(block.get("title", "")).strip() or href
            return f"[{title}]({href})"
        src = str(block.get("src", "")).strip()
        if src:
            return f"![image]({src})"
        return self._plain_text(block.get("children", [])).strip()

    def _block_text(self, blocks: Any) -> str:
        if not isinstance(blocks, list):
            return ""
        temp = KuJsonToMarkdown(source_path=self.source_path)
        temp._render_blocks(blocks)
        return temp._cleanup("\n".join(temp.lines)).strip()

    def _render_table(self, table: Dict[str, Any]) -> None:
        rows = table.get("children", [])
        if not isinstance(rows, list) or not rows:
            return

        grid, has_span = self._build_table_grid(rows)
        if not grid:
            return

        if has_span:
            self._render_table_html(grid)
        else:
            self._render_table_markdown(grid)

    def _build_table_grid(self, rows: List[Any]) -> Tuple[List[List[Optional[Dict[str, Any]]]], bool]:
        grid: List[List[Optional[Dict[str, Any]]]] = []
        has_span = False
        for r_idx, row in enumerate(rows):
            while len(grid) <= r_idx:
                grid.append([])
            row_cells = row.get("children", []) if isinstance(row, dict) else []
            if not isinstance(row_cells, list):
                row_cells = []

            c_idx = 0
            for cell in row_cells:
                if not isinstance(cell, dict):
                    continue
                while c_idx < len(grid[r_idx]) and grid[r_idx][c_idx] is None:
                    c_idx += 1

                data = cell.get("data", {}) if isinstance(cell.get("data"), dict) else {}
                colspan = int(data.get("colspan", 1) or 1)
                rowspan = int(data.get("rowspan", 1) or 1)
                has_span = has_span or colspan > 1 or rowspan > 1

                text = self._inline_text(cell.get("children", []), block_mode=True)
                cell_obj = {"text": text, "colspan": max(1, colspan), "rowspan": max(1, rowspan)}
                self._set_cell(grid, r_idx, c_idx, cell_obj)

                for dc in range(1, cell_obj["colspan"]):
                    self._set_placeholder(grid, r_idx, c_idx + dc)

                for dr in range(1, cell_obj["rowspan"]):
                    for dc in range(cell_obj["colspan"]):
                        self._set_placeholder(grid, r_idx + dr, c_idx + dc)

                c_idx += cell_obj["colspan"]

        width = max((len(r) for r in grid), default=0)
        for row in grid:
            if len(row) < width:
                row.extend([{"text": "", "colspan": 1, "rowspan": 1}] * (width - len(row)))

        return grid, has_span

    def _set_cell(self, grid: List[List[Optional[Dict[str, Any]]]], r: int, c: int, cell: Dict[str, Any]) -> None:
        while len(grid) <= r:
            grid.append([])
        while len(grid[r]) <= c:
            grid[r].append({"text": "", "colspan": 1, "rowspan": 1})
        grid[r][c] = cell

    def _set_placeholder(self, grid: List[List[Optional[Dict[str, Any]]]], r: int, c: int) -> None:
        while len(grid) <= r:
            grid.append([])
        while len(grid[r]) <= c:
            grid[r].append({"text": "", "colspan": 1, "rowspan": 1})
        grid[r][c] = None

    def _render_table_markdown(self, grid: List[List[Optional[Dict[str, Any]]]]) -> None:
        def md_cell(cell: Optional[Dict[str, Any]]) -> str:
            if not cell:
                return ""
            return str(cell.get("text", "")).replace("|", "\\|").replace("\n", "<br>").strip()

        header = [md_cell(c) for c in grid[0]]
        self._add_line("| " + " | ".join(header) + " |")
        self._add_line("| " + " | ".join(["---"] * len(header)) + " |")
        for row in grid[1:]:
            vals = [md_cell(c) for c in row]
            self._add_line("| " + " | ".join(vals) + " |")

    def _render_table_html(self, grid: List[List[Optional[Dict[str, Any]]]]) -> None:
        self._add_line("<table>")
        self._add_line("  <tbody>")
        for r_idx, row in enumerate(grid):
            self._add_line("    <tr>")
            for cell in row:
                if cell is None:
                    continue
                text = html.escape(str(cell.get("text", "")).strip()).replace("\n", "<br>")
                tag = "th" if r_idx == 0 else "td"
                attrs = []
                colspan = int(cell.get("colspan", 1) or 1)
                rowspan = int(cell.get("rowspan", 1) or 1)
                if colspan > 1:
                    attrs.append(f'colspan="{colspan}"')
                if rowspan > 1:
                    attrs.append(f'rowspan="{rowspan}"')
                attr_str = (" " + " ".join(attrs)) if attrs else ""
                self._add_line(f"      <{tag}{attr_str}>{text}</{tag}>")
            self._add_line("    </tr>")
        self._add_line("  </tbody>")
        self._add_line("</table>")

    def _add_line(self, line: str) -> None:
        self.lines.append(line.rstrip())

    def _add_blank(self) -> None:
        if not self.lines or self.lines[-1] != "":
            self.lines.append("")

    def _cleanup(self, text: str) -> str:
        lines = text.splitlines()
        out: List[str] = []
        blank = False
        for line in lines:
            is_blank = not line.strip()
            if is_blank and blank:
                continue
            out.append(line.rstrip())
            blank = is_blank
        return "\n".join(out).strip() + "\n"
