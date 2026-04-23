#!/usr/bin/env python3
"""HuggingFace Model Explorer - 探索模型结构、参数统计"""

import argparse
import json
import sys
import re


def check_dependencies():
    """检查必要依赖"""
    missing = []
    try:
        import transformers
    except ImportError:
        missing.append("transformers")
    try:
        import torch
    except ImportError:
        missing.append("torch")
    if missing:
        print(json.dumps({
            "error": f"缺少依赖: {', '.join(missing)}",
            "fix": f"pip install {' '.join(missing)}"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


# ============================================================
# 配置加载与模型卡片
# ============================================================

def load_config(model_name, trust_remote_code=False, token=None):
    """加载模型配置"""
    from transformers import AutoConfig
    kwargs = {"trust_remote_code": trust_remote_code}
    if token:
        kwargs["token"] = token
    return AutoConfig.from_pretrained(model_name, **kwargs)


def fetch_model_card(model_name, token=None):
    """从 HuggingFace Hub 获取模型卡片信息"""
    result = {"model_name": model_name}
    try:
        from huggingface_hub import model_info as hf_model_info
        kwargs = {}
        if token:
            kwargs["token"] = token
        info = hf_model_info(model_name, **kwargs)
        result["model_id"] = info.id
        result["author"] = info.author
        result["tags"] = info.tags or []
        result["pipeline_tag"] = info.pipeline_tag
        result["library_name"] = info.library_name
        result["license"] = getattr(info, "card_data", None) and getattr(info.card_data, "license", None)
        result["downloads"] = info.downloads
        result["likes"] = info.likes
    except Exception:
        pass

    # 下载 README.md 前 300 行提取模型介绍
    try:
        from huggingface_hub import hf_hub_download
        kwargs = {}
        if token:
            kwargs["token"] = token
        readme_path = hf_hub_download(model_name, "README.md", **kwargs)
        with open(readme_path, "r", encoding="utf-8") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= 300:
                    break
                lines.append(line)
        readme_text = "".join(lines)

        # 提取 YAML frontmatter 后面的介绍段落
        intro_lines = []
        in_frontmatter = False
        past_frontmatter = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---" and not past_frontmatter:
                if in_frontmatter:
                    past_frontmatter = True
                    in_frontmatter = False
                else:
                    in_frontmatter = True
                continue
            if in_frontmatter:
                continue
            if past_frontmatter or not stripped.startswith("---"):
                # 跳过标题行和空行直到找到正文
                if stripped and not stripped.startswith("#"):
                    intro_lines.append(line.rstrip())
                elif intro_lines:
                    # 遇到空行或标题时停止
                    if not stripped and len(intro_lines) > 2:
                        break
                    elif stripped.startswith("#") and len(intro_lines) > 1:
                        break
                    elif stripped:
                        intro_lines.append(line.rstrip())
        result["introduction"] = "\n".join(intro_lines[:20])

        # 提取所需 transformers 版本
        version_patterns = [
            r"transformers[>=<]+\s*([\d.]+)",
            r"transformers\s+version\s*[>=<]*\s*([\d.]+)",
            r"pip install.*transformers[>=<]+([\d.]+)",
        ]
        for pat in version_patterns:
            m = re.search(pat, readme_text, re.IGNORECASE)
            if m:
                result["required_transformers_version"] = m.group(1)
                break

    except Exception:
        pass

    return result


# ============================================================
# 检测函数
# ============================================================

def detect_moe(config):
    """检测是否为 MoE 模型，提取完整 MoE 信息"""
    moe_info = {"is_moe": False}
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}

    # 合并顶层和子配置中的 MoE 信息
    def _scan_moe_keys(d):
        """从一个 dict 中提取 MoE 相关字段"""
        found = {}
        # 专家数量
        for key in ["n_routed_experts", "num_local_experts", "num_experts", "moe_num_experts"]:
            if key in d and d[key] is not None:
                found["total_routed"] = d[key]
                found["_key_routed"] = key
                break
        # 每 token 激活数
        for key in ["num_experts_per_tok", "num_selected_experts", "experts_per_tok"]:
            if key in d and d[key] is not None:
                found["per_token"] = d[key]
                break
        # 共享专家
        for key in ["n_shared_experts", "num_shared_experts"]:
            if key in d and d[key] is not None:
                found["shared"] = d[key]
                break
        # 其他 MoE 架构参数
        for key in ["moe_intermediate_size", "first_k_dense_replace", "moe_layer_freq"]:
            if key in d and d[key] is not None:
                found[key] = d[key]
        # 路由参数
        routing = {}
        for key in ["topk_method", "topk_group", "n_group", "scoring_func",
                     "norm_topk_prob", "routed_scaling_factor"]:
            if key in d and d[key] is not None:
                routing[key] = d[key]
        if routing:
            found["routing"] = routing
        return found

    # 扫描顶层
    top_moe = _scan_moe_keys(config_dict)
    if "total_routed" in top_moe:
        moe_info["is_moe"] = True
        moe_info["expert_counts"] = {
            "total_routed": top_moe["total_routed"],
            "per_token": top_moe.get("per_token"),
            "shared": top_moe.get("shared", 0),
        }
        moe_info["architecture"] = {
            k: top_moe[k] for k in ["moe_intermediate_size", "first_k_dense_replace", "moe_layer_freq"]
            if k in top_moe
        }
        if "routing" in top_moe:
            moe_info["routing"] = top_moe["routing"]

    # 扫描嵌套子配置
    for k, v in config_dict.items():
        if isinstance(v, dict):
            sub_moe = _scan_moe_keys(v)
            if "total_routed" in sub_moe:
                moe_info["is_moe"] = True
                moe_info.setdefault("sub_configs", {})[k] = sub_moe

    return moe_info


def detect_mla(config):
    """检测 Multi-head Latent Attention (MLA) 配置"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    mla_keys = ["kv_lora_rank", "q_lora_rank", "qk_nope_head_dim", "qk_rope_head_dim", "v_head_dim"]

    mla_info = {"is_mla": False}

    # 检查顶层
    found = {k: config_dict[k] for k in mla_keys if k in config_dict and config_dict[k] is not None}
    if "kv_lora_rank" in found:
        mla_info["is_mla"] = True
        mla_info.update(found)

    # 检查子配置
    for k, v in config_dict.items():
        if isinstance(v, dict) and "kv_lora_rank" in v:
            mla_info["is_mla"] = True
            sub = {mk: v[mk] for mk in mla_keys if mk in v and v[mk] is not None}
            mla_info.setdefault("sub_configs", {})[k] = sub
            # 如果顶层没有找到，用子配置的值
            if "kv_lora_rank" not in mla_info:
                mla_info.update(sub)

    return mla_info


def detect_quantization(config):
    """解析量化配置"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    quant_config = config_dict.get("quantization_config")

    if not quant_config:
        # 也检查子配置中的量化
        for k, v in config_dict.items():
            if isinstance(v, dict) and "quantization_config" in v:
                quant_config = v["quantization_config"]
                break
    if not quant_config:
        return {"is_quantized": False}

    result = {"is_quantized": True}
    method = quant_config.get("quant_method", "unknown")
    result["method"] = method

    if method == "compressed-tensors":
        groups = quant_config.get("config_groups", {})
        for gname, gconf in groups.items():
            w = gconf.get("weights", {})
            result["bits"] = w.get("num_bits", 4)
            result["group_size"] = w.get("group_size")
            result["strategy"] = w.get("strategy")
            result["symmetric"] = w.get("symmetric")
        result["format"] = quant_config.get("format")
        result["ignore_patterns"] = quant_config.get("ignore", [])

    elif method == "fp8":
        result["bits"] = 8
        result["format"] = quant_config.get("fmt")
        result["activation_scheme"] = quant_config.get("activation_scheme")

    elif method in ("gptq", "awq"):
        result["bits"] = quant_config.get("bits", 4)
        result["group_size"] = quant_config.get("group_size")

    elif method == "bitsandbytes":
        is_4bit = quant_config.get("load_in_4bit", False)
        is_8bit = quant_config.get("load_in_8bit", False)
        result["bits"] = 4 if is_4bit else (8 if is_8bit else 16)
        result["quant_type"] = quant_config.get("bnb_4bit_quant_type")
        result["skip_modules"] = quant_config.get("llm_int8_skip_modules", [])

    return result


def detect_sub_configs(config):
    """检测多模态子配置"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    known_sub_keys = [
        "text_config", "vision_config", "audio_config",
        "thinker_config", "talker_config",
        "projector_config", "perceiver_config",
    ]

    detected = {}
    for key, val in config_dict.items():
        if not isinstance(val, dict):
            continue
        has_model_keys = any(mk in val for mk in [
            "hidden_size", "num_hidden_layers", "num_attention_heads",
            "depth", "num_heads"
        ])
        if key in known_sub_keys or (has_model_keys and key.endswith("_config")):
            summary = {
                "model_type": val.get("model_type"),
                "architectures": val.get("architectures"),
                "hidden_size": val.get("hidden_size") or val.get("mm_hidden_size") or val.get("vt_hidden_size"),
                "num_hidden_layers": val.get("num_hidden_layers") or val.get("depth") or val.get("vt_num_hidden_layers"),
                "intermediate_size": val.get("intermediate_size") or val.get("vt_intermediate_size"),
                "num_attention_heads": val.get("num_attention_heads") or val.get("num_heads") or val.get("vt_num_attention_heads"),
                "vocab_size": val.get("vocab_size"),
            }
            # 清除 None 值
            summary = {k: v for k, v in summary.items() if v is not None}
            summary["_full"] = val  # 保留完整配置用于详细估算
            detected[key] = summary

    return detected if detected else None


# ============================================================
# 配置提取
# ============================================================

def extract_key_config(config):
    """提取关键配置信息"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}

    key_fields = [
        "architectures", "model_type", "hidden_size", "num_hidden_layers",
        "num_attention_heads", "num_key_value_heads", "intermediate_size",
        "vocab_size", "max_position_embeddings", "torch_dtype",
        "tie_word_embeddings", "rope_type", "rope_theta",
        "sliding_window", "head_dim",
        # MLA
        "kv_lora_rank", "q_lora_rank", "qk_nope_head_dim", "qk_rope_head_dim", "v_head_dim",
        # MoE
        "n_routed_experts", "n_shared_experts", "num_local_experts",
        "num_experts_per_tok", "moe_intermediate_size", "first_k_dense_replace",
        "moe_layer_freq",
        # RoPE scaling
        "rope_scaling",
    ]

    result = {}
    for field in key_fields:
        if field in config_dict:
            result[field] = config_dict[field]

    # 添加子配置摘要
    sub_configs = detect_sub_configs(config)
    if sub_configs:
        result["_sub_configs"] = {
            name: {k: v for k, v in sc.items() if k != "_full"}
            for name, sc in sub_configs.items()
        }

    return result


# ============================================================
# 参数估算
# ============================================================

def _estimate_attention_params(cfg_dict):
    """估算每层 attention 参数量，MLA 感知"""
    h = cfg_dict.get("hidden_size", 0)
    n_heads = cfg_dict.get("num_attention_heads", 0)
    if h == 0 or n_heads == 0:
        return 0

    kv_lora = cfg_dict.get("kv_lora_rank")
    q_lora = cfg_dict.get("q_lora_rank")

    if kv_lora and q_lora:
        # MLA (DeepseekV3 style)
        qk_nope = cfg_dict.get("qk_nope_head_dim", 128)
        qk_rope = cfg_dict.get("qk_rope_head_dim", 64)
        v_head = cfg_dict.get("v_head_dim", 128)

        q_down = h * q_lora
        q_norm = q_lora
        q_up = q_lora * n_heads * (qk_nope + qk_rope)
        kv_down = h * (kv_lora + qk_rope)  # kv_a_proj_with_mqa
        kv_norm = kv_lora
        kv_up = kv_lora * n_heads * (qk_nope + v_head)
        o_proj = n_heads * v_head * h

        return q_down + q_norm + q_up + kv_down + kv_norm + kv_up + o_proj
    else:
        # 标准 MHA/GQA
        n_kv = cfg_dict.get("num_key_value_heads", n_heads)
        head_dim = cfg_dict.get("head_dim", h // n_heads if n_heads > 0 else 0)
        q = h * n_heads * head_dim
        k = h * n_kv * head_dim
        v = h * n_kv * head_dim
        o = n_heads * head_dim * h
        return q + k + v + o


def _estimate_mlp_params(h, intermediate_size):
    """估算 gated MLP 参数量 (SwiGLU: gate + up + down)"""
    if h == 0 or intermediate_size == 0:
        return 0
    return 3 * h * intermediate_size


def _estimate_vision_params(vision_cfg):
    """估算 ViT 视觉编码器参数量"""
    h = vision_cfg.get("hidden_size") or vision_cfg.get("mm_hidden_size") or vision_cfg.get("vt_hidden_size", 0)
    n_layers = vision_cfg.get("num_hidden_layers") or vision_cfg.get("depth") or vision_cfg.get("vt_num_hidden_layers", 0)
    inter = vision_cfg.get("intermediate_size") or vision_cfg.get("vt_intermediate_size", 0)
    patch_size = vision_cfg.get("patch_size") or vision_cfg.get("spatial_patch_size", 14)
    in_ch = vision_cfg.get("num_channels") or vision_cfg.get("in_channels", 3)

    if h == 0 or n_layers == 0:
        return 0, {}

    # Patch embedding
    temporal_patch = vision_cfg.get("temporal_patch_size", 1)
    if temporal_patch > 1:
        # Conv3d
        patch_embed = in_ch * h * temporal_patch * patch_size * patch_size + h
    else:
        # Conv2d
        patch_embed = in_ch * h * patch_size * patch_size + h

    # ViT 标准层: QKV + O + MLP (非 gated, 2层) + 2*LayerNorm
    qkv = 3 * (h * h + h)  # with bias
    o = h * h + h
    mlp = h * inter + inter + inter * h + h  # fc1 + fc2, with bias
    ln = 2 * (h + h)  # weight + bias
    per_layer = qkv + o + mlp + ln

    total = patch_embed + n_layers * per_layer + (h + h)  # final layernorm
    return total, {
        "hidden_size": h,
        "num_layers": n_layers,
        "intermediate_size": inter,
        "patch_embed": patch_embed,
        "per_layer": per_layer,
        "total": total,
    }


def estimate_params_from_config(config):
    """从配置估算参数量，支持 MLA、MoE、多模态"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    breakdown = {}
    grand_total = 0

    # 检测子配置
    sub_configs = detect_sub_configs(config)

    # 确定 text 配置
    text_cfg = config_dict
    if sub_configs and "text_config" in sub_configs:
        text_cfg = sub_configs["text_config"]["_full"]

    h = text_cfg.get("hidden_size", 0)
    n_layers = text_cfg.get("num_hidden_layers", 0)
    vocab = text_cfg.get("vocab_size", 0) or config_dict.get("vocab_size", 0)
    inter = text_cfg.get("intermediate_size", 0)

    if h == 0 or n_layers == 0:
        return None

    # Embedding
    embed_params = vocab * h
    breakdown["embedding"] = embed_params
    grand_total += embed_params

    # 每层 attention
    attn_per_layer = _estimate_attention_params(text_cfg)
    norm_per_layer = 2 * h

    # MoE 检测
    n_routed = (text_cfg.get("n_routed_experts") or text_cfg.get("num_local_experts") or
                config_dict.get("n_routed_experts") or config_dict.get("num_local_experts"))
    n_shared = (text_cfg.get("n_shared_experts") or config_dict.get("n_shared_experts") or 0)
    moe_inter = text_cfg.get("moe_intermediate_size") or config_dict.get("moe_intermediate_size")
    first_k_dense = (text_cfg.get("first_k_dense_replace") or
                     config_dict.get("first_k_dense_replace") or 0)

    if n_routed and moe_inter:
        # MoE 模型
        dense_mlp = _estimate_mlp_params(h, inter)
        expert_mlp = _estimate_mlp_params(h, moe_inter)
        shared_mlp = n_shared * expert_mlp if n_shared else 0
        router = h * n_routed

        n_dense = first_k_dense
        n_moe = n_layers - n_dense

        dense_per_layer = attn_per_layer + norm_per_layer + dense_mlp
        moe_per_layer = attn_per_layer + norm_per_layer + n_routed * expert_mlp + shared_mlp + router

        layer_total = n_dense * dense_per_layer + n_moe * moe_per_layer
        breakdown["attention_per_layer"] = attn_per_layer
        breakdown["dense_layers"] = {"count": n_dense, "params_per_layer": dense_per_layer,
                                     "total": n_dense * dense_per_layer}
        breakdown["moe_layers"] = {
            "count": n_moe, "params_per_layer": moe_per_layer,
            "total": n_moe * moe_per_layer,
            "routed_experts": n_routed, "shared_experts": n_shared,
            "expert_mlp": expert_mlp, "moe_intermediate_size": moe_inter,
        }
    elif inter > 0:
        # 标准 dense 模型
        mlp_per_layer = _estimate_mlp_params(h, inter)
        per_layer = attn_per_layer + mlp_per_layer + norm_per_layer
        layer_total = n_layers * per_layer
        breakdown["per_layer"] = per_layer
    else:
        layer_total = 0

    grand_total += layer_total

    # Final norm + LM head
    grand_total += h
    tie = text_cfg.get("tie_word_embeddings", config_dict.get("tie_word_embeddings", True))
    if not tie:
        lm_head = vocab * h
        breakdown["lm_head"] = lm_head
        grand_total += lm_head

    # Vision encoder
    if sub_configs and "vision_config" in sub_configs:
        vis_cfg = sub_configs["vision_config"]["_full"]
        vis_total, vis_detail = _estimate_vision_params(vis_cfg)
        if vis_total > 0:
            breakdown["vision_encoder"] = vis_detail
            grand_total += vis_total

            # Projector 估算
            vis_h = vis_detail.get("hidden_size", 0)
            text_h = h
            merge_size = vis_cfg.get("spatial_merge_size") or vis_cfg.get("merge_kernel_size")
            if isinstance(merge_size, list):
                merge_factor = merge_size[0] * merge_size[1]
            elif merge_size:
                merge_factor = merge_size * merge_size
            else:
                merge_factor = 4

            proj_params = vis_h * merge_factor * text_h + text_h
            breakdown["projector"] = proj_params
            grand_total += proj_params

    # 激活参数估算 (MoE)
    active_total = None
    if n_routed and moe_inter:
        per_tok = (text_cfg.get("num_experts_per_tok") or config_dict.get("num_experts_per_tok") or 1)
        active_expert_mlp = per_tok * expert_mlp + shared_mlp + router
        active_moe_layer = attn_per_layer + norm_per_layer + active_expert_mlp
        active_layer_total = n_dense * dense_per_layer + n_moe * active_moe_layer
        active_total = embed_params + active_layer_total + h
        if not tie:
            active_total += vocab * h
        # 加上 vision
        if "vision_encoder" in breakdown:
            active_total += breakdown["vision_encoder"]["total"]
        if "projector" in breakdown:
            active_total += breakdown["projector"]
        breakdown["active_params"] = {
            "total": int(active_total),
            "total_str": format_params(int(active_total)),
            "experts_per_token": per_tok,
        }

    return {
        "estimated_total": int(grand_total),
        "estimated_total_str": format_params(int(grand_total)),
        "breakdown": _serialize_breakdown(breakdown),
        "note": "估算值，实际参数量可能略有差异",
    }


def _serialize_breakdown(breakdown):
    """将 breakdown 中的整数递归转为 int"""
    result = {}
    for k, v in breakdown.items():
        if isinstance(v, dict):
            result[k] = _serialize_breakdown(v)
        elif isinstance(v, float):
            result[k] = int(v)
        else:
            result[k] = v
    return result


# ============================================================
# 合成树（从 config 构建）
# ============================================================

def build_synthetic_tree(config, max_depth=4):
    """当 meta device 加载失败时，从 config 构建仿真结构树"""
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    sub_configs = detect_sub_configs(config)

    text_cfg = config_dict
    if sub_configs and "text_config" in sub_configs:
        text_cfg = sub_configs["text_config"]["_full"]

    h = text_cfg.get("hidden_size", 0)
    n_layers = text_cfg.get("num_hidden_layers", 0)
    vocab = text_cfg.get("vocab_size", 0) or config_dict.get("vocab_size", 0)

    if h == 0 or n_layers == 0:
        return None

    arch_name = "Model"
    if config_dict.get("architectures"):
        arch_name = config_dict["architectures"][0]

    root_children = []
    total_params = 0

    # --- Vision encoder ---
    if sub_configs and "vision_config" in sub_configs:
        vis_cfg = sub_configs["vision_config"]["_full"]
        vis_total, vis_detail = _estimate_vision_params(vis_cfg)
        if vis_total > 0:
            vis_node = _build_synthetic_vision(vis_cfg, vis_detail, max_depth - 1)
            root_children.append(vis_node)
            total_params += vis_total

        # Projector
        vis_h = vis_detail.get("hidden_size", 0) if vis_detail else 0
        merge_size = vis_cfg.get("spatial_merge_size") or vis_cfg.get("merge_kernel_size")
        if isinstance(merge_size, list):
            merge_factor = merge_size[0] * merge_size[1]
        elif merge_size:
            merge_factor = merge_size * merge_size
        else:
            merge_factor = 4
        proj_type = vis_cfg.get("mm_projector_type", "patchmerger")
        proj_params = vis_h * merge_factor * h + h
        root_children.append({
            "name": "multi_modal_projector",
            "type": f"Projector({proj_type})",
            "own_params": proj_params,
            "total_params": proj_params,
            "children": [
                _leaf("ln", "LayerNorm", vis_h + vis_h),
                _leaf("linear", f"Linear({vis_h * merge_factor}→{h})", proj_params - vis_h - vis_h),
            ] if max_depth > 1 else [],
        })
        total_params += proj_params

    # --- Language model ---
    lm_children = []
    lm_total = 0

    # Embedding
    embed_params = vocab * h
    lm_children.append(_leaf("embed_tokens", f"Embedding({vocab}, {h})", embed_params))
    lm_total += embed_params

    # Layers
    moe_info = detect_moe(config)
    mla_info = detect_mla(config)

    n_routed = (text_cfg.get("n_routed_experts") or text_cfg.get("num_local_experts") or
                config_dict.get("n_routed_experts") or config_dict.get("num_local_experts"))
    n_shared = (text_cfg.get("n_shared_experts") or config_dict.get("n_shared_experts") or 0)
    moe_inter = text_cfg.get("moe_intermediate_size") or config_dict.get("moe_intermediate_size")
    first_k_dense = text_cfg.get("first_k_dense_replace") or config_dict.get("first_k_dense_replace") or 0
    inter = text_cfg.get("intermediate_size", 0)

    attn_params = _estimate_attention_params(text_cfg)
    layers_children = []
    layers_total = 0

    for i in range(min(n_layers, 200)):
        is_dense = (i < first_k_dense) or not (n_routed and moe_inter)
        layer_node = _build_synthetic_layer(
            text_cfg, config_dict, i, is_dense, attn_params,
            n_routed, n_shared, moe_inter, inter, h,
            mla_info, max_depth - 2
        )
        layers_children.append(layer_node)
        layers_total += layer_node["total_params"]

    layers_node = {
        "name": "layers",
        "type": f"ModuleList({n_layers})",
        "own_params": 0,
        "total_params": layers_total,
        "children": layers_children if max_depth >= 2 else [],
    }
    lm_children.append(layers_node)
    lm_total += layers_total

    # Final norm
    norm_params = h
    lm_children.append(_leaf("norm", f"RMSNorm({h})", norm_params))
    lm_total += norm_params

    # LM head
    tie = text_cfg.get("tie_word_embeddings", config_dict.get("tie_word_embeddings", True))
    if not tie:
        lm_params = vocab * h
        lm_children.append(_leaf("lm_head", f"Linear({h}→{vocab})", lm_params))
        lm_total += lm_params

    # 包装 language_model
    if sub_configs:
        lm_name = "language_model"
        lm_type = text_cfg.get("architectures", ["DecoderModel"])[0] if text_cfg.get("architectures") else "DecoderModel"
        lm_node = {
            "name": lm_name, "type": lm_type,
            "own_params": 0, "total_params": lm_total,
            "children": lm_children if max_depth >= 1 else [],
        }
        root_children.append(lm_node)
    else:
        root_children = lm_children

    total_params += lm_total

    return {
        "name": arch_name, "type": arch_name,
        "own_params": 0, "total_params": total_params,
        "children": root_children,
        "_synthetic": True,
    }


def _leaf(name, type_str, params):
    """创建叶子节点"""
    return {"name": name, "type": type_str, "own_params": params, "total_params": params, "children": []}


def _build_synthetic_layer(text_cfg, config_dict, idx, is_dense, attn_params,
                           n_routed, n_shared, moe_inter, inter, h,
                           mla_info, remaining_depth):
    """构建单个 Transformer 层节点"""
    children = []
    layer_total = 0

    # Attention
    attn_children = []
    if remaining_depth > 0 and mla_info.get("is_mla"):
        kv_lora = mla_info.get("kv_lora_rank", 512)
        q_lora = mla_info.get("q_lora_rank", 1536)
        qk_nope = mla_info.get("qk_nope_head_dim", 128)
        qk_rope = mla_info.get("qk_rope_head_dim", 64)
        v_head = mla_info.get("v_head_dim", 128)
        n_heads = text_cfg.get("num_attention_heads", 64)
        attn_children = [
            _leaf("q_a_proj", f"Linear({h}→{q_lora})", h * q_lora),
            _leaf("q_a_layernorm", f"RMSNorm({q_lora})", q_lora),
            _leaf("q_b_proj", f"Linear({q_lora}→{n_heads * (qk_nope + qk_rope)})", q_lora * n_heads * (qk_nope + qk_rope)),
            _leaf("kv_a_proj_with_mqa", f"Linear({h}→{kv_lora + qk_rope})", h * (kv_lora + qk_rope)),
            _leaf("kv_a_layernorm", f"RMSNorm({kv_lora})", kv_lora),
            _leaf("kv_b_proj", f"Linear({kv_lora}→{n_heads * (qk_nope + v_head)})", kv_lora * n_heads * (qk_nope + v_head)),
            _leaf("o_proj", f"Linear({n_heads * v_head}→{h})", n_heads * v_head * h),
        ]
        attn_type = "MLA"
    elif remaining_depth > 0:
        n_heads = text_cfg.get("num_attention_heads", 0)
        n_kv = text_cfg.get("num_key_value_heads", n_heads)
        head_dim = text_cfg.get("head_dim", h // n_heads if n_heads > 0 else 0)
        attn_children = [
            _leaf("q_proj", f"Linear({h}→{n_heads * head_dim})", h * n_heads * head_dim),
            _leaf("k_proj", f"Linear({h}→{n_kv * head_dim})", h * n_kv * head_dim),
            _leaf("v_proj", f"Linear({h}→{n_kv * head_dim})", h * n_kv * head_dim),
            _leaf("o_proj", f"Linear({n_heads * head_dim}→{h})", n_heads * head_dim * h),
        ]
        attn_type = "GQA" if n_kv < n_heads else "MHA"
    else:
        attn_type = "Attention"

    children.append({
        "name": "self_attn", "type": attn_type,
        "own_params": 0, "total_params": attn_params,
        "children": attn_children,
    })
    layer_total += attn_params

    # MLP / MoE
    if is_dense:
        mlp_params = _estimate_mlp_params(h, inter)
        mlp_children = []
        if remaining_depth > 0 and inter > 0:
            mlp_children = [
                _leaf("gate_proj", f"Linear({h}→{inter})", h * inter),
                _leaf("up_proj", f"Linear({h}→{inter})", h * inter),
                _leaf("down_proj", f"Linear({inter}→{h})", inter * h),
            ]
        children.append({
            "name": "mlp", "type": f"DenseMLP({h}→{inter}→{h})",
            "own_params": 0, "total_params": mlp_params,
            "children": mlp_children,
        })
        layer_total += mlp_params
        layer_label = f"DenseLayer"
    else:
        # MoE
        expert_mlp = _estimate_mlp_params(h, moe_inter)
        shared_mlp = n_shared * expert_mlp if n_shared else 0
        router_params = h * n_routed
        moe_total = n_routed * expert_mlp + shared_mlp + router_params

        moe_children = []
        if remaining_depth > 0:
            moe_children.append(_leaf("gate", f"Linear({h}→{n_routed})", router_params))
            moe_children.append({
                "name": f"experts", "type": f"ModuleList({n_routed}×MLP)",
                "own_params": 0, "total_params": n_routed * expert_mlp,
                "children": [
                    _leaf(f"[0..{n_routed-1}]", f"SwiGLU({h}→{moe_inter}→{h})", expert_mlp),
                ] if remaining_depth > 1 else [],
            })
            if n_shared:
                moe_children.append({
                    "name": f"shared_experts", "type": f"SharedMLP(×{n_shared})",
                    "own_params": 0, "total_params": shared_mlp,
                    "children": [],
                })

        children.append({
            "name": "mlp", "type": "MoE",
            "own_params": 0, "total_params": moe_total,
            "children": moe_children,
        })
        layer_total += moe_total
        layer_label = f"MoELayer"

    # Norms
    norm_params = 2 * h
    layer_total += norm_params

    return {
        "name": f"layers.{idx}",
        "type": layer_label,
        "own_params": norm_params,
        "total_params": layer_total,
        "children": children if remaining_depth >= 0 else [],
    }


def _build_synthetic_vision(vis_cfg, vis_detail, remaining_depth):
    """构建视觉编码器节点"""
    h = vis_detail.get("hidden_size", 0)
    n_layers = vis_detail.get("num_layers", 0)

    children = []
    if remaining_depth > 0:
        children.append(_leaf("patch_embed", f"PatchEmbed→{h}", vis_detail.get("patch_embed", 0)))
        blocks_total = n_layers * vis_detail.get("per_layer", 0)
        children.append({
            "name": f"blocks", "type": f"ViTBlock(×{n_layers})",
            "own_params": 0, "total_params": blocks_total,
            "children": [],
        })

    return {
        "name": "visual", "type": "VisionEncoder",
        "own_params": 0, "total_params": vis_detail.get("total", 0),
        "children": children,
    }


# ============================================================
# 模型加载
# ============================================================

def load_model_meta(config, trust_remote_code=False):
    """使用 meta device 加载模型（零内存占用），多策略"""
    import torch

    errors = []

    # 策略 1: 根据 auto_map 选择
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    auto_map = config_dict.get("auto_map", {})
    auto_class_priority = []
    if auto_map:
        for key in ["AutoModelForCausalLM", "AutoModelForImageTextToText",
                     "AutoModel", "AutoModelForSeq2SeqLM"]:
            if key in auto_map:
                auto_class_priority.insert(0, key)

    # 策略 2: 根据架构名推断
    if hasattr(config, "architectures") and config.architectures:
        arch = config.architectures[0]
        arch_map = {
            "ForCausalLM": "AutoModelForCausalLM",
            "ForConditionalGeneration": "AutoModelForImageTextToText",
            "ForImageTextToText": "AutoModelForImageTextToText",
            "ForSeq2SeqLM": "AutoModelForSeq2SeqLM",
        }
        for suffix, cls_name in arch_map.items():
            if suffix in arch and cls_name not in auto_class_priority:
                auto_class_priority.append(cls_name)

    # 默认候选
    for cls_name in ["AutoModelForCausalLM", "AutoModel"]:
        if cls_name not in auto_class_priority:
            auto_class_priority.append(cls_name)

    # 尝试加载
    import transformers
    for cls_name in auto_class_priority:
        cls = getattr(transformers, cls_name, None)
        if cls is None:
            continue
        for trc in ([trust_remote_code] if not trust_remote_code else [True, False]):
            try:
                with torch.device("meta"):
                    model = cls.from_config(config, trust_remote_code=trc)
                return model
            except Exception as e:
                errors.append(f"{cls_name}(trust_remote_code={trc}): {e}")

    # 策略 5: 仅加载 text_config 子模型
    sub_configs = detect_sub_configs(config)
    if sub_configs and "text_config" in sub_configs:
        try:
            from transformers import AutoConfig, AutoModelForCausalLM
            text_full = sub_configs["text_config"]["_full"]
            text_config = AutoConfig.for_model(
                text_full.get("model_type", "llama"), **text_full
            )
            with torch.device("meta"):
                model = AutoModelForCausalLM.from_config(text_config, trust_remote_code=trust_remote_code)
            return model
        except Exception as e:
            errors.append(f"text_config fallback: {e}")

    raise RuntimeError(f"所有加载策略均失败:\n" + "\n".join(f"  - {e}" for e in errors))


# ============================================================
# 通用工具函数
# ============================================================

def build_tree(module, name="", max_depth=3, current_depth=0):
    """递归构建模块树"""
    own_params = sum(p.numel() for p in module.parameters(recurse=False))
    total_params = sum(p.numel() for p in module.parameters())

    node = {
        "name": name or module.__class__.__name__,
        "type": module.__class__.__name__,
        "own_params": own_params,
        "total_params": total_params,
        "children": []
    }

    if current_depth < max_depth:
        for child_name, child_module in module.named_children():
            child_node = build_tree(child_module, child_name, max_depth, current_depth + 1)
            node["children"].append(child_node)

    return node


def tree_to_text(node, prefix="", is_last=True, is_root=True):
    """将树结构转为文本格式"""
    lines = []

    if is_root:
        params_str = f"  ({format_params(node['total_params'])})" if node["total_params"] > 0 else ""
        lines.append(f"{node['name']}{params_str}")
    else:
        connector = "└── " if is_last else "├── "
        params_str = f"  ({format_params(node['total_params'])})" if node["total_params"] > 0 else ""
        lines.append(f"{prefix}{connector}{node['name']}: {node['type']}{params_str}")

    child_prefix = prefix + ("    " if is_last else "│   ")
    children = node.get("children", [])
    for i, child in enumerate(children):
        is_child_last = (i == len(children) - 1)
        lines.extend(tree_to_text(child, child_prefix if not is_root else "", is_child_last, False))

    return lines


def format_params(count):
    """格式化参数量"""
    if count >= 1e9:
        return f"{count / 1e9:.2f}B"
    elif count >= 1e6:
        return f"{count / 1e6:.2f}M"
    elif count >= 1e3:
        return f"{count / 1e3:.2f}K"
    return str(count)


def get_dtype_distribution(model):
    """统计参数的 dtype 分布"""
    dist = {}
    for p in model.parameters():
        dtype_str = str(p.dtype)
        if dtype_str not in dist:
            dist[dtype_str] = 0
        dist[dtype_str] += p.numel()
    return dist


def get_top_modules(model, top_n=15):
    """获取顶层模块的参数统计"""
    modules = []
    for name, child in model.named_children():
        params = sum(p.numel() for p in child.parameters())
        if params > 0:
            modules.append({"name": name, "params": params})

    modules.sort(key=lambda x: x["params"], reverse=True)

    total = sum(p.numel() for p in model.parameters())
    for m in modules:
        m["percentage"] = round(m["params"] / total * 100, 2) if total > 0 else 0
        m["params_str"] = format_params(m["params"])

    return modules[:top_n]


# ============================================================
# 主函数
# ============================================================

def explore(model_name, output_mode="full", config_only=False,
            trust_remote_code=False, token=None, max_depth=3):
    """主探索函数"""
    result = {"model_name": model_name, "error": None}

    # 1. 加载配置
    config = load_config(model_name, trust_remote_code, token)
    result["config"] = extract_key_config(config)
    result["moe_info"] = detect_moe(config)
    result["mla_info"] = detect_mla(config)
    result["quant_info"] = detect_quantization(config)

    sub_configs = detect_sub_configs(config)
    if sub_configs:
        result["sub_configs"] = {
            name: {k: v for k, v in sc.items() if k != "_full"}
            for name, sc in sub_configs.items()
        }

    # 模型卡片信息
    try:
        result["model_card"] = fetch_model_card(model_name, token)
    except Exception:
        pass

    # config 中的 transformers 版本
    config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
    tv = config_dict.get("transformers_version")
    if tv:
        result["config_transformers_version"] = tv

    if output_mode == "config" or config_only:
        estimated = estimate_params_from_config(config)
        if estimated:
            result["params"] = estimated
        # 即使 config-only 也构建合成树
        synthetic_tree = build_synthetic_tree(config, max_depth)
        if synthetic_tree:
            result["structure"] = synthetic_tree
            result["tree_text"] = "\n".join(tree_to_text(synthetic_tree))
            result["_synthetic_tree"] = True
        return result

    # 2. 尝试 meta device 加载
    try:
        model = load_model_meta(config, trust_remote_code)
        result["model_class"] = model.__class__.__name__
    except Exception as e:
        result["warning"] = f"Meta device 加载失败 ({e})，使用配置估算"
        estimated = estimate_params_from_config(config)
        if estimated:
            result["params"] = estimated
        # 构建合成树
        synthetic_tree = build_synthetic_tree(config, max_depth)
        if synthetic_tree:
            result["structure"] = synthetic_tree
            result["tree_text"] = "\n".join(tree_to_text(synthetic_tree))
            result["_synthetic_tree"] = True
        return result

    # 3. 结构信息
    if output_mode in ("structure", "full"):
        tree = build_tree(model, model.__class__.__name__, max_depth)
        result["structure"] = tree
        result["tree_text"] = "\n".join(tree_to_text(tree))

    # 4. 参数统计
    if output_mode in ("params", "full"):
        total = sum(p.numel() for p in model.parameters())
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        dtype_dist = get_dtype_distribution(model)

        size_bytes = 0
        for p in model.parameters():
            size_bytes += p.numel() * p.element_size()
        size_mb = size_bytes / (1024 * 1024)

        result["params"] = {
            "total": total,
            "total_str": format_params(total),
            "trainable": trainable,
            "trainable_str": format_params(trainable),
            "non_trainable": total - trainable,
            "size_mb": round(size_mb, 2),
            "size_str": f"{size_mb / 1024:.2f} GB" if size_mb > 1024 else f"{size_mb:.2f} MB",
            "dtype_distribution": {k: format_params(v) for k, v in dtype_dist.items()},
            "top_modules": get_top_modules(model),
        }

        # MoE 激活参数估算
        if result["moe_info"]["is_moe"]:
            moe = result["moe_info"]
            ec = moe.get("expert_counts", {})
            num_experts = ec.get("total_routed", 1)
            experts_per_tok = ec.get("per_token", 1)
            n_shared = ec.get("shared", 0)
            if num_experts > 1:
                ratio = experts_per_tok / num_experts
                result["params"]["moe_note"] = (
                    f"MoE 模型: {num_experts} 路由专家, "
                    f"每次激活 {experts_per_tok} 个"
                )
                if n_shared:
                    result["params"]["moe_note"] += f" + {n_shared} 共享专家"
                result["params"]["moe_note"] += f", 激活比例约 {ratio:.1%}"

    return result


def main():
    parser = argparse.ArgumentParser(description="HuggingFace 模型结构探索")
    parser.add_argument("model", help="模型名称或本地路径")
    parser.add_argument("--output", choices=["structure", "params", "full", "config"],
                        default="full", help="输出模式")
    parser.add_argument("--config-only", action="store_true",
                        help="仅加载配置，不下载权重")
    parser.add_argument("--trust-remote-code", action="store_true",
                        help="信任远程代码")
    parser.add_argument("--token", help="HuggingFace 认证 token")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="树结构最大深度")

    args = parser.parse_args()

    check_dependencies()

    try:
        result = explore(
            args.model,
            output_mode=args.output,
            config_only=args.config_only,
            trust_remote_code=args.trust_remote_code,
            token=args.token,
            max_depth=args.max_depth,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except OSError as e:
        error_msg = str(e)
        fix = None
        if "401" in error_msg or "gated" in error_msg.lower():
            fix = "这是一个需要认证的模型。运行: huggingface-cli login"
        elif "404" in error_msg:
            fix = "模型未找到，请检查模型名称是否正确"
        print(json.dumps({"error": error_msg, "fix": fix},
                         ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "fix": None},
                         ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
