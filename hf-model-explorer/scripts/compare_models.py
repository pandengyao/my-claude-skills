#!/usr/bin/env python3
"""HuggingFace 模型对比 - 对比两个模型的结构和参数差异"""

import argparse
import json
import sys
import os

# 添加当前目录到 path，复用 explore_model 的函数
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from explore_model import (
    check_dependencies, load_config, load_model_meta,
    extract_key_config, detect_moe, detect_mla,
    detect_quantization, detect_sub_configs,
    get_top_modules, format_params, estimate_params_from_config
)


def compare_configs(config_a, config_b):
    """对比两个配置"""
    dict_a = config_a.to_dict() if hasattr(config_a, "to_dict") else {}
    dict_b = config_b.to_dict() if hasattr(config_b, "to_dict") else {}

    all_keys = sorted(set(list(dict_a.keys()) + list(dict_b.keys())))

    diff = []
    same = []

    # 忽略无关紧要的 key
    skip_keys = {"_name_or_path", "transformers_version", "_commit_hash", "auto_map"}

    for key in all_keys:
        if key.startswith("_") and key in skip_keys:
            continue

        val_a = dict_a.get(key, "<不存在>")
        val_b = dict_b.get(key, "<不存在>")

        # 处理嵌套 dict（简化为字符串比较）
        if isinstance(val_a, dict) or isinstance(val_b, dict):
            if json.dumps(val_a, sort_keys=True, default=str) != json.dumps(val_b, sort_keys=True, default=str):
                diff.append({"key": key, "model_a": str(val_a)[:200], "model_b": str(val_b)[:200]})
            else:
                same.append({"key": key, "value": str(val_a)[:200]})
            continue

        if val_a != val_b:
            diff.append({"key": key, "model_a": val_a, "model_b": val_b})
        else:
            same.append({"key": key, "value": val_a})

    return diff, same


def compare_modules(model_a, model_b):
    """对比两个模型的模块结构"""
    def get_module_paths(model):
        paths = {}
        for name, module in model.named_modules():
            if name:
                params = sum(p.numel() for p in module.parameters(recurse=False))
                paths[name] = {
                    "type": module.__class__.__name__,
                    "own_params": params
                }
        return paths

    paths_a = get_module_paths(model_a)
    paths_b = get_module_paths(model_b)

    keys_a = set(paths_a.keys())
    keys_b = set(paths_b.keys())

    only_in_a = sorted(keys_a - keys_b)
    only_in_b = sorted(keys_b - keys_a)
    common = sorted(keys_a & keys_b)

    type_changes = []
    for key in common:
        if paths_a[key]["type"] != paths_b[key]["type"]:
            type_changes.append({
                "module": key,
                "model_a_type": paths_a[key]["type"],
                "model_b_type": paths_b[key]["type"]
            })

    return {
        "only_in_a": only_in_a[:30],  # 限制输出量
        "only_in_b": only_in_b[:30],
        "type_changes": type_changes[:20],
        "total_modules_a": len(paths_a),
        "total_modules_b": len(paths_b),
    }


def compare_params(model_a, model_b, name_a, name_b):
    """对比参数量"""
    total_a = sum(p.numel() for p in model_a.parameters())
    total_b = sum(p.numel() for p in model_b.parameters())

    top_a = {m["name"]: m for m in get_top_modules(model_a)}
    top_b = {m["name"]: m for m in get_top_modules(model_b)}
    all_module_names = sorted(set(list(top_a.keys()) + list(top_b.keys())))

    per_module = []
    for name in all_module_names:
        entry = {"module": name}
        if name in top_a:
            entry["model_a_params"] = top_a[name]["params"]
            entry["model_a_str"] = top_a[name]["params_str"]
        else:
            entry["model_a_params"] = 0
            entry["model_a_str"] = "-"
        if name in top_b:
            entry["model_b_params"] = top_b[name]["params"]
            entry["model_b_str"] = top_b[name]["params_str"]
        else:
            entry["model_b_params"] = 0
            entry["model_b_str"] = "-"
        per_module.append(entry)

    per_module.sort(key=lambda x: max(x.get("model_a_params", 0), x.get("model_b_params", 0)), reverse=True)

    return {
        "model_a_total": total_a,
        "model_a_total_str": format_params(total_a),
        "model_b_total": total_b,
        "model_b_total_str": format_params(total_b),
        "ratio": round(total_b / total_a, 2) if total_a > 0 else None,
        "per_module": per_module,
    }


def main():
    parser = argparse.ArgumentParser(description="对比两个 HuggingFace 模型")
    parser.add_argument("model_a", help="第一个模型名称或路径")
    parser.add_argument("model_b", help="第二个模型名称或路径")
    parser.add_argument("--config-only", action="store_true",
                        help="仅对比配置，不加载模型")
    parser.add_argument("--trust-remote-code", action="store_true",
                        help="信任远程代码")
    parser.add_argument("--token", help="HuggingFace 认证 token")

    args = parser.parse_args()
    check_dependencies()

    try:
        result = {
            "model_a": {"name": args.model_a},
            "model_b": {"name": args.model_b},
            "error": None,
        }

        # 加载配置
        config_a = load_config(args.model_a, args.trust_remote_code, args.token)
        config_b = load_config(args.model_b, args.trust_remote_code, args.token)

        result["model_a"]["config"] = extract_key_config(config_a)
        result["model_b"]["config"] = extract_key_config(config_b)
        result["model_a"]["moe_info"] = detect_moe(config_a)
        result["model_b"]["moe_info"] = detect_moe(config_b)
        result["model_a"]["mla_info"] = detect_mla(config_a)
        result["model_b"]["mla_info"] = detect_mla(config_b)
        result["model_a"]["quant_info"] = detect_quantization(config_a)
        result["model_b"]["quant_info"] = detect_quantization(config_b)

        sub_a = detect_sub_configs(config_a)
        sub_b = detect_sub_configs(config_b)
        if sub_a:
            result["model_a"]["sub_configs"] = {
                name: {k: v for k, v in sc.items() if k != "_full"}
                for name, sc in sub_a.items()
            }
        if sub_b:
            result["model_b"]["sub_configs"] = {
                name: {k: v for k, v in sc.items() if k != "_full"}
                for name, sc in sub_b.items()
            }

        # 配置对比
        config_diff, config_same = compare_configs(config_a, config_b)
        result["config_diff"] = config_diff
        result["config_same"] = config_same

        if not args.config_only:
            # 独立加载每个模型
            model_a = None
            model_b = None

            try:
                model_a = load_model_meta(config_a, args.trust_remote_code)
                result["model_a"]["class"] = model_a.__class__.__name__
            except Exception as e:
                result["model_a"]["warning"] = f"加载失败: {e}"
                est_a = estimate_params_from_config(config_a)
                if est_a:
                    result["model_a"]["estimated_params"] = est_a

            try:
                model_b = load_model_meta(config_b, args.trust_remote_code)
                result["model_b"]["class"] = model_b.__class__.__name__
            except Exception as e:
                result["model_b"]["warning"] = f"加载失败: {e}"
                est_b = estimate_params_from_config(config_b)
                if est_b:
                    result["model_b"]["estimated_params"] = est_b

            if model_a and model_b:
                result["param_comparison"] = compare_params(
                    model_a, model_b, args.model_a, args.model_b
                )
                result["structural_diff"] = compare_modules(model_a, model_b)
            else:
                # 部分比较：使用估算值
                est_a = estimate_params_from_config(config_a)
                est_b = estimate_params_from_config(config_b)
                if est_a or est_b:
                    result["param_comparison"] = {
                        "model_a_total_str": est_a["estimated_total_str"] if est_a else "N/A",
                        "model_b_total_str": est_b["estimated_total_str"] if est_b else "N/A",
                        "note": "一个或两个模型使用估算值"
                    }

        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    except OSError as e:
        error_msg = str(e)
        fix = None
        if "401" in error_msg or "gated" in error_msg.lower():
            fix = "需要认证的模型，请运行: huggingface-cli login"
        elif "404" in error_msg:
            fix = "模型未找到，请检查模型名称"
        print(json.dumps({"error": error_msg, "fix": fix},
                         ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "fix": None},
                         ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
