"""
iCafe Skill - Python SDK for iCafe Card Operations

This package provides a comprehensive SDK for interacting with iCafe API,
including card queries, creation, updates, and comment management.

Basic Usage:
    >>> from icafe_skill import ICafeClient, AuthConfig
    >>> from icafe_skill.query import get_card, list_cards
    >>>
    >>> # Initialize client from config file (relative path)
    >>> auth = AuthConfig.from_file("config/config.yaml")
    >>> client = ICafeClient(auth)
    >>>
    >>> # Or use init_client helper
    >>> client = init_client(config_file="config/config.yaml")
    >>>
    >>> # Query a card
    >>> card = get_card(client, "my-space", "123")
    >>> print(f"{card.title}: {card.status}")
    >>>
    >>> # List cards with filter
    >>> cards = list_cards(client, "my-space", iql="流程状态=新建")

For more examples, see the examples/ directory.
"""

__version__ = "0.4.3"
__author__ = "iCafe Team"
__license__ = "MIT"

# Core components
from .auth import AuthConfig, load_config_file
from .client import ICafeClient
from .models import Card, CardRelation, Issue, Comment, Plan, DevInfo, FieldConfig, FieldGap, DetectRequiredFieldsResult
from .exceptions import (
    ICafeError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ResourceConflictError,
    MissingRequiredFieldsError,
    ValidationError,
    InvalidParameterError,
    NetworkError,
    TimeoutError,
    APIError,
)

# Query functions
from .query import (
    get_card,
    list_cards,
    get_card_status,
    get_dev_info,
    get_comments,
    get_cards_with_dev_updates,
)

# Create functions
from .create import (
    create_cards,
    create_comment,
)

# Update functions
from .update import (
    update_card,
    update_comment,
    preview_update,
    detect_required_fields,
)

# Plan functions
from .plan import (
    get_plan,
    create_plan,
    update_plan_date,
    get_plans_with_milestones,
)

# Utility functions
from .utils import (
    get_plans,
    get_issue_types,
    get_fields_for_create,
    parse_card_id,
    validate_space_id,
    validate_date_format,
    validate_email,
    format_date,
    build_iql_query,
)

# Field configuration
from .field_config import (
    FieldConfig as FieldConfigClass,
    IssueTypeConfig,
    SpaceConfigCache,
)

# Helper functions
from .helpers import (
    get_required_fields_info,
    print_required_fields,
    validate_card_data,
    build_issue_with_guidance,
    list_available_types,
    print_available_types,
)

__all__ = [
    # Version
    "__version__",
    
    # Core
    "AuthConfig",
    "ICafeClient",
    "load_config_file",
    
    # Models
    "Card",
    "CardRelation",
    "Issue",
    "Comment",
    "Plan",
    "DevInfo",
    "FieldConfig",
    "FieldGap",
    "DetectRequiredFieldsResult",
    
    # Exceptions
    "ICafeError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ResourceConflictError",
    "MissingRequiredFieldsError",
    "ValidationError",
    "InvalidParameterError",
    "NetworkError",
    "TimeoutError",
    "APIError",
    
    # Query
    "get_card",
    "list_cards",
    "get_card_status",
    "get_dev_info",
    "get_comments",
    "get_cards_with_dev_updates",
    
    # Create
    "create_cards",
    "create_comment",
    
    # Update
    "update_card",
    "update_comment",
    "preview_update",
    "detect_required_fields",

    # Plan
    "get_plan",
    "create_plan",
    "update_plan_date",
    "get_plans_with_milestones",
    
    # Utils
    "get_plans",
    "get_issue_types",
    "get_fields_for_create",
    "parse_card_id",
    "validate_space_id",
    "validate_date_format",
    "validate_email",
    "format_date",
    "build_iql_query",
    
    # Field configuration
    "FieldConfigClass",
    "IssueTypeConfig",
    "SpaceConfigCache",
    
    # Helpers
    "get_required_fields_info",
    "print_required_fields",
    "validate_card_data",
    "build_issue_with_guidance",
    "list_available_types",
    "print_available_types",
]


def init_client(
    username: str = None,
    password: str = None,
    config_file: str = None,
    **kwargs
) -> ICafeClient:
    """
    Convenient function to initialize an iCafe client.

    Priority (highest to lowest):
    1. Explicit username and password
    2. Configuration file (relative path, e.g., "config/config.yaml")

    Args:
        username: iCafe username
        password: Virtual password
        config_file: Path to YAML configuration file (relative path recommended)
        **kwargs: Additional arguments for ICafeClient

    Returns:
        Initialized ICafeClient instance

    Raises:
        AuthenticationError: If credentials cannot be loaded

    Example:
        >>> # From config file (relative path)
        >>> client = init_client(config_file="config/config.yaml")
        >>>
        >>> # Explicit credentials
        >>> client = init_client(username="zhangsan", password="xxx")
    """
    if username and password:
        auth = AuthConfig(username=username, password=password)
    elif config_file:
        auth = AuthConfig.from_file(config_file)
    else:
        raise AuthenticationError(
            "No authentication credentials provided. "
            "Please provide username/password or config file (e.g., config_file='config/config.yaml')."
        )

    return ICafeClient(auth, **kwargs)