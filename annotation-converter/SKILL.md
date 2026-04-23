---
name: annotation-converter
description: 皮肤病多模态标注数据 Excel → JSON 转换工具。必须在以下场景使用此skill：用户提到"标注数据转换"、"Excel转JSON"、"标注Excel"、"annotation Excel"、"皮肤标注导出"、"标注数据导出"、"多模态标注"中的任何关键词时；用户要把皮肤病标注Excel（含疾病词、皮损、颜色、部位等维度列）转为结构化JSON时；用户提到审核/评估平台的标注数据需要做格式转化时；用户上传了包含 talk_id、image_url、疾病词、皮肤损害 等列的 Excel 文件并要求转 JSON 时。即使用户只是问"帮我把标注Excel转成JSON"或"处理一下这个标注数据"也应触发。
---

# 皮肤病多模态标注数据 Excel → JSON 转换

## 功能

将皮肤病多模态标注 Excel 数据按列映射规则转换为结构化 JSON 格式，用于标注平台数据导入或下游模型训练。

## 列映射规则

脚本通过 `ANNOTATION_COLUMNS` 配置表定义 Excel 列名到 JSON `latitude_name` 的映射：

| Excel 列名 | JSON latitude_name |
|---|---|
| 疾病词1【多选】 | 疾病词1【多选】 |
| 疾病词2【多选】 | 疾病词2【多选】 |
| 疾病词3【多选】 | 疾病词3【多选】 |
| 皮肤损害 | 皮肤损害【多选】 |
| 最大皮损颜色 | 最大皮损颜色 |
| 最大皮损大小 | 最大皮损大小 |
| 皮损排列（多选） | 皮损排列（多选） |
| 皮损数量 | 皮损数量 |
| 皮损边缘 | 皮损边缘 |
| 皮损界限 | 皮损界限 |
| 表面湿度 | 表面湿度 |
| 鳞屑/痂 | 鳞屑/痂 |
| 年龄 | 年龄 |
| 部位 | 部位 |

> 所有维度均不输出 label 字段。

## 元数据字段

除标注维度外，脚本还会读取以下 Excel 列作为元数据，包裹为单元素数组：

- `talk_id` → `["xxx"]`
- `query` → `["xxx"]`
- `history` → `["xxx"]`
- `image_url` → `["xxx"]`
- `box_url` → `["xxx"]`
- `img_coordinates` → 解析为整数数组，如 `[4, 17, 584, 319]`

## 输出 JSON 格式

```json
[
  [
    {
      "talk_id": ["data_010426/images_45w/xxx.jpg"],
      "query": [""],
      "history": [""],
      "image_url": ["https://..."],
      "box_url": [""],
      "img_coordinates": [4, 17, 584, 319],
      "annotation_list": [
        {
          "latitude": {
            "latitude_name": "疾病词1【多选】",
            "tags_list": ["毛周角化病", "毛囊炎"]
          }
        },
        {
          "latitude": {
            "latitude_name": "皮肤损害【多选】",
            "tags_list": ["丘疹"]
          }
        }
      ]
    }
  ]
]
```

整体结构为 `[[record], [record], ...]`，每条记录包裹在单元素数组中。

## 使用方式

### CLI 用法

```bash
~/py312/bin/python3 scripts/excel_to_annotation_json.py input.xlsx output.json [--sheet 有效数据]
```

参数说明：
- `input.xlsx` — 输入 Excel 文件（必填）
- `output.json` — 输出 JSON 文件路径（必填）
- `--sheet` — 指定 Sheet 名称（默认优先选 "有效数据"，否则用 active sheet）

### Python 代码调用

```python
from scripts.excel_to_annotation_json import convert_excel_to_json, convert_row

convert_excel_to_json("input.xlsx", "output.json", sheet_name="有效数据")
```

## 核心函数

| 函数 | 用途 |
|---|---|
| `convert_excel_to_json(input, output, sheet)` | 主入口，Excel 文件整体转 JSON |
| `convert_row(row_dict)` → `dict` | 单行 dict 转为一条 JSON record |
| `build_annotation(value, name)` → `dict` | 构建单个 annotation 项 |
| `parse_tags(value)` → `list` | 逗号分隔字符串 → tags 数组 |
| `parse_coordinates(value)` → `list` | 坐标字符串 → 整数数组 |

## 自定义扩展

如需增减标注维度，修改脚本中的 `ANNOTATION_COLUMNS` 列表即可：

```python
ANNOTATION_COLUMNS = [
    ("Excel列名", "JSON中的latitude_name"),
    # 添加新维度...
]
```

## 依赖

- Python 3.8+
- openpyxl（`~/py312/bin/pip install openpyxl`）
