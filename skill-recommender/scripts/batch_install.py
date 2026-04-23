#!/usr/bin/env python3
"""
批量安装全部远端技能，支持冲突检测（比较本地与远端SKILL.md大小，保留更新的版本）。
"""
import sys
import os
import json
import urllib.request
import urllib.error
import zipfile
import tempfile
import shutil
from pathlib import Path

API_BASE_URL = "http://10.11.152.208:8101/api/v1/skills/package"

def detect_skills_directory():
    script_path = Path(__file__).resolve()
    skills_dir = script_path.parent.parent.parent
    return skills_dir

SKILLS_DIR = detect_skills_directory()

ALL_SKILLS = [
    "database-helper", "prompt-engineering-patterns", "creating-financial-models",
    "sequential-thinking", "arxiv-search", "web-research", "gemini", "chrome-devtools",
    "pdf", "mcp-builder", "git-commit-helper", "skill-creator", "docx", "typescript-write",
    "excel-analysis", "pptx", "dashboard-creator", "create-plan", "linear-implement",
    "playwright-mcp", "get-weather", "sql-optimization-patterns", "api-design-principles",
    "changelog-generator", "pr-reviewer", "presentation-builder", "research-synthesis",
    "skill_bmap_jsapi_gl", "skill_map_test_code", "icafe_card_assistant",
    "ipipe_pipeline_assistant", "ku-doc-manage", "create-pr", "go-codereviewer",
    "experiment-code-cleanup", "ec-live-log-refine", "code-generation",
    "programmer-cheerleader", "gdp2-sql-api", "prd-to-tech-design",
    "android-peer-pushedcode-reviewer", "baidu-vectordb", "go-code-analyzer",
    "iapi-manager", "frontend-design", "baidu-search", "daily-hot-news", "clawdbot-logs",
    "planning-with-files", "xiaohongshu", "baidu-scholar-search", "baidu-baike",
    "baidu-exchange-skill", "skill_comp_analysis", "so-send-message", "icafe-skill",
    "itest-assistant", "baidu-uuap-login", "processing-batch-crypto", "app-builder",
    "doc_check_solution", "shenghua_skill", "Payment_term_query", "skill_project_937",
    "weiyun_log_query", "aihc-kubeconfig", "wechat-article-to-markdown",
    "module-detailed-design", "terabox-server-prd-requirement-analysis",
    "terabox-server-task-planning", "integrating-probehub", "IM_group_manager",
    "lx-analyzer", "report-skill", "skill_customer-information-checking",
    "file-covert-to-markdown", "scan-log-analyzer", "hi_zhiban",
    "dam_db_table_change_skill", "skill_project_100", "skill_promo_text",
    "notebooklm-skill", "skill_iapi_api_to_code", "relay-oncall",
    "figma-image-processor", "dam-mapper-to-repository-sync",
    "dam-function-documentation-generator", "go-robustness-review-v2", "bdpan-storage",
    "zhiyanshi-assistant", "annotation-converter", "code-refactoring-and-optimization",
    "skill-daily-goals", "find_skills", "agent-teams-playbook", "acud-icon-components",
    "seui-figma-to-xml", "code-review-skill", "weekly-git-report", "claude-backup-migrate",
]

def get_download_url(skill_name):
    url = f"{API_BASE_URL}?skillIdentifier={skill_name}"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('code') == 200:
                return data.get('data', {}).get('bosUrl')
    except Exception:
        pass
    return None

def get_local_skill_md_size(skill_name):
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    if skill_md.exists():
        return skill_md.stat().st_size
    return 0

def get_remote_skill_md_size(zip_path, skill_name):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.filename.endswith('SKILL.md') and skill_name in info.filename:
                    return info.file_size
    except Exception:
        pass
    return 0

def download_file(url, dest):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(dest, 'wb') as f:
                f.write(response.read())
        return True
    except Exception:
        return False

def install_from_zip(zip_path, skill_name):
    install_dir = SKILLS_DIR / skill_name
    try:
        if install_dir.exists():
            shutil.rmtree(install_dir)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(SKILLS_DIR)
        return True
    except Exception:
        return False

def main():
    stats = {"installed": 0, "updated": 0, "skipped": 0, "failed": 0}
    total = len(ALL_SKILLS)

    print(f"开始批量安装 {total} 个技能到 {SKILLS_DIR}\n")

    for i, skill_name in enumerate(ALL_SKILLS, 1):
        print(f"[{i}/{total}] {skill_name} ... ", end="", flush=True)

        # Get download URL
        download_url = get_download_url(skill_name)
        if not download_url:
            print("FAILED (无法获取下载链接)")
            stats["failed"] += 1
            continue

        # Download to temp file
        temp_path = tempfile.mktemp(suffix='.zip')
        try:
            if not download_file(download_url, temp_path):
                print("FAILED (下载失败)")
                stats["failed"] += 1
                continue

            local_exists = (SKILLS_DIR / skill_name).exists()

            if local_exists:
                # Compare SKILL.md sizes
                local_size = get_local_skill_md_size(skill_name)
                remote_size = get_remote_skill_md_size(temp_path, skill_name)

                if remote_size > local_size:
                    if install_from_zip(temp_path, skill_name):
                        print(f"UPDATED (远端 {remote_size}B > 本地 {local_size}B)")
                        stats["updated"] += 1
                    else:
                        print("FAILED (安装失败)")
                        stats["failed"] += 1
                else:
                    print(f"SKIPPED (本地 {local_size}B >= 远端 {remote_size}B)")
                    stats["skipped"] += 1
            else:
                if install_from_zip(temp_path, skill_name):
                    print("INSTALLED")
                    stats["installed"] += 1
                else:
                    print("FAILED (安装失败)")
                    stats["failed"] += 1
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    print(f"\n{'='*50}")
    print(f"安装完成！统计：")
    print(f"  新安装: {stats['installed']}")
    print(f"  已更新: {stats['updated']}")
    print(f"  已跳过: {stats['skipped']}")
    print(f"  失败:   {stats['failed']}")
    print(f"  总计:   {total}")

if __name__ == "__main__":
    main()
