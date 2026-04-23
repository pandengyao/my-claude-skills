"""
Utility functions for iCafe Skill.

This module provides helper functions for plans, types, field configuration,
and data validation.
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from .client import ICafeClient
from .models import Plan, FieldConfig
from .exceptions import ValidationError, InvalidParameterError


def get_plans(
    client: ICafeClient,
    space_id: str
) -> List[Plan]:
    """
    Get all plans in a space.

    Args:
        client: Authenticated iCafe client
        space_id: Space identifier

    Returns:
        List of Plan objects

    Raises:
        ValidationError: If space_id is empty

    Example:
        >>> plans = get_plans(client, "test-space")
        >>> for plan in plans:
        ...     print(f"{plan.name}: {plan.start_date} - {plan.end_date}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")

    path = f"/api/v2/space/{space_id}/plans"
    response = client.get(path)

    # Handle different response formats
    # iCafe API returns: {'result': [...], 'status': 200, 'message': 'OK.'}
    if isinstance(response, dict):
        if "result" in response:
            plans_data = response["result"]
        else:
            plans_data = response.get("plans", response.get("data", []))
            if not isinstance(plans_data, list):
                plans_data = [response] if response else []
    elif isinstance(response, list):
        plans_data = response
    else:
        plans_data = []

    plans = []
    for plan_data in plans_data:
        if not isinstance(plan_data, dict):
            continue
        if "spaceId" not in plan_data:
            plan_data["spaceId"] = space_id
        plans.append(Plan.from_api_response(plan_data))

    return plans


def get_issue_types(
    client: ICafeClient,
    space_id: str
) -> List[Dict[str, Any]]:
    """
    Get all issue types configured in a space.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        
    Returns:
        List of issue type dictionaries
        
    Raises:
        ValidationError: If space_id is empty
        
    Example:
        >>> types = get_issue_types(client, "test-space")
        >>> for t in types:
        ...     print(f"{t['name']}: {t['id']}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    path = f"/api/v2/space/{space_id}/issueTypes"
    response = client.get(path)
    
    # Handle different response formats
    types_data = response.get("issueTypes", response.get("types", response.get("data", [])))
    
    if not isinstance(types_data, list):
        types_data = [response] if response else []
    
    return types_data


def get_fields_for_create(
    client: ICafeClient,
    space_id: str,
    issue_type_name: str
) -> List[FieldConfig]:
    """
    Get field configurations for creating a specific issue type.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_type_name: Issue type name (e.g., "Story", "Task", "Bug")
        
    Returns:
        List of FieldConfig objects
        
    Raises:
        ValidationError: If parameters are empty
        
    Example:
        >>> fields = get_fields_for_create(client, "test-space", "Story")
        >>> for field in fields:
        ...     print(f"{field.field_name} ({field.field_type}): required={field.required}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    if not issue_type_name or not issue_type_name.strip():
        raise ValidationError("issue_type_name cannot be empty")
    
    path = f"/api/v2/spaces/{space_id}/fieldsForCreate"
    params = {"issueTypeName": issue_type_name}
    response = client.get(path, params=params)
    
    # Handle different response formats
    fields_data = response.get("fields", response.get("data", []))
    
    if not isinstance(fields_data, list):
        fields_data = []
    
    fields = []
    for field_data in fields_data:
        fields.append(FieldConfig.from_api_response(field_data))
    
    return fields


def parse_card_id(card_id: str) -> tuple[str, str]:
    """
    Parse card ID to extract space_id and numeric ID.
    
    Supports formats:
    - "123" -> ("", "123")
    - "space-123" -> ("space", "123")
    - "my-space-456" -> ("my-space", "456")
    
    Args:
        card_id: Card ID in any format
        
    Returns:
        Tuple of (space_id, numeric_id)
        
    Raises:
        InvalidParameterError: If card_id format is invalid
        
    Example:
        >>> space, num = parse_card_id("test-space-123")
        >>> print(f"Space: {space}, ID: {num}")
    """
    if not card_id or not isinstance(card_id, str):
        raise InvalidParameterError("card_id cannot be empty")
    
    card_id = card_id.strip()
    
    # If no hyphen, assume it's just numeric ID
    if "-" not in card_id:
        if not card_id.isdigit():
            raise InvalidParameterError(
                f"Invalid card_id format: {card_id}. Expected numeric ID or 'space-id' format."
            )
        return ("", card_id)
    
    # Split by hyphen
    parts = card_id.split("-")
    
    # Last part should be numeric
    numeric_id = parts[-1]
    if not numeric_id.isdigit():
        raise InvalidParameterError(
            f"Invalid card_id format: {card_id}. Last part should be numeric."
        )
    
    # Everything before last hyphen is space_id
    space_id = "-".join(parts[:-1])
    
    return (space_id, numeric_id)


def validate_space_id(space_id: str) -> bool:
    """
    Validate space ID format.
    
    Rules:
    - Not empty
    - 3-50 characters
    - Only letters, numbers, hyphens
    - Cannot start or end with hyphen
    
    Args:
        space_id: Space identifier to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    space_id = space_id.strip()
    
    if len(space_id) < 3:
        raise ValidationError("space_id must be at least 3 characters")
    
    if len(space_id) > 50:
        raise ValidationError("space_id must be at most 50 characters")
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', space_id):
        raise ValidationError(
            "space_id must contain only letters, numbers, and hyphens, "
            "and cannot start or end with a hyphen"
        )
    
    return True


def validate_date_format(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format.
    
    Args:
        date_str: Date string to validate
        format: Expected date format (default: "YYYY-MM-DD")
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not date_str or not date_str.strip():
        raise ValidationError("date_str cannot be empty")
    
    try:
        datetime.strptime(date_str.strip(), format)
        return True
    except ValueError as e:
        raise ValidationError(f"Invalid date format: {date_str}. Expected format: {format}. Error: {e}")


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not email or not email.strip():
        raise ValidationError("email cannot be empty")
    
    email = email.strip()
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return True


def format_date(date_str: str, input_format: str = None, output_format: str = "%Y-%m-%d") -> str:
    """
    Convert date string from one format to another.
    
    Args:
        date_str: Date string to convert
        input_format: Input format (if None, will try common formats)
        output_format: Output format (default: "YYYY-MM-DD")
        
    Returns:
        Formatted date string
        
    Raises:
        ValidationError: If date cannot be parsed
    """
    if not date_str or not date_str.strip():
        raise ValidationError("date_str cannot be empty")
    
    date_str = date_str.strip()
    
    # If input format is specified, use it
    if input_format:
        try:
            dt = datetime.strptime(date_str, input_format)
            return dt.strftime(output_format)
        except ValueError as e:
            raise ValidationError(f"Failed to parse date: {e}")
    
    # Try common formats
    common_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    
    for fmt in common_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue
    
    raise ValidationError(f"Cannot parse date: {date_str}. Unknown format.")


def build_iql_query(conditions: Dict[str, str]) -> str:
    """
    Build IQL query string from conditions dictionary.
    
    Args:
        conditions: Dictionary of field-value pairs
        
    Returns:
        IQL query string
        
    Example:
        >>> iql = build_iql_query({"流程状态": "新建", "负责人": "zhangsan"})
        >>> print(iql)  # "流程状态=新建 AND 负责人=zhangsan"
    """
    if not conditions:
        return ""
    
    parts = []
    for key, value in conditions.items():
        parts.append(f"{key}={value}")
    
    return " AND ".join(parts)