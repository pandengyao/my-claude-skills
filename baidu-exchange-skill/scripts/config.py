#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载模块

提供 config.yaml 配置加载和 SKILL.md frontmatter 解析。
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any


def _load_config() -> Dict[str, Any]:
    """加载 config.yaml 配置文件"""
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


_CONFIG = _load_config()

# 缓存 skill name，避免每次上报都读文件
_SKILL_NAME_CACHE: Optional[str] = None


def _get_skill_name() -> Optional[str]:
    """
    从 SKILL.md frontmatter 中读取 name 字段

    Returns:
        str: skill 名称，读取失败返回 None
    """
    global _SKILL_NAME_CACHE
    if _SKILL_NAME_CACHE is not None:
        return _SKILL_NAME_CACHE

    try:
        skill_path = Path(__file__).parent.parent / 'SKILL.md'
        content = skill_path.read_text(encoding='utf-8')
        # 解析 YAML frontmatter（--- 包裹的部分）
        if content.startswith('---'):
            end = content.find('---', 3)
            if end != -1:
                frontmatter = yaml.safe_load(content[3:end])
                if isinstance(frontmatter, dict):
                    _SKILL_NAME_CACHE = frontmatter.get('name')
                    return _SKILL_NAME_CACHE
    except Exception:
        pass
    return None
