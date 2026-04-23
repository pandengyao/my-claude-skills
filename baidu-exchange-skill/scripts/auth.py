#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证管理模块

封装 Ugate-Token 的获取、解析、刷新和本地缓存逻辑。
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict


class AuthManager:
    """Ugate-Token 认证管理器"""

    def __init__(self):
        self.agent_token: Optional[str] = None
        self.agent_token_refreshed: bool = False  # 标记是否已经尝试过刷新 ugate-token

    @staticmethod
    def _get_current_username() -> str:
        """
        获取当前用户名
        优先级：
        1. SANDBOX_USERNAME > BAIDU_CC_USERNAME 环境变量
        2. 如果环境变量未设置，引导用户输入用户名

        Returns:
            str: 用户名
        """
        username = os.environ.get('SANDBOX_USERNAME') or os.environ.get('BAIDU_CC_USERNAME')
        if username and username.strip():
            return username.strip()

        # 如果环境变量未设置，引导用户输入用户名
        print("ℹ️  请输入您的用户名")
        username = input("用户名: ").strip()
        if not username:
            raise ValueError("用户名不能为空")

        # 创建空的 token 文件，方便下次自动识别
        uuap_dir = Path.home() / ".config" / "uuap"
        uuap_dir.mkdir(parents=True, exist_ok=True)
        token_file_path = AuthManager._get_ugate_token_file_path(username)
        token_file_path.touch()
        print(f"✅ 已创建用户配置文件: {token_file_path}")
        print(
            "💡 提示: 您也可以通过设置环境变量"
            " SANDBOX_USERNAME 或 BAIDU_CC_USERNAME 来指定用户名"
        )

        return username

    @staticmethod
    def _get_ugate_token_file_path(username: str) -> Path:
        """
        获取 ugate token 文件路径

        Args:
            username: 用户名

        Returns:
            Path: token 文件路径
        """
        return Path.home() / ".config" / "uuap" / f".eac_ugate_token_{username}"

    @staticmethod
    def _parse_token_content(content: str) -> Optional[str]:
        """
        解析token内容，支持多种格式：
        1. 纯文本token
        2. JSON格式：{"token": "...", "permanent": true/false} 或 {"token": "...", "expires_at": ...}
        3. 多行格式：第一行是过期时间（permanent:...），第二行是token

        Args:
            content: token文件内容或SKILL输出内容

        Returns:
            str: 解析后的token字符串，如果解析失败返回 None
        """
        if not content:
            return None

        content = content.strip()

        # 尝试格式1：JSON格式
        try:
            token_data = json.loads(content)
            if isinstance(token_data, dict) and 'token' in token_data:
                token = token_data['token']

                # 新格式：检查 permanent 字段
                if 'permanent' in token_data:
                    is_permanent = token_data['permanent']
                    if is_permanent:
                        print(f"✅ 解析 token (JSON格式，永久有效)")
                    else:
                        print(f"✅ 解析 token (JSON格式，非永久)")
                    return token

                # 旧格式：检查 expires_at 字段（保持向后兼容）
                if 'expires_at' in token_data:
                    import time
                    expires_at = token_data['expires_at']
                    current_time = int(time.time())
                    if expires_at < current_time:
                        print(f"⚠️  Token 已过期 (expires_at: {expires_at}, current: {current_time})")
                        return None
                    print(f"✅ 解析 token (JSON格式，旧格式)")
                    return token

                # 如果没有 permanent 和 expires_at 字段，直接返回 token
                print(f"✅ 解析 token (JSON格式)")
                return token
        except json.JSONDecodeError:
            pass

        # 尝试格式2：多行格式（第一行是 EXPIRES_AT:...，第二行是token）
        if '\n' in content:
            lines = content.split('\n')
            if len(lines) >= 2:
                first_line = lines[0].strip()
                second_line = lines[1].strip()

                # 检查第一行是否包含 EXPIRES_AT
                if 'EXPIRES_AT:' in first_line.upper():
                    # 第二行是实际的token
                    if second_line:
                        print(f"✅ 解析 token (多行格式，过期时间: {first_line})")
                        return second_line

        # 格式3：纯文本token（单行）
        if content and not content.startswith('{'):
            print(f"✅ 解析 token (纯文本格式)")
            return content

        return None

    @staticmethod
    def _read_local_token(username: str) -> Optional[str]:
        """
        从本地文件读取 token

        Args:
            username: 用户名

        Returns:
            str: token 字符串，如果读取失败返回 None
        """
        try:
            token_file = AuthManager._get_ugate_token_file_path(username)
            if token_file.exists():
                with open(token_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return None

                    token = AuthManager._parse_token_content(content)
                    if token:
                        print(f"📄 从本地文件读取: {token_file}")
                        return token
        except Exception as e:
            print(f"⚠️  读取本地 token 文件失败: {e}", file=sys.stderr)

        return None

    @staticmethod
    def _write_local_token(username: str, token: str):
        """
        将 token 写入本地文件

        Args:
            username: 用户名
            token: token 字符串
        """
        try:
            token_file = AuthManager._get_ugate_token_file_path(username)
            token_file.parent.mkdir(parents=True, exist_ok=True)

            with open(token_file, 'w', encoding='utf-8') as f:
                f.write(token)

            print(f"✅ Token 已保存到本地文件: {token_file}")
        except Exception as e:
            print(f"⚠️  写入本地 token 文件失败: {e}", file=sys.stderr)

    def _get_agent_token(self, force_refresh: bool = False) -> str:
        """
        获取个人身份token
        认证逻辑:
        1. 获取当前用户名（从 SANDBOX_USERNAME 环境变量）
        2. 优先从本地文件 ~/.config/uuap/.eac_ugate_token_{username} 读取 token
        3. 如果本地文件不存在或 force_refresh=True，则调用 get-ugate-token SKILL 获取新 token

        Args:
            force_refresh: 是否强制刷新 token（认证失败时使用）

        Returns:
            str: Ugate Token
        """
        # 获取当前用户名
        username = self._get_current_username()

        # 如果不是强制刷新，先尝试从本地文件读取
        if not force_refresh:
            local_token = self._read_local_token(username)
            if local_token:
                return local_token

        # 本地文件不存在或强制刷新，调用 get-ugate-token SKILL 获取新 token
        try:
            if force_refresh:
                print(f"🔄 认证失败，重新调用 get-ugate-token SKILL 获取新 token...")
            else:
                print(f"🔄 本地 token 不存在，调用 get-ugate-token SKILL 获取新 token...")

            # 获取 get-ugate-token 脚本路径
            skill_dir = Path.home() / ".openclaw" / "skills" / "get-ugate-token"
            script_path = skill_dir / "getUgateToken.py"

            if not script_path.exists():
                project_skill_dir = Path(__file__).parent.parent.parent / "get-ugate-token"
                script_path = project_skill_dir / "getUgateToken.py"

            if not script_path.exists():
                print("\n" + "=" * 70)
                print("⚠️  未找到 get-ugate-token SKILL")
                print("=" * 70)
                print(f"\n检查路径: {skill_dir}")
                print(f"检查路径: {project_skill_dir}")
                print("\n💡 解决方案：下载并安装 get-ugate-token SKILL")
                print("\n请执行以下步骤：")
                print("1. 下载 Skill 包：")
                _zip_url = (
                    "https://bj.bcebos.com/baidu-cc/skills/"
                    "16dbe2c9-c2e2-444c-90e0-8ceac0d332a5/"
                    "get-ugate-token.zip"
                )
                print(f"   wget {_zip_url}")
                print("\n2. 解压并安装到以下任一目录：")
                print(f"   unzip get-ugate-token.zip -d {Path(__file__).parent.parent.parent}/")
                print("\n正在尝试自动下载安装...")
                print("=" * 70)

                # 尝试自动下载安装
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir)
                        zip_file = tmp_path / "get-ugate-token.zip"

                        print("📥 正在下载 get-ugate-token SKILL...")
                        _zip_url = (
                            "https://bj.bcebos.com/baidu-cc/"
                            "skills/16dbe2c9-c2e2-444c-90e0"
                            "-8ceac0d332a5/get-ugate-token.zip"
                        )
                        download_result = subprocess.run(
                            ["wget", "-O", str(zip_file), _zip_url],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )

                        if download_result.returncode != 0:
                            raise RuntimeError(f"下载失败: {download_result.stderr}")

                        print("✅ 下载完成")

                        target_dir = Path(__file__).parent.parent.parent
                        target_dir.mkdir(parents=True, exist_ok=True)

                        print(f"📦 正在解压到 {target_dir}...")
                        unzip_result = subprocess.run(
                            ["unzip", "-o", str(zip_file), "-d", str(target_dir)],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if unzip_result.returncode != 0:
                            raise RuntimeError(f"解压失败: {unzip_result.stderr}")

                        print("✅ 安装完成")

                        script_path = target_dir / "get-ugate-token" / "getUgateToken.py"
                        if not script_path.exists():
                            raise RuntimeError(f"安装后仍然找不到脚本: {script_path}")

                        print(f"✅ 找到脚本: {script_path}\n")
                        print("=" * 70 + "\n")

                except Exception as e:
                    print(f"\n❌ 自动安装失败: {e}")
                    print("\n" + "=" * 70)
                    print("💡 请手动执行以下命令安装：")
                    print(
                        "wget https://bj.bcebos.com/baidu-cc/"
                        "skills/16dbe2c9-c2e2-444c-90e0"
                        "-8ceac0d332a5/get-ugate-token.zip"
                    )
                    print(f"unzip get-ugate-token.zip -d {Path(__file__).parent.parent.parent}/")
                    print("\n安装完成后，请重新运行本命令")
                    print("=" * 70 + "\n")
                    raise RuntimeError("get-ugate-token SKILL 未安装，请先安装后重试")

            print(f"⏳ 正在等待认证（可能需要1-5分钟，请耐心等待）...\n")

            result = subprocess.run(
                [sys.executable, str(script_path), username],
                capture_output=True,
                text=True,
                timeout=300,
                env=os.environ.copy()
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                print("\n" + "=" * 70)
                print("❌ 获取个人身份token 失败")
                print("=" * 70 + "\n")
                raise RuntimeError(f"获取个人身份token失败: {error_msg}")

            output_content = result.stdout.strip()
            print("UUAP 返回最新内容: {}".format(output_content))
            token = self._parse_token_content(output_content)

            if not token:
                raise RuntimeError(
                    f"无法解析个人身份token，原始输出:\n"
                    f"{output_content}\n"
                    f"请检查 get-ugate-token SKILL 是否正常工作"
                )

            print(f"✅ 成功获取新 token")
            return token

        except subprocess.TimeoutExpired:
            print("\n" + "=" * 70)
            print("⏰ 认证超时（5分钟内未完成）")
            print("=" * 70 + "\n")
            raise RuntimeError("⏰ 认证超时（5分钟内未完成）")
        except Exception as e:
            print(f"⚠️  获取个人身份token失败: {e}", file=sys.stderr)
            raise

    def get_headers(self) -> Dict[str, str]:
        """
        构建请求头

        Returns:
            dict: HTTP请求头
        """
        headers = {
            'Content-Type': 'application/json'
        }

        if not self.agent_token:
            self.agent_token = self._get_agent_token()
            if self.agent_token is None:
                raise RuntimeError("个人身份认证失败（未找到 get-ugate-token SKILL）")
        headers['Ugate-Token'] = self.agent_token

        return headers

    def try_refresh_token(self) -> bool:
        """
        尝试刷新 token
        返回True表示刷新成功，False表示失败
        """
        if self.agent_token_refreshed:
            return False

        print("\n" + "=" * 70)
        print("🔄 个人身份认证失败，尝试重新获取 token...")
        print("=" * 70)
        try:
            self.agent_token = self._get_agent_token(force_refresh=True)
            if self.agent_token is None:
                print("⚠️  get-ugate-token SKILL 不可用")
                self.agent_token_refreshed = True
                return False
            else:
                self.agent_token_refreshed = True
                print("✅ Token 已刷新，重新尝试请求\n")
                print("=" * 70 + "\n")
                return True
        except Exception as e:
            print(f"⚠️  刷新 token 失败: {e}")
            self.agent_token_refreshed = True
            return False

    def print_auth_help(self):
        """打印认证配置帮助信息"""
        print("\n💡 认证配置帮助：\n")
        print("   个人身份认证（仅 Ugate-Token）：")
        print("     * Ugate-Token: 从本地文件读取，认证失败时自动调用 get-ugate-token SKILL 刷新")
        print("       - Token文件位置: ~/.config/uuap/.eac_ugate_token_{username}")
        print("       - username 从环境变量 SANDBOX_USERNAME 或 BAIDU_CC_USERNAME 获取")
        print("=" * 70 + "\n")
