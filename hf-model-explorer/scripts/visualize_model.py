#!/usr/bin/env python3
"""HuggingFace 模型可视化 - 生成交互式 HTML 架构图"""

import argparse
import json
import sys
import os
import html as html_module

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from explore_model import (
    check_dependencies, load_config, load_model_meta,
    build_tree, build_synthetic_tree, format_params,
    extract_key_config, detect_moe, detect_mla,
    detect_quantization, detect_sub_configs,
    estimate_params_from_config
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{model_name} - 模型架构可视化</title>
<style>
  :root {{
    --bg-primary: #0d1117; --bg-secondary: #161b22; --bg-tertiary: #1c2128;
    --border: #30363d; --border-light: #21262d;
    --text-primary: #f0f6fc; --text-secondary: #c9d1d9; --text-muted: #8b949e;
    --blue: #58a6ff; --green: #3fb950; --yellow: #d29922; --orange: #f78166;
    --purple: #bc8cff; --red: #f85149; --cyan: #39d2c0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg-primary); color: var(--text-secondary); padding: 24px; line-height: 1.5; }}
  h1 {{ color: var(--blue); font-size: 1.6em; margin-bottom: 4px; }}
  .subtitle {{ color: var(--text-muted); margin-bottom: 16px; font-size: 0.9em; }}
  .badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
  .badge {{ padding: 4px 12px; border-radius: 16px; font-size: 0.82em; font-weight: 600; }}
  .badge-blue {{ background: #1f6feb33; color: var(--blue); }}
  .badge-green {{ background: #23883633; color: var(--green); }}
  .badge-orange {{ background: #f7816633; color: var(--orange); }}
  .badge-purple {{ background: #8957e533; color: var(--purple); }}
  .badge-cyan {{ background: #39d2c033; color: var(--cyan); }}
  {synthetic_banner_css}

  /* Stats cards */
  .stats {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .stat-card {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }}
  .stat-label {{ color: var(--text-muted); font-size: 0.78em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat-value {{ color: var(--text-primary); font-size: 1.4em; font-weight: 700; }}
  .stat-sub {{ color: var(--text-muted); font-size: 0.75em; margin-top: 2px; }}

  /* Config grid */
  .config-section {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
  .config-section h2 {{ color: var(--text-primary); font-size: 1em; margin-bottom: 12px; }}
  .config-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 6px; }}
  .config-item {{ display: flex; justify-content: space-between; padding: 5px 10px; border-radius: 4px; background: var(--bg-primary); }}
  .config-key {{ color: var(--text-muted); font-size: 0.82em; }}
  .config-val {{ color: var(--text-primary); font-weight: 600; font-size: 0.82em; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

  /* Parameter distribution bars */
  .bar-section {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
  .bar-section h2 {{ color: var(--text-primary); font-size: 1em; margin-bottom: 12px; }}
  .bar-row {{ margin-bottom: 8px; }}
  .bar-label {{ display: flex; justify-content: space-between; font-size: 0.82em; margin-bottom: 3px; }}
  .bar-label span:first-child {{ color: var(--text-secondary); }}
  .bar-label span:last-child {{ color: var(--orange); font-weight: 600; }}
  .bar-track {{ height: 16px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.4s ease; min-width: 2px; }}

  /* Tree structure - real tree with connector lines */
  .tree-section {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
  .tree-section h2 {{ color: var(--text-primary); font-size: 1em; margin-bottom: 16px; }}
  .tree {{ font-family: "SF Mono", Monaco, Consolas, "Liberation Mono", monospace; font-size: 0.82em; line-height: 1.8; }}
  .tree ul {{ list-style: none; padding-left: 0; }}
  .tree > ul {{ padding-left: 0; }}
  .tree li {{ position: relative; padding-left: 24px; }}
  .tree li::before {{
    content: ""; position: absolute; left: 6px; top: 0; bottom: 50%;
    border-left: 1px solid #30363d; border-bottom: 1px solid #30363d;
    width: 14px; height: 50%;
  }}
  .tree li::after {{
    content: ""; position: absolute; left: 6px; top: 50%; bottom: 0;
    border-left: 1px solid #30363d;
  }}
  .tree li:last-child::after {{ display: none; }}
  .tree > ul > li::before, .tree > ul > li::after {{ display: none; }}
  .tree > ul > li {{ padding-left: 0; }}

  .node-row {{ display: inline-flex; align-items: center; gap: 6px; padding: 2px 6px; border-radius: 4px; cursor: pointer; }}
  .node-row:hover {{ background: #1f2937; }}
  .node-icon {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .icon-attention {{ background: var(--blue); }}
  .icon-mlp {{ background: var(--green); }}
  .icon-moe {{ background: var(--orange); }}
  .icon-norm {{ background: var(--yellow); }}
  .icon-embed {{ background: var(--purple); }}
  .icon-conv {{ background: var(--red); }}
  .icon-default {{ background: #484f58; }}
  .node-name {{ color: var(--text-secondary); font-weight: 500; }}
  .node-type {{ font-size: 0.88em; padding: 1px 6px; border-radius: 3px; font-weight: 500; }}
  .type-attention {{ background: #1a3a5c; color: var(--blue); }}
  .type-mlp {{ background: #1a3c2a; color: var(--green); }}
  .type-moe {{ background: #3d2600; color: var(--orange); }}
  .type-norm {{ background: #3d2e00; color: var(--yellow); }}
  .type-embed {{ background: #2d1a4e; color: var(--purple); }}
  .type-conv {{ background: #3d1a1a; color: var(--red); }}
  .type-default {{ background: var(--border-light); color: var(--text-muted); }}
  .node-params {{ color: var(--text-muted); font-size: 0.85em; margin-left: 4px; }}
  .node-bar {{ display: inline-block; height: 6px; border-radius: 3px;
               background: linear-gradient(90deg, #238636, #2ea043); margin-left: 6px;
               min-width: 2px; vertical-align: middle; }}
  .toggle-btn {{ cursor: pointer; color: #484f58; font-size: 0.75em; user-select: none; margin-right: 2px; width: 14px; display: inline-block; text-align: center; }}
  .collapsed > ul {{ display: none; }}
  .tooltip {{ position: absolute; background: var(--bg-tertiary); border: 1px solid var(--border);
              border-radius: 6px; padding: 8px 12px; font-size: 0.78em; pointer-events: none;
              z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.5); display: none; max-width: 300px; }}
  .tooltip b {{ color: var(--text-primary); }}
  {synthetic_banner_style}
</style>
</head>
<body>

<h1>{model_name}</h1>
<div class="subtitle">{model_class} &mdash; HuggingFace Model Architecture Visualization</div>

{synthetic_banner}

<div class="badges">
  {badges}
</div>

<div class="stats">
  {stat_cards}
</div>

<div class="config-section">
  <h2>Configuration</h2>
  <div class="config-grid">
    {config_items}
  </div>
</div>

{bar_section}

<div class="tree-section">
  <h2>Architecture Tree {tree_note}</h2>
  <div class="tree">
    <ul>{tree_html}</ul>
  </div>
</div>

<div class="tooltip" id="tooltip"></div>

<script>
document.querySelectorAll('.toggle-btn').forEach(el => {{
  el.addEventListener('click', e => {{
    e.stopPropagation();
    const li = el.closest('li');
    li.classList.toggle('collapsed');
    el.textContent = li.classList.contains('collapsed') ? '\\u25b6' : '\\u25bc';
  }});
}});
const tooltip = document.getElementById('tooltip');
document.querySelectorAll('.node-row').forEach(el => {{
  el.addEventListener('mouseenter', e => {{
    const info = el.dataset.info;
    if (info) {{ tooltip.innerHTML = info; tooltip.style.display = 'block'; }}
  }});
  el.addEventListener('mousemove', e => {{
    tooltip.style.left = (e.pageX + 14) + 'px';
    tooltip.style.top = (e.pageY + 14) + 'px';
  }});
  el.addEventListener('mouseleave', () => {{ tooltip.style.display = 'none'; }});
}});
// Auto-collapse deep nodes
document.querySelectorAll('.tree li').forEach(li => {{
  const depth = li.dataset.depth;
  if (depth && parseInt(depth) >= 3) {{
    li.classList.add('collapsed');
    const btn = li.querySelector(':scope > .node-row .toggle-btn');
    if (btn) btn.textContent = '\\u25b6';
  }}
}});
</script>
</body>
</html>"""


def get_type_info(type_name):
    """根据模块类型返回 CSS 类名和图标类"""
    name_lower = type_name.lower()
    if any(k in name_lower for k in ["moe", "expert"]):
        return "type-moe", "icon-moe"
    if any(k in name_lower for k in ["attention", "attn", "sdpa", "mla", "mha", "gqa"]):
        return "type-attention", "icon-attention"
    if any(k in name_lower for k in ["mlp", "feedforward", "ffn", "gate", "swiglu", "densmlp"]):
        return "type-mlp", "icon-mlp"
    if any(k in name_lower for k in ["norm", "layernorm", "rmsnorm"]):
        return "type-norm", "icon-norm"
    if any(k in name_lower for k in ["embed", "embedding", "wte", "wpe"]):
        return "type-embed", "icon-embed"
    if any(k in name_lower for k in ["conv", "pool", "patch"]):
        return "type-conv", "icon-conv"
    return "type-default", "icon-default"


def tree_to_html(node, max_params, depth=0):
    """将树节点转为 HTML <li> 结构，使用真正的 ul/li 树形"""
    has_children = bool(node.get("children"))
    type_class, icon_class = get_type_info(node["type"])

    name_esc = html_module.escape(node["name"])
    type_esc = html_module.escape(node["type"])

    # Toggle button
    toggle = f'<span class="toggle-btn">&#x25bc;</span>' if has_children else '<span class="toggle-btn">&nbsp;</span>'

    # Parameter bar
    bar_html = ""
    params_html = ""
    if node["total_params"] > 0:
        bar_width = max(2, int(node["total_params"] / max_params * 180)) if max_params > 0 else 0
        bar_html = f'<span class="node-bar" style="width:{bar_width}px"></span>'
        params_html = f'<span class="node-params">{format_params(node["total_params"])}</span>'

    # Tooltip info
    info = (f"<b>{type_esc}</b><br>"
            f"Total params: {node['total_params']:,}<br>"
            f"Own params: {node['own_params']:,}")
    if node["total_params"] > 0 and max_params > 0:
        pct = node["total_params"] / max_params * 100
        info += f"<br>Percentage: {pct:.2f}%"
    info_esc = html_module.escape(info)

    html = f'<li data-depth="{depth}">'
    html += f'<span class="node-row" data-info="{info_esc}">'
    html += f'{toggle}<span class="node-icon {icon_class}"></span>'
    html += f'<span class="node-name">{name_esc}</span> '
    html += f'<span class="node-type {type_class}">{type_esc}</span>'
    html += f'{params_html}{bar_html}'
    html += '</span>'

    if has_children:
        html += '<ul>'
        for child in node["children"]:
            html += tree_to_html(child, max_params, depth + 1)
        html += '</ul>'

    html += '</li>'
    return html


BAR_COLORS = [
    "linear-gradient(90deg, #f78166, #ea4a5a)",
    "linear-gradient(90deg, #58a6ff, #388bfd)",
    "linear-gradient(90deg, #3fb950, #2ea043)",
    "linear-gradient(90deg, #bc8cff, #8957e5)",
    "linear-gradient(90deg, #d29922, #bb8009)",
    "linear-gradient(90deg, #39d2c0, #1e9e8f)",
    "linear-gradient(90deg, #f0883e, #d18616)",
    "linear-gradient(90deg, #8b949e, #6e7681)",
]


def generate_html(model_name, config, tree, model_class, total_params, size_str,
                  moe_info, mla_info=None, quant_info=None, is_synthetic=False,
                  active_params=None):
    """生成完整 HTML"""
    config_dict = extract_key_config(config)

    # Badges
    badges = []
    badges.append(f'<span class="badge badge-blue">Params: {format_params(total_params)}</span>')
    if active_params:
        badges.append(f'<span class="badge badge-green">Active: {format_params(active_params)}</span>')
    if moe_info and moe_info.get("is_moe"):
        badges.append('<span class="badge badge-orange">MoE</span>')
    if mla_info and mla_info.get("is_mla"):
        badges.append('<span class="badge badge-cyan">MLA</span>')
    if quant_info and quant_info.get("is_quantized"):
        method = quant_info.get("method", "").upper()
        bits = quant_info.get("bits", "?")
        badges.append(f'<span class="badge badge-purple">{method} {bits}-bit</span>')

    # Stat cards
    cards = []
    cards.append(_stat_card("Total Parameters", format_params(total_params)))
    if active_params:
        cards.append(_stat_card("Active Parameters", format_params(active_params), "per token"))
    cards.append(_stat_card("Model Size", size_str))
    num_layers = config_dict.get("num_hidden_layers", "-")
    cards.append(_stat_card("Layers", str(num_layers)))
    hidden_size = config_dict.get("hidden_size", "-")
    cards.append(_stat_card("Hidden Size", str(hidden_size)))

    if moe_info and moe_info.get("is_moe"):
        ec = moe_info.get("expert_counts", {})
        n_exp = ec.get("total_routed") or moe_info.get("num_local_experts") or moe_info.get("num_experts", "?")
        n_per = ec.get("per_token") or moe_info.get("num_experts_per_tok", "?")
        n_shared = ec.get("shared", 0)
        sub = f"top-{n_per}"
        if n_shared:
            sub += f" + {n_shared} shared"
        cards.append(_stat_card("MoE Experts", str(n_exp), sub))

    if mla_info and mla_info.get("is_mla"):
        kv_r = mla_info.get("kv_lora_rank", "?")
        q_r = mla_info.get("q_lora_rank", "?")
        cards.append(_stat_card("MLA", f"KV={kv_r}", f"Q={q_r}"))

    if quant_info and quant_info.get("is_quantized"):
        method = quant_info.get("method", "unknown")
        bits = quant_info.get("bits", "?")
        gs = quant_info.get("group_size")
        sub = f"group_size={gs}" if gs else ""
        cards.append(_stat_card("Quantization", f"{method} {bits}-bit", sub))

    # Config items
    config_html = ""
    skip_keys = {"_sub_configs", "rope_scaling"}
    for key, val in config_dict.items():
        if key in skip_keys:
            continue
        if isinstance(val, (list, dict)):
            val = str(val)[:80]
        config_html += (f'<div class="config-item">'
                       f'<span class="config-key">{html_module.escape(str(key))}</span>'
                       f'<span class="config-val">{html_module.escape(str(val))}</span></div>\n')

    # Sub-configs
    sub_configs = config_dict.get("_sub_configs", {})
    for sc_name, sc_vals in sub_configs.items():
        for sk, sv in sc_vals.items():
            if sv is not None:
                config_html += (f'<div class="config-item">'
                               f'<span class="config-key">{html_module.escape(sc_name)}.{html_module.escape(sk)}</span>'
                               f'<span class="config-val">{html_module.escape(str(sv)[:60])}</span></div>\n')

    # Parameter distribution bars
    bar_html = ""
    if tree and tree.get("children"):
        top_children = sorted(tree["children"], key=lambda c: c["total_params"], reverse=True)
        if total_params > 0:
            rows = []
            for i, child in enumerate(top_children[:8]):
                pct = child["total_params"] / total_params * 100
                color = BAR_COLORS[i % len(BAR_COLORS)]
                rows.append(
                    f'<div class="bar-row">'
                    f'<div class="bar-label"><span>{html_module.escape(child["name"])}</span>'
                    f'<span>{format_params(child["total_params"])} ({pct:.1f}%)</span></div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{min(pct, 100):.1f}%;background:{color}"></div></div>'
                    f'</div>\n'
                )
            bar_html = (f'<div class="bar-section"><h2>Parameter Distribution</h2>'
                       f'{"".join(rows)}</div>')

    # Tree HTML
    max_params = tree["total_params"] if tree else 0
    tree_html_str = tree_to_html(tree, max_params) if tree else "<li>No structure available</li>"
    tree_note = '<span style="color:#d29922;font-size:0.8em">(estimated from config)</span>' if is_synthetic else ""

    # Synthetic banner
    synthetic_banner = ""
    synthetic_banner_css = ""
    synthetic_banner_style = ""
    if is_synthetic:
        synthetic_banner_css = ".synth-banner { background:#3d2e00; border:1px solid #d29922; border-radius:8px; padding:12px 16px; margin-bottom:16px; color:#d29922; font-size:0.88em; }"
        synthetic_banner = '<div class="synth-banner">&#9888; 此结构树为配置估算生成，非实际模型加载。参数量为估算值。</div>'

    return HTML_TEMPLATE.format(
        model_name=html_module.escape(model_name),
        model_class=html_module.escape(model_class),
        badges="".join(badges),
        stat_cards="".join(cards),
        config_items=config_html,
        bar_section=bar_html,
        tree_html=tree_html_str,
        tree_note=tree_note,
        synthetic_banner=synthetic_banner,
        synthetic_banner_css=synthetic_banner_css,
        synthetic_banner_style=synthetic_banner_style,
    )


def _stat_card(label, value, sub=""):
    sub_html = f'<div class="stat-sub">{html_module.escape(sub)}</div>' if sub else ""
    return (f'<div class="stat-card">'
            f'<div class="stat-label">{html_module.escape(label)}</div>'
            f'<div class="stat-value">{html_module.escape(value)}</div>'
            f'{sub_html}</div>\n')


def main():
    parser = argparse.ArgumentParser(description="生成 HuggingFace 模型架构可视化 HTML")
    parser.add_argument("model", help="模型名称或本地路径")
    parser.add_argument("--output", default=None, help="输出 HTML 文件路径")
    parser.add_argument("--config-only", action="store_true",
                        help="仅使用配置估算")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--token", help="HuggingFace 认证 token")
    parser.add_argument("--max-depth", type=int, default=4, help="树最大深度")
    parser.add_argument("--open", action="store_true", help="生成后自动打开")

    args = parser.parse_args()
    check_dependencies()

    if args.output is None:
        safe_name = args.model.replace("/", "_").replace("\\", "_")
        args.output = f"/tmp/model_viz_{safe_name}.html"

    try:
        config = load_config(args.model, args.trust_remote_code, args.token)
        moe_info = detect_moe(config)
        mla_info = detect_mla(config)
        quant_info = detect_quantization(config)

        is_synthetic = False
        active_params = None

        if args.config_only:
            # 直接用合成树
            tree = build_synthetic_tree(config, args.max_depth)
            estimated = estimate_params_from_config(config)
            arch = config.architectures[0] if hasattr(config, 'architectures') and config.architectures else "Model"
            model_class = f"{arch} (estimated)"
            total_params = estimated["estimated_total"] if estimated else 0
            if estimated and "active_params" in estimated.get("breakdown", {}):
                active_params = estimated["breakdown"]["active_params"]["total"]
            config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
            dtype_str = str(config_dict.get("torch_dtype", config_dict.get("dtype", "float16")))
            bytes_per = {"float32": 4, "float16": 2, "bfloat16": 2}.get(dtype_str, 2)
            size_bytes = total_params * bytes_per
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb / 1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
            is_synthetic = True
        else:
            try:
                model = load_model_meta(config, args.trust_remote_code)
                model_class = model.__class__.__name__
                tree = build_tree(model, model_class, args.max_depth)
                total_params = sum(p.numel() for p in model.parameters())
                size_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb / 1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
            except Exception:
                # Fallback to synthetic tree
                tree = build_synthetic_tree(config, args.max_depth)
                estimated = estimate_params_from_config(config)
                arch = config.architectures[0] if hasattr(config, 'architectures') and config.architectures else "Model"
                model_class = f"{arch} (estimated)"
                total_params = estimated["estimated_total"] if estimated else 0
                if estimated and "active_params" in estimated.get("breakdown", {}):
                    active_params = estimated["breakdown"]["active_params"]["total"]
                config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
                dtype_str = str(config_dict.get("torch_dtype", config_dict.get("dtype", "float16")))
                bytes_per = {"float32": 4, "float16": 2, "bfloat16": 2}.get(dtype_str, 2)
                size_bytes = total_params * bytes_per
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb / 1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
                is_synthetic = True

        if tree is None:
            print(json.dumps({"error": "无法构建结构树", "fix": "检查模型配置是否完整"},
                             ensure_ascii=False, indent=2))
            sys.exit(1)

        html_content = generate_html(
            args.model, config, tree, model_class, total_params, size_str,
            moe_info, mla_info, quant_info, is_synthetic, active_params
        )

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html_content)

        result = {
            "output_path": args.output,
            "model_name": args.model,
            "total_params": format_params(total_params),
            "is_synthetic": is_synthetic,
            "error": None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if args.open:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(args.output)}")

    except Exception as e:
        print(json.dumps({"error": str(e), "fix": None},
                         ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
