"""
Card creation module for iCafe Skill.

This module provides functions to create cards and comments.
"""

from typing import List, Dict, Any, Optional
from .client import ICafeClient
from .models import Issue
from .exceptions import ValidationError
from .field_config import SpaceConfigCache
import warnings
import logging

logger = logging.getLogger(__name__)


def create_cards(
    client: ICafeClient,
    space_id: str,
    issues: List[Issue],
    dry_run: bool = True,
    validate_fields: bool = True,
    config_cache: Optional[SpaceConfigCache] = None
) -> Dict[str, Any]:
    """
    Create one or more cards in batch.

    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issues: List of Issue objects to create
        dry_run: If True, only validate and show what would be sent (default: True)
        validate_fields: If True, validate fields against space configuration (default: True)
        config_cache: Optional SpaceConfigCache for field validation

    Returns:
        Dictionary with creation results or dry-run preview

    Raises:
        ValidationError: If parameters are invalid

    Example:
        >>> from icafe_skill.models import Issue
        >>> issue = Issue.create(
        ...     title="New feature",
        ...     detail="Implement new feature",
        ...     type="Story",
        ...     creator="zhangsan",
        ...     assignee="lisi",
        ...     priority="P1-High"
        ... )
        >>> result = create_cards(client, "test-space", [issue], dry_run=True)
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    if not issues or not isinstance(issues, list):
        raise ValidationError("issues must be a non-empty list")
    
    # Validate each issue
    validation_errors = []
    for i, issue in enumerate(issues):
        if not isinstance(issue, Issue):
            raise ValidationError(f"Issue at index {i} is not an Issue object")
        if not issue.title or not issue.title.strip():
            validation_errors.append(f"Issue {i+1}: title cannot be empty")
        if not issue.type or not issue.type.strip():
            validation_errors.append(f"Issue {i+1}: type cannot be empty")
        if not issue.creator or not issue.creator.strip():
            validation_errors.append(f"Issue {i+1}: creator cannot be empty")
        
        # Validate fields against space configuration
        if validate_fields:
            try:
                if config_cache is None:
                    config_cache = SpaceConfigCache(client)
                
                logger.info(f"Validating fields for issue {i+1} (type: {issue.type})")
                type_config = config_cache.get_type_with_fields(space_id, issue.type)
                
                # Prepare fields for validation
                fields_data = issue.fields.copy()
                fields_data["标题"] = issue.title
                fields_data["内容"] = issue.detail
                fields_data["负责人"] = issue.fields.get("负责人", issue.creator)
                
                # Validate
                field_errors = type_config.validate_fields(fields_data)
                if field_errors:
                    validation_errors.append(f"Issue {i+1} field errors: " + "; ".join(field_errors))
                else:
                    logger.info(f"✓ Issue {i+1} fields validated successfully")
                    
            except Exception as e:
                logger.warning(f"Field validation failed for issue {i+1}: {e}")
                validation_errors.append(f"Issue {i+1}: field validation error - {e}")
    
    if validation_errors:
        raise ValidationError(
            "Validation failed:\n" + "\n".join(validation_errors)
        )
    
    # Build request payload
    issues_data = [issue.to_api_format() for issue in issues]
    payload = {
        "issues": issues_data
    }
    
    if dry_run:
        warnings.warn(
            "Running in DRY-RUN mode. No actual API call will be made. "
            "Set dry_run=False to execute actual creation.",
            UserWarning
        )
        return {
            "dry_run": True,
            "space_id": space_id,
            "issues_count": len(issues),
            "payload": payload,
            "endpoint": f"/api/v2/space/{space_id}/issue/new"
        }

    # Actual creation
    path = f"/api/v2/space/{space_id}/issue/new"
    response = client.post(path, json=payload)
    
    return response


def create_comment(
    client: ICafeClient,
    space_id: str,
    issue_id: str,
    comment_msg: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Create a comment on a card.

    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_id: Issue/card ID
        comment_msg: Comment message
        dry_run: If True, only show what would be sent (default: True)

    Returns:
        Dictionary with creation result or dry-run preview

    Raises:
        ValidationError: If parameters are invalid

    Example:
        >>> result = create_comment(
        ...     client,
        ...     "test-space",
        ...     "123",
        ...     "This is a test comment",
        ...     dry_run=True
        ... )
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    if not issue_id or not issue_id.strip():
        raise ValidationError("issue_id cannot be empty")
    
    if not comment_msg or not comment_msg.strip():
        raise ValidationError("comment_msg cannot be empty")
    
    # Parse issue_id
    from .query import _parse_card_id
    issue_id = _parse_card_id(issue_id)
    
    payload = {
        "commentMsg": comment_msg.strip()
    }
    
    if dry_run:
        warnings.warn(
            "Running in DRY-RUN mode. No actual API call will be made.",
            UserWarning
        )
        return {
            "dry_run": True,
            "space_id": space_id,
            "issue_id": issue_id,
            "payload": payload,
            "endpoint": f"/api/v2/space/{space_id}/issue/{issue_id}/comment"
        }

    # Actual creation
    path = f"/api/v2/space/{space_id}/issue/{issue_id}/comment"
    response = client.post(path, json=payload)
    
    return response