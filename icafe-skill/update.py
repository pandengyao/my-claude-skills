"""
iCafe Skill 卡片更新模块。

此模块提供更新卡片和评论的函数。
"""

from typing import Dict, Any, Optional, List, Tuple
from collections import Counter
from .client import ICafeClient
from .exceptions import ValidationError, MissingRequiredFieldsError
from .auth import load_config_file
from .models import Card, FieldGap, DetectRequiredFieldsResult
from .field_config import SpaceConfigCache
import warnings


# 字段名映射: Python 风格 -> 中文 API 字段
FIELD_MAPPING = {
    "title": "标题",
    "detail": "内容",
    "content": "内容",
    "assignee": "负责人",
    "owner": "负责人",
    "status": "流程状态",
    "flow_status": "流程状态",
    "priority": "优先级",
    "type": "类型",
    "问题原因": "Bug问题原因",
    "bug_reason": "Bug问题原因",
    "bug问题原因": "Bug问题原因",
}


def update_card(
    client: ICafeClient,
    space_id: str,
    card_id: str,
    fields: Dict[str, str],
    comment: Optional[str] = None,
    rel_issue: Optional[str] = None,
    rel_issue_operation: Optional[str] = None,
    operator: Optional[str] = None,
    is_check_status: Optional[bool] = None,
    rel_project: Optional[str] = None,
    rel_project_operation: Optional[str] = None,
    dry_run: bool = True,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    更新卡片字段。

    Args:
        client: 已认证的 iCafe 客户端
        space_id: 空间标识符
        card_id: 卡片 ID（数字或 "space-id" 格式）
        fields: 要更新的字段名和值字典
        comment: 可选评论，随更新一起添加
        rel_issue: 关联卡片ID，格式为"空间标识-卡片序号"
        rel_issue_operation: 关联操作类型，"add"（添加）或 "delete"（删除）
        operator: 修改人邮箱前缀，用于校验卡片权限，不填取认证用户
        is_check_status: 是否进行流程状态可达检查，默认 True
        rel_project: 关联项目编号
        rel_project_operation: 关联项目操作类型，"add"（添加）或 "delete"（删除）
        dry_run: 如果为 True，仅显示将要发送的内容（默认: True）
        config_path: 配置文件的可选路径，用于默认字段值

    Returns:
        成功时返回 API 响应，失败时返回包含错误信息的字典:
        - success: 是否成功
        - error: 错误消息
        - error_type: 错误类型（如 "required_fields_missing"）
        - required_fields: 缺失的必填字段列表
        - missing_fields_count: 缺失字段数量
        - message: 友好的错误提示

    Raises:
        ValidationError: 如果参数无效

    Example:
        >>> result = update_card(
        ...     client,
        ...     "test-space",
        ...     "123",
        ...     {"status": "开发中", "assignee": "lisi"},
        ...     comment="Updated status",
        ...     rel_issue="edc-scrum-12345",
        ...     rel_issue_operation="add",
        ...     operator="zhangsan",
        ...     is_check_status=False,
        ...     dry_run=True
        ... )
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")

    if not card_id or not card_id.strip():
        raise ValidationError("card_id cannot be empty")

    if fields is None:
        fields = {}

    if not isinstance(fields, dict):
        raise ValidationError("fields must be a dictionary")

    # 至少需要 fields、comment、rel_issue、rel_project 其中之一
    if not fields and not comment and not rel_issue and not rel_project:
        raise ValidationError("至少需要提供 fields、comment、rel_issue 或 rel_project 其中之一")

    # 校验关联项目参数配对
    if rel_project and not rel_project_operation:
        raise ValidationError("使用 rel_project 参数时必须同时指定 rel_project_operation (add/delete)")
    if rel_project_operation and not rel_project:
        raise ValidationError("rel_project_operation 需要配合 rel_project 参数使用")

    # Apply default field values based on Bug分析结论
    fields = _apply_default_fields(fields, config_path)

    # 解析 card_id
    from .query import _parse_card_id
    card_id = _parse_card_id(card_id)

    # 构建 API 格式的 fields 参数
    fields_params = _build_fields_params(fields, comment)

    # 添加关联卡片参数（单独的查询参数）
    rel_params = {}
    if rel_issue and rel_issue_operation:
        rel_params["relIssue"] = rel_issue
        rel_params["relIssueOperation"] = rel_issue_operation

    # 添加 operator 参数
    if operator:
        rel_params["operator"] = operator

    # 添加 isCheckStatus 参数
    if is_check_status is not None:
        rel_params["isCheckStatus"] = "true" if is_check_status else "false"

    # 添加关联项目参数
    if rel_project and rel_project_operation:
        rel_params["relProjectSequence"] = rel_project
        rel_params["relProjectOperation"] = rel_project_operation

    if dry_run:
        warnings.warn(
            "Running in DRY-RUN mode. No actual API call will be made.",
            UserWarning
        )
        return {
            "dry_run": True,
            "space_id": space_id,
            "card_id": card_id,
            "fields": fields,
            "comment": comment,
            "rel_issue": rel_issue,
            "rel_issue_operation": rel_issue_operation,
            "operator": operator,
            "is_check_status": is_check_status,
            "rel_project": rel_project,
            "rel_project_operation": rel_project_operation,
            "fields_params": fields_params,
            "endpoint": f"/api/spaces/{space_id}/cards/{card_id}",
            "warning": "DRY-RUN: This operation would modify the card. Not executed."
        }

    # 实际更新 - 解析 fields_params 并作为查询参数传递
    # 格式: "fields=字段名=值&fields=字段名=值&comment=评论"
    params_dict = {}
    if '&' in fields_params:
        for pair in fields_params.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                if key in params_dict:
                # 处理同一键的多个值（如 fields）
                    if isinstance(params_dict[key], list):
                        params_dict[key].append(value)
                    else:
                        params_dict[key] = [params_dict[key], value]
                else:
                    params_dict[key] = value
    else:
        # 单个字段
        if '=' in fields_params:
            key, value = fields_params.split('=', 1)
            params_dict[key] = value

    # 添加关联卡片参数到查询参数
    params_dict.update(rel_params)

    try:
        response = client.post(
            f"/api/spaces/{space_id}/cards/{card_id}",
            params=params_dict
        )
        return response
    except Exception as e:
        # 更新失败时，检测是否是必填字段缺失导致的错误
        error_msg = str(e)
        required_fields = _extract_required_fields_from_error(error_msg)

        if required_fields:
            # 获取当前卡片状态（如果可能）
            current_status = None
            target_status = None
            if "status" in fields:
                target_status = fields.get("status") or fields.get("流程状态")
            # 尝试从 error_msg 中提取状态信息
            if "无法到达该流程状态" in error_msg:
                import re
                status_match = re.search(r'(\[状态:([^\]]+)\]|状态[：:]\s*([^\s]+))', error_msg)
                if status_match:
                    current_status = status_match.group(1) or status_match.group(2)

            # 抛出 MissingRequiredFieldsError
            raise MissingRequiredFieldsError(
                message="无法到达该流程状态，还有必填字段没有填写",
                missing_fields=required_fields,
                current_status=current_status,
                target_status=target_status,
                field_options=None
            ) from e
        if "无法流转到该流程状态" in error_msg:
            raise ValidationError(
                f"无法流转到该流程状态：{error_msg}"
            )
        else:
            # 其他类型的错误，重新抛出
            raise


def update_comment(
    client: ICafeClient,
    space_id: str,
    comment_id: str,
    content: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    更新现有评论。

    Args:
        client: 已认证的 iCafe 客户端
        space_id: 空间标识符
        comment_id: 评论 ID
        content: 新评论内容
        dry_run: 如果为 True，仅显示将要发送的内容（默认: True）

    Returns:
        包含更新结果或 dry-run 预览的字典

    Raises:
        ValidationError: 如果参数无效
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    if not comment_id or not comment_id.strip():
        raise ValidationError("comment_id cannot be empty")
    
    if not content or not content.strip():
        raise ValidationError("content cannot be empty")
    
    payload = {
        "content": content.strip()
    }
    
    if dry_run:
        warnings.warn(
            "Running in DRY-RUN mode. No actual API call will be made.",
            UserWarning
        )
        return {
            "dry_run": True,
            "space_id": space_id,
            "comment_id": comment_id,
            "payload": payload,
            "endpoint": f"/api/v2/space/{space_id}/issue/comment/{comment_id}"
        }

    # 实际更新
    path = f"/api/v2/space/{space_id}/issue/comment/{comment_id}"
    response = client.post(path, json=payload)

    return response


def _build_fields_params(fields: Dict[str, str], comment: Optional[str] = None) -> str:
    """
    构建 API 格式的字段参数字符串。

    格式: "fields=字段名=值&fields=字段名=值&comment=评论"

    Args:
        fields: 字段名和值字典
        comment: 可选评论

    Returns:
        格式化后的参数字符串
    """
    parts = []
    
    for key, value in fields.items():
        # 将 Python 风格的字段名映射为中文 API 字段
        api_field = FIELD_MAPPING.get(key.lower(), key)
        parts.append(f"fields={api_field}={value}")
    
    if comment:
        parts.append(f"comment={comment}")
    
    return "&".join(parts)


def preview_update(
    space_id: str,
    card_id: str,
    fields: Dict[str, str],
    comment: Optional[str] = None,
    rel_issue: Optional[str] = None,
    rel_issue_operation: Optional[str] = None,
    operator: Optional[str] = None,
    is_check_status: Optional[bool] = None,
    rel_project: Optional[str] = None,
    rel_project_operation: Optional[str] = None
) -> str:
    """
    预览更新操作会是什么样子的。

    这是一个辅助函数，显示将进行的精确 API 调用，
    不需要客户端实例。

    Args:
        space_id: 空间标识符
        card_id: 卡片 ID
        fields: 字段名和值字典
        comment: 可选评论
        rel_issue: 关联卡片ID
        rel_issue_operation: 关联操作类型
        operator: 修改人邮箱前缀
        is_check_status: 是否进行流程状态可达检查
        rel_project: 关联项目编号
        rel_project_operation: 关联项目操作类型

    Returns:
        格式化后的预览字符串
    """
    from .query import _parse_card_id
    card_id = _parse_card_id(card_id)
    
    fields_params = _build_fields_params(fields, comment)

    # 构建关联卡片参数
    rel_params_str = ""
    if rel_issue and rel_issue_operation:
        rel_params_str += f"&relIssue={rel_issue}&relIssueOperation={rel_issue_operation}"

    # 构建 operator 参数
    if operator:
        rel_params_str += f"&operator={operator}"

    # 构建 isCheckStatus 参数
    if is_check_status is not None:
        rel_params_str += f"&isCheckStatus={'true' if is_check_status else 'false'}"

    # 构建关联项目参数
    if rel_project and rel_project_operation:
        rel_params_str += f"&relProjectSequence={rel_project}&relProjectOperation={rel_project_operation}"

    url = f"http://icafeapi.baidu-int.com/api/spaces/{space_id}/cards/{card_id}"
    full_url = f"{url}?u={{username}}&pw={{password}}&{fields_params}{rel_params_str}"

    preview = f"""
Update Preview
==============
Space ID: {space_id}
Card ID: {card_id}

Fields to update:
"""
    for key, value in fields.items():
        api_field = FIELD_MAPPING.get(key.lower(), key)
        preview += f"  - {api_field} = {value}\n"

    if comment:
        preview += f"\nComment: {comment}\n"

    if rel_issue and rel_issue_operation:
        preview += f"\nRelated Issue:\n"
        preview += f"  - Card ID: {rel_issue}\n"
        preview += f"  - Operation: {rel_issue_operation}\n"

    if operator:
        preview += f"\nOperator: {operator}\n"

    if is_check_status is not None:
        preview += f"\nCheck Status: {'true' if is_check_status else 'false'}\n"

    if rel_project and rel_project_operation:
        preview += f"\nRelated Project:\n"
        preview += f"  - Project ID: {rel_project}\n"
        preview += f"  - Operation: {rel_project_operation}\n"

    preview += f"\nAPI Endpoint:\n  POST {url}\n"
    preview += f"\nQuery Parameters:\n  {fields_params}{rel_params_str}\n"

    return preview


def _apply_default_fields(
    fields: Dict[str, str],
    config_path: Optional[str] = None
) -> Dict[str, str]:
    """
    应用基于 Bug分析结论 配置的默认字段值。

    如果 fields 字典中包含 'Bug分析结论'，并且其值匹配配置文件 'fileds' 部分的键，
    则自动填充该状态的默认字段值。

    Args:
        fields: Dictionary of field names and values to update
        config_path: Optional path to config file (default: config/config.yaml)

    Returns:
        Updated fields dictionary with default values applied
    """
    # 检查 fields 中是否包含 Bug分析结论
    bug_conclusion_key = None
    bug_conclusion_value = None

    # 检查 Bug分析结论 的各种可能的键名
    for key in ["Bug分析结论", "bug_conclusion", "bugConclusion"]:
        if key in fields:
            bug_conclusion_key = key
            bug_conclusion_value = fields[key]
            break

    if not bug_conclusion_value:
        return fields

    # 加载配置文件
    if config_path is None:
        config_path = "config/config.yaml"

    try:
        config = load_config_file(config_path)
    except (ValidationError, FileNotFoundError):
        # 配置文件未找到或无效，返回原始字段
        return fields

    # 获取 fields 配置部分
    fields_config = config.get("fields", {})
    if not isinstance(fields_config, dict):
        return fields

    # 在 fields 配置中查找匹配的状态
    # 配置结构为: fields.Bug分析结论.<status>.<field>: <value>
    bug_analysis_config = fields_config.get("Bug分析结论", {})
    if not isinstance(bug_analysis_config, dict):
        return fields

    # 查找与 bug_conclusion_value 匹配的状态
    default_fields = None
    for status, status_config in bug_analysis_config.items():
        if status == bug_conclusion_value and isinstance(status_config, dict):
            default_fields = status_config
            break

    if not default_fields:
        return fields

    # 创建字段的副本，避免修改原始字典
    result = fields.copy()

    # 仅当用户未设置该字段时才应用默认值
    for field_name, field_value in default_fields.items():
        if field_name not in result:
            result[field_name] = field_value

    return result


def _extract_field_value(card: Card, field_name: str, field_display: str) -> Any:
    """
    从 Card 对象中提取字段值。

    同时检查标准字段（如 assignee、status 等）和 extra_fields。

    Args:
        card: 要提取值的 Card 对象
        field_name: 内部字段名
        field_display: 显示字段名（如 "Bug问题原因"）

    Returns:
        字段值，如果未找到则返回 None
    """
    # 首先检查标准 Card 字段
    standard_fields = {
        "title": "title",
        "detail": "detail",
        "type": "type",
        "status": "status",
        "assignee": "assignee",
        "priority": "priority",
        "creator": "creator",
        "plan": "plan",
    }

    # 检查 field_name 是否匹配标准字段
    for std_name, std_attr in standard_fields.items():
        if field_name and field_name.lower() == std_name.lower():
            return getattr(card, std_attr, None)

    # 使用 field_display 检查 extra_fields（常用于中文字段）
    if field_display in card.extra_fields:
        return card.extra_fields[field_display]

    # 同时使用 field_name 检查 extra_fields
    if field_name in card.extra_fields:
        return card.extra_fields[field_name]

    # 在 properties 字典中检查（用于自定义字段）
    if "properties" in card.extra_fields and isinstance(card.extra_fields["properties"], dict):
        if field_display in card.extra_fields["properties"]:
            return card.extra_fields["properties"][field_display]
        if field_name in card.extra_fields["properties"]:
            return card.extra_fields["properties"][field_name]

    return None


def _analyze_field_from_samples(
    sample_cards: List[Card],
    field_name: str,
    field_display: str
) -> Dict[str, Any]:
    """
    分析样本卡片中的字段值。

    Args:
        sample_cards: 样本卡片列表
        field_name: 内部字段名
        field_display: 显示字段名

    Returns:
        包含以下内容的字典:
            - values: 找到的所有值列表
            - most_common: 最常见的值
            - unique_values: 唯一值集合
            - consistency_ratio: 最常见值计数与总数的比率
            - fill_ratio: 填写比例（有值的样本数 / 总样本数）
            - filled_count: 有值的样本数量
    """
    values = []
    filled_count = 0  # 有值的样本数量
    for card in sample_cards:
        value = _extract_field_value(card, field_name, field_display)
        # 跳过 None 和空字符串
        if value is None or value == "":
            continue
        # 跳过字典值（Counter 无法处理）
        if isinstance(value, dict):
            continue
        # 处理列表值（如 select_list 字段）
        if isinstance(value, list):
            # 如果列表为空则跳过
            if not value:
                continue
            # 过滤列表中的空字符串
            list_values = [v for v in value if not isinstance(v, (dict, list)) and v != ""]
            if list_values:
                values.extend(list_values)
                filled_count += 1
            else:
                continue
        # 仅添加可哈希的非空值
        elif isinstance(value, (str, int, float, bool)):
            # 额外过滤空字符串（确保）
            if isinstance(value, str) and value.strip() == "":
                continue
            values.append(value)
            filled_count += 1

    # 过滤掉任何剩余的不可哈希值和空字符串
    values = [v for v in values if isinstance(v, (str, int, float, bool)) and not (isinstance(v, str) and v.strip() == "")]

    # 计算填写比例（有值的样本数 / 总样本数）
    total_samples = len(sample_cards)
    fill_ratio = filled_count / total_samples if total_samples > 0 else 0.0

    if not values:
        return {
            "values": [],
            "most_common": None,
            "unique_values": set(),
            "consistency_ratio": 0.0,
            "fill_ratio": fill_ratio,
            "filled_count": filled_count,
        }

    # 统计出现次数
    counter = Counter(values)
    most_common = counter.most_common(1)[0][0] if counter else None

    # 计算一致性比率（有多少样本具有最常见的值）
    consistency_ratio = counter[most_common] / len(values) if most_common else 0.0

    return {
        "values": values,
        "most_common": most_common,
        "unique_values": set(values),
        "consistency_ratio": consistency_ratio,
        "fill_ratio": fill_ratio,
        "filled_count": filled_count,
    }


def _calculate_confidence(
    sample_count: int,
    max_sample_cards: int,
    field_consistencies: List[float]
) -> float:
    """
    根据样本数量和字段一致性计算置信度分数。

    Args:
        sample_count: 找到的样本卡片数量
        max_sample_cards: 请求的样本卡片最大数量
        field_consistencies: 每个字段的一致性比率列表

    Returns:
        0.0 到 1.0 之间的置信度分数
    """
    # 基于样本数量的基础置信度
    if sample_count == 0:
        count_confidence = 0.0
    else:
        count_confidence = min(sample_count / max_sample_cards, 1.0)

    # 各字段的平均一致性
    if field_consistencies:
        avg_consistency = sum(field_consistencies) / len(field_consistencies)
    else:
        avg_consistency = 0.0

    # 结合两个因素（加权平均）
    # 样本数量更重要（70%），一致性占（30%）
    confidence = 0.7 * count_confidence + 0.3 * avg_consistency

    return round(confidence, 2)


def _extract_required_fields_from_error(error_message: str) -> List[str]:
    """
    从 iCafe 错误消息中提取必填字段名。

    Args:
        error_message: iCafe API 返回的错误消息

    Returns:
        必填字段名列表
    """
    import re

    # 匹配模式: "还有必填字段没有填写: 字段名1, 字段名2, 字段名3"
    # 匹配冒号后的所有内容，然后按逗号分割
    pattern = r'还有必填字段没有填写[:：]\s*(.+?)(?:\s*[,\，]\s*(.+?))*$'
    match = re.search(pattern, error_message)
    if match:
        # 使用 group(1) 捕获整个字段部分
        all_fields = match.group(1).strip()

        # 按逗号分割（英文和中文）
        raw_fields = re.split(r'[,，\s]+', all_fields)

        # 清理和过滤字段
        fields = []
        for field in raw_fields:
            field = field.strip()
            # 移除尾部的 JSON 伪影
            if '"' in field:
                field = field.split('"')[0]
            # 移除任何尾部标点符号
            field = field.rstrip(',，.。;；')
            if field and field not in fields:
                fields.append(field)

        return fields

    # 备选模式: "required field X is missing"
    alt_pattern = r'required\s+field\s+(.+?)\s+is\s+missing'
    match = re.search(alt_pattern, error_message, re.IGNORECASE)
    if match:
        return [match.group(1).strip()]

    return []


def detect_required_fields(
    client: ICafeClient,
    space_id: str,
    card_id: str,
    target_status: str,
    max_sample_cards: int = 3
) -> DetectRequiredFieldsResult:
    """
    检测将卡片流转到目标状态时需要填写的必填字段。
    完全依靠样本卡片来推断必填字段。

    Args:
        client: 已认证的 iCafe 客户端
        space_id: 空间标识符
        card_id: 要更新的卡片 ID（格式: "123" 或 "space-123"）
        target_status: 目标流程状态
        max_sample_cards: 查询的样本卡片最大数量

    Returns:
        包含分析结果的 DetectRequiredFieldsResult

    Raises:
        ValidationError: 如果参数无效
    """
    # 输入验证
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")

    if not card_id or not card_id.strip():
        raise ValidationError("card_id cannot be empty")

    if not target_status or not target_status.strip():
        raise ValidationError("target_status cannot be empty")

    # 解析 card_id
    from .query import _parse_card_id
    card_id = _parse_card_id(card_id)

    # 导入查询函数
    from .query import get_card, list_cards

    warnings = []

    # 1. 获取当前卡片信息
    current_card = get_card(client, space_id, card_id)
    current_status = current_card.status or ""
    issue_type = current_card.type or ""

    # 1.5. 获取字段配置（用于判断字段类型）
    field_cache = SpaceConfigCache(client)
    try:
        field_configs = field_cache.get_fields_for_type(space_id, issue_type)
    except Exception as e:
        field_configs = {}
        warnings.append(f"Could not fetch field configurations: {e}")

    # 2. 查询目标状态样本卡片
    iql = f'负责人 = currentUser AND 最后修改人 = currentUser AND 类型="{issue_type}" AND 流程状态="{target_status}"'
    try:
        sample_card_list = list_cards(client, space_id, iql=iql, max_records=str(max_sample_cards), order='lastModifiedTime', is_desc=True)
        sample_card_ids = [card.sequence for card in sample_card_list]
        sample_card_count = len(sample_card_ids)
    except Exception as e:
        sample_card_list = []
        sample_card_ids = []
        sample_card_count = 0
        warnings.append(f"Could not query sample cards: {e}")

    # 3. 获取样本卡片详细信息
    sample_cards: List[Card] = []
    for sc_id in sample_card_ids:
        try:
            sample_card = get_card(client, space_id, sc_id)
            sample_cards.append(sample_card)
        except Exception as e:
            warnings.append(f"Could not fetch sample card {sc_id}: {e}")

    # 4. 从样本中分析所有字段以查找常用填充字段
    # 完全依靠样本来推断必填字段
    required_fields: List[FieldGap] = []
    fields_needing_fill: List[FieldGap] = []
    fields_unchanged: List[FieldGap] = []
    field_consistencies: List[float] = []

    # 从样本卡片中收集所有字段
    all_fields_in_samples = set()
    for card in sample_cards:
        for field_name in card.extra_fields.keys():
            # 如果是 properties 字段，展开其中的键
            if field_name == "properties" and isinstance(card.extra_fields.get("properties"), dict):
                for prop_key in card.extra_fields["properties"].keys():
                    all_fields_in_samples.add(prop_key)
            else:
                all_fields_in_samples.add(field_name)
        # 添加标准字段
        standard_field_map = {
            "title": "标题",
            "detail": "内容",
            "type": "类型",
            "status": "流程状态",
            "assignee": "负责人",
            "priority": "优先级",
        }
        for std_name, display_name in standard_field_map.items():
            if hasattr(card, std_name):
                all_fields_in_samples.add(display_name)

    # 需要过滤的系统字段（内部使用，不应暴露给用户）
    SYSTEM_FIELDS = {
        "resolveTime", "spaceName", "isFinishedStatus", "lastModifiedUser",
        "projectName", "relProjects", "Comments", "Assignee"
    }

    # 对于样本中的每个字段，检查是否被普遍填写
    for field_display in all_fields_in_samples:
        # 跳过标准字段
        if field_display in ["标题", "内容", "类型", "流程状态", "负责人", "优先级"]:
            continue

        # 跳过系统字段
        if field_display in SYSTEM_FIELDS:
            continue

        # 获取字段类型配置
        field_config = field_configs.get(field_display)
        field_type = field_config.type if field_config else "string"

        # 分析此字段
        sample_analysis = _analyze_field_from_samples(sample_cards, "", field_display)
        fill_ratio = sample_analysis["fill_ratio"]

        # 所有字段类型统一使用填写比例判断
        # 如果至少 80% 的样本填写了该字段，则认为是必填的
        # 提高阈值以避免误判经常填写但实际非必填的字段
        if fill_ratio >= 0.8:
            field_consistencies.append(fill_ratio)

            # 检查当前卡片是否有此字段
            current_value = _extract_field_value(current_card, "", field_display)

            # 过滤空字符串判断是否需要填写
            if current_value is None:
                needs_fill = True
            elif isinstance(current_value, str) and current_value.strip() == "":
                needs_fill = True
            elif isinstance(current_value, list) and len(current_value) == 0:
                needs_fill = True
            else:
                needs_fill = False

            # 根据字段类型生成建议值
            if field_type == "date_time":
                # 日期字段使用今天的日期
                from datetime import datetime
                suggestion = datetime.now().strftime("%Y-%m-%d")
            elif sample_analysis["most_common"]:
                # 有最常见值则使用
                suggestion = str(sample_analysis["most_common"])
            else:
                # 无最常见值则使用空字符串占位
                suggestion = ""

            field_gap = FieldGap(
                field_display=field_display,
                field_name=field_display,
                field_type=field_type,
                is_required=True,
                current_value=current_value,
                sample_values=sample_analysis["values"],
                most_common_value=sample_analysis["most_common"],
                options=[],
                default_value=None,
                suggestion=suggestion,
                needs_fill=needs_fill,
                reason=f"Inferred required field from samples (filled in {fill_ratio:.0%} of sample cards)",
            )

            required_fields.append(field_gap)

            if field_gap.needs_fill:
                fields_needing_fill.append(field_gap)
            else:
                fields_unchanged.append(field_gap)

    # 5. 构建结果
    can_transition = len(fields_needing_fill) == 0
    confidence = _calculate_confidence(
        sample_card_count,
        max_sample_cards,
        field_consistencies
    )

    # 构建推荐字段
    recommended_fields = {}
    for field in fields_needing_fill:
        if field.suggestion and not field.suggestion.startswith("("):
            recommended_fields[field.field_name] = field.suggestion

    # 如果没有找到样本卡片，添加警告
    if sample_card_count == 0:
        warnings.append(
            "No sample cards found for the target status. "
            "Cannot provide accurate field suggestions."
        )

    return DetectRequiredFieldsResult(
        space_id=space_id,
        card_id=card_id,
        current_status=current_status,
        target_status=target_status,
        issue_type=issue_type,
        can_transition=can_transition,
        required_fields=required_fields,
        fields_needing_fill=fields_needing_fill,
        fields_unchanged=fields_unchanged,
        sample_card_ids=sample_card_ids,
        sample_card_count=sample_card_count,
        total_required_fields=len(required_fields),
        fields_to_fill_count=len(fields_needing_fill),
        confidence=confidence,
        recommended_fields=recommended_fields,
        warnings=warnings,
    )