"""
Helper functions for creating and updating cards with field assistance.

This module provides interactive helpers that guide users through
card creation and modification by showing required fields and their options.
"""

import logging
from typing import Dict, List, Optional, Any
from .client import ICafeClient
from .field_config import SpaceConfigCache, FieldConfig
from .models import Issue
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


def get_required_fields_info(
    client: ICafeClient,
    space_id: str,
    issue_type: str,
    config_cache: Optional[SpaceConfigCache] = None
) -> Dict[str, Any]:
    """
    Get information about required fields for an issue type.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_type: Issue type name
        config_cache: Optional configuration cache
        
    Returns:
        Dictionary with required fields information
        
    Example:
        >>> info = get_required_fields_info(client, "edc-scrum", "Bug")
        >>> print("Required fields:")
        >>> for field in info['required_fields']:
        ...     print(f"  - {field['prompt']}")
    """
    if config_cache is None:
        config_cache = SpaceConfigCache(client)
    
    type_config = config_cache.get_type_with_fields(space_id, issue_type)
    
    required_fields = []
    for field in type_config.get_required_fields():
        field_info = {
            'name': field.name,
            'display': field.display,
            'type': field.type,
            'required': field.required,
            'prompt': field.get_prompt(),
            'default_value': field.default_value,
            'options': field.value_items if field.type in [
                'select_list', 'select_list_multiple', 'radio_field'
            ] else None
        }
        required_fields.append(field_info)
    
    return {
        'issue_type': issue_type,
        'type_id': type_config.type_id,
        'required_fields': required_fields,
        'required_count': len(required_fields)
    }


def print_required_fields(
    client: ICafeClient,
    space_id: str,
    issue_type: str,
    config_cache: Optional[SpaceConfigCache] = None
):
    """
    Print required fields information to console.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_type: Issue type name
        config_cache: Optional configuration cache
    """
    info = get_required_fields_info(client, space_id, issue_type, config_cache)
    
    print(f"\n{'='*70}")
    print(f"必填字段列表 - {issue_type} ({space_id})")
    print(f"{'='*70}")
    print(f"共 {info['required_count']} 个必填字段:\n")
    
    for i, field in enumerate(info['required_fields'], 1):
        print(f"{i}. {field['prompt']}")
        if field['options'] and len(field['options']) <= 20:
            print(f"   可选值:")
            for opt in field['options']:
                print(f"     - {opt}")
        print()
    
    print(f"{'='*70}\n")


def validate_card_data(
    client: ICafeClient,
    space_id: str,
    issue_type: str,
    title: str,
    detail: str,
    fields: Dict[str, Any],
    config_cache: Optional[SpaceConfigCache] = None
) -> Dict[str, Any]:
    """
    Validate card data before creation.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_type: Issue type name
        title: Card title
        detail: Card detail
        fields: Dictionary of field values
        config_cache: Optional configuration cache
        
    Returns:
        Validation result with errors and warnings
        
    Example:
        >>> result = validate_card_data(
        ...     client, "edc-scrum", "Bug",
        ...     title="Test Bug",
        ...     detail="Bug description",
        ...     fields={"优先级": "P1-High", "负责人": "zhangsan"}
        ... )
        >>> if result['valid']:
        ...     print("✓ Validation passed")
        >>> else:
        ...     print("Errors:", result['errors'])
    """
    if config_cache is None:
        config_cache = SpaceConfigCache(client)
    
    type_config = config_cache.get_type_with_fields(space_id, issue_type)
    
    # Prepare fields for validation
    fields_data = fields.copy()
    fields_data["标题"] = title
    fields_data["内容"] = detail
    
    # Validate
    errors = type_config.validate_fields(fields_data)
    
    # Check for warnings (optional fields)
    warnings = []
    optional_fields = type_config.get_optional_fields()
    for field in optional_fields:
        if field.display not in fields_data and field.name not in fields_data:
            warnings.append(f"可选字段未填写: {field.display}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'missing_required': [e for e in errors if '缺少必填字段' in e],
        'invalid_values': [e for e in errors if '缺少必填字段' not in e]
    }


def build_issue_with_guidance(
    client: ICafeClient,
    space_id: str,
    issue_type: str,
    title: str,
    detail: str,
    creator: str,
    fields: Optional[Dict[str, Any]] = None,
    show_hints: bool = True,
    config_cache: Optional[SpaceConfigCache] = None
) -> Issue:
    """
    Build an Issue object with field validation and guidance.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_type: Issue type name
        title: Card title
        detail: Card detail
        creator: Creator username
        fields: Dictionary of field values
        show_hints: Whether to print hints about missing fields
        config_cache: Optional configuration cache
        
    Returns:
        Issue object ready for creation
        
    Raises:
        ValidationError: If required fields are missing or invalid
        
    Example:
        >>> issue = build_issue_with_guidance(
        ...     client, "edc-scrum", "Bug",
        ...     title="Test Bug",
        ...     detail="Description",
        ...     creator="zhangsan",
        ...     fields={"优先级": "P1-High", "负责人": "zhangsan"},
        ...     show_hints=True
        ... )
    """
    if fields is None:
        fields = {}
    
    # Validate
    validation = validate_card_data(
        client, space_id, issue_type, title, detail, fields, config_cache
    )
    
    if show_hints:
        if validation['warnings']:
            print("\n💡 提示：以下可选字段未填写：")
            for warning in validation['warnings'][:5]:  # Show first 5
                print(f"  - {warning}")
            if len(validation['warnings']) > 5:
                print(f"  ... 还有 {len(validation['warnings']) - 5} 个可选字段")
            print()
    
    if not validation['valid']:
        error_msg = "字段验证失败:\n"
        if validation['missing_required']:
            error_msg += "\n缺少必填字段:\n"
            for err in validation['missing_required']:
                error_msg += f"  - {err}\n"
        if validation['invalid_values']:
            error_msg += "\n字段值无效:\n"
            for err in validation['invalid_values']:
                error_msg += f"  - {err}\n"
        
        if show_hints:
            print("\n📋 获取完整字段列表，请运行:")
            print(f'  print_required_fields(client, "{space_id}", "{issue_type}")\n')
        
        raise ValidationError(error_msg)
    
    # Build Issue
    issue = Issue(
        title=title,
        detail=detail,
        type=issue_type,
        creator=creator,
        fields=fields
    )
    
    if show_hints:
        print(f"✓ Issue 创建成功，已通过字段验证")
    
    return issue


def list_available_types(
    client: ICafeClient,
    space_id: str,
    config_cache: Optional[SpaceConfigCache] = None
) -> List[Dict[str, Any]]:
    """
    List all available issue types in a space.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        config_cache: Optional configuration cache
        
    Returns:
        List of type information dictionaries
    """
    if config_cache is None:
        config_cache = SpaceConfigCache(client)
    
    types = config_cache.get_issue_types(space_id)
    
    result = []
    for name, type_config in types.items():
        result.append({
            'name': name,
            'id': type_config.type_id,
            'alias': type_config.alias,
            'color': type_config.color,
            'has_children': len(type_config.child_type_ids) > 0,
            'child_count': len(type_config.child_type_ids)
        })
    
    return result


def print_available_types(
    client: ICafeClient,
    space_id: str,
    config_cache: Optional[SpaceConfigCache] = None
):
    """
    Print available issue types to console.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        config_cache: Optional configuration cache
    """
    types = list_available_types(client, space_id, config_cache)
    
    print(f"\n{'='*70}")
    print(f"可用卡片类型 - {space_id}")
    print(f"{'='*70}")
    print(f"共 {len(types)} 种类型:\n")
    
    for i, t in enumerate(types, 1):
        print(f"{i}. {t['name']} (ID: {t['id']})")
        if t['alias']:
            print(f"   别名: {t['alias']}")
        if t['has_children']:
            print(f"   子类型数: {t['child_count']}")
    
    print(f"\n{'='*70}\n")