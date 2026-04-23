#!/usr/bin/env python3
"""
知识库文档查询工具 - 从 ku.baidu-int.com 获取文档并转换为 Markdown

完全独立，不依赖外部模块

使用方法:
    python query_ku_doc.py --url "https://ku.baidu-int.com/knowledge/xxx/DOC_ID"
    python query_ku_doc.py --doc-id "DOC_ID" --output ./output.md

功能:
    1. 调用知识库 API 获取文档 JSON
    2. 转换为 Markdown 格式
    3. 保存到指定路径
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from ku_json_to_md_converter import KuJsonToMarkdown as ExternalKuJsonToMarkdown


# ============================================================================
# 知识库 API 客户端（内联实现，无外部依赖）
# ============================================================================

class KuApiClient:
    """知识库开放 API 客户端 - 精简版（仅 query_content）"""

    BASE_URL_PERSONAL = 'http://10.11.152.208:8701/api/process/ku'
    BASE_URL_DIGITAL = 'https://ku.baidu-int.com/wiki/so'

    def __init__(self):
        """初始化客户端，优先使用个人认证"""
        self.token = self._get_token()
        self.ak = None
        self.sk = None
        self.base_url = self.BASE_URL_PERSONAL
        self.use_digital_auth = False

    def _get_token(self) -> str:
        """获取认证 Token，优先级：环境变量 > 登录文件"""
        # 从环境变量获取
        token = os.getenv('COMATE_AUTH_TOKEN')
        if token:
            return token.strip()

        # 从登录文件获取
        login_file = Path.home() / '.comate' / 'login'
        if login_file.exists():
            with open(login_file, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if token:
                    return token

        return ""

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            'Content-Type': 'application/json',
            'x-ac-Authorization': self.token
        }
        if self.use_digital_auth:
            headers['ak'] = self.ak
            headers['sk'] = self.sk
        return headers

    def query_content(self, doc_id: str = None, url: str = None) -> Dict[str, Any]:
        """
        查询文档正文内容

        Args:
            doc_id: 文档 ID
            url: 文档 URL

        Returns:
            dict: 文档内容数据
        """
        if not doc_id and not url:
            raise ValueError("doc_id 和 url 至少提供一个")

        data = {"showDocInfo": True}
        if doc_id:
            data["docId"] = doc_id
        if url:
            data["url"] = url

        return self._request("/ku/openapi/queryContent", data)

    def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送 HTTP 请求（使用标准库 urllib）"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))

            # 检查是否需要切换到数字员工认证
            response_code = result.get('code') or result.get('returnCode')
            if response_code in [403, 60413]:
                if not self.use_digital_auth:
                    self._switch_to_digital_auth()
                    return self._request(endpoint, data)

            return result

        except urllib.error.HTTPError as e:
            if e.code == 403 and not self.use_digital_auth:
                self._switch_to_digital_auth()
                return self._request(endpoint, data)
            # 尝试解析错误响应
            try:
                result = json.loads(e.read().decode('utf-8'))
                response_code = result.get('code') or result.get('returnCode')
                if response_code in [403, 60413] and not self.use_digital_auth:
                    self._switch_to_digital_auth()
                    return self._request(endpoint, data)
                return result
            except:
                raise
        except Exception as e:
            # Token 为空时尝试数字员工认证
            if not self.token and not self.use_digital_auth:
                self._switch_to_digital_auth()
                return self._request(endpoint, data)
            raise

    def _switch_to_digital_auth(self):
        """切换到数字员工身份认证"""
        print("\n" + "=" * 70)
        print("🔄 个人身份认证失败，尝试切换到数字员工身份认证...")
        print("=" * 70)
        print("\n💡 如需使用个人身份认证，请设置环境变量：")
        print("   export COMATE_AUTH_TOKEN=\"your-token\"")
        print("\n   Token获取: https://console.cloud.baidu-int.com/onetool/auth-manage/my-services")

        # 从环境变量读取 AK/SK
        self.ak = os.getenv('KU_AK', '')
        self.sk = os.getenv('KU_SK', '')

        if not self.ak or not self.sk:
            print("\n❌ 数字员工认证失败：未设置 KU_AK/KU_SK 环境变量")
            raise ValueError("认证失败：请设置 COMATE_AUTH_TOKEN 或 KU_AK/KU_SK 环境变量")

        self.base_url = self.BASE_URL_DIGITAL
        self.use_digital_auth = True
        print(f"✅ 已切换到数字员工身份认证\n")



def json_to_markdown(content, doc_title=""):
    """将知识库文档 JSON 转换为 Markdown（兼容旧接口）"""
    converter = ExternalKuJsonToMarkdown()
    # 如果传入的是完整响应，直接转换
    if isinstance(content, dict) and "result" in content:
        return converter.convert(content, add_title=True)
    # 如果只传内容，包装后转换
    return converter.convert({"content": content}, add_title=bool(doc_title))


# ============================================================================
# 主函数
# ============================================================================

def main():
    """ 主函数 """
    parser = argparse.ArgumentParser(description="知识库文档查询工具")
    parser.add_argument("--url", help="知识库文档完整 URL")
    parser.add_argument("--doc-id", help="文档 ID (URL 最后一部分)")
    parser.add_argument("--output", "-o", help="输出文件路径 (默认: ./PRD.md)")
    parser.add_argument("--json-output", help="JSON 输出路径 (可选)")
    parser.add_argument("--no-convert", action="store_true", help="只获取 JSON，不转换")

    args = parser.parse_args()

    # 提取 doc_id
    doc_id = args.doc_id
    if args.url and not doc_id:
        doc_id = args.url.rstrip("/").split("/")[-1]

    if not doc_id:
        print("❌ 错误: 请提供 --url 或 --doc-id")
        sys.exit(1)

    # 输出路径
    output_path = args.output or "./PRD.md"
    json_output = args.json_output or output_path.replace(".md", ".json")

    print(f"📄 正在获取文档: {doc_id}")

    try:
        # 调用 API
        client = KuApiClient()
        result = client.query_content(doc_id=doc_id)

        if not result.get("success"):
            print(f"❌ API 调用失败: {result.get('msg', '未知错误')}")
            sys.exit(1)

        # 提取内容
        content = result.get("result", {}).get("content", [])
        doc_info = result.get("result", {}).get("docInfo", {})
        doc_title = doc_info.get("title", "") or doc_info.get("name", "")

        # 保存 JSON
        json_dir = os.path.dirname(json_output)
        if json_dir:
            os.makedirs(json_dir, exist_ok=True)
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 已保存: {json_output}")

        if args.no_convert:
            print("⏭️  跳过 Markdown 转换")
            return

        # 转换为 Markdown
        converter = ExternalKuJsonToMarkdown(source_path=json_output)
        markdown = converter.convert(result, add_title=True)

        md_dir = os.path.dirname(output_path)
        if md_dir:
            os.makedirs(md_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✅ Markdown 已保存: {output_path}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
