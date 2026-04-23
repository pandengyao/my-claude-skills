"""
Card query module for iCafe Skill.

This module provides functions to query card information from iCafe API.
"""

from typing import Optional, List, Dict, Any
from .client import ICafeClient
from .models import Card, Comment, DevInfo
from .exceptions import ValidationError, InvalidParameterError


def get_card(
    client: ICafeClient,
    space_id: str,
    card_id: str
) -> Card:
    """
    Get a single card by ID.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier (e.g., "edc-scrum-352568")
        card_id: Card ID (e.g., "352568" or "edc-scrum-352568")
        
    Returns:
        Card object with card information
        
    Raises:
        ValidationError: If space_id or card_id is empty
        ResourceNotFoundError: If card doesn't exist
        
    Example:
        >>> from icafe_skill.auth import AuthConfig
        >>> from icafe_skill.client import ICafeClient
        >>> from icafe_skill.query import get_card
        >>>
        >>> auth = AuthConfig.from_env()  # or AuthConfig.from_file("config.yaml")
        >>> client = ICafeClient(auth)
        >>> card = get_card(client, "edc-scrum-352568", "352568")
        >>> print(f"Title: {card.title}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    # Parse card_id to handle both formats: "123" and "space-123"
    card_id = _parse_card_id(card_id)
    
    if not card_id:
        raise ValidationError("card_id cannot be empty")
    
    path = f"/api/spaces/{space_id}/cards/{card_id}"
    response = client.get(path)

    # Handle response format: {"cards": [...]}
    cards_data = response.get("cards", response.get("data", []))
    if not isinstance(cards_data, list):
        # If response is not a list, try to use it directly
        card_data = response
    elif len(cards_data) == 0:
        raise ResourceNotFoundError(
            f"Card not found: space_id={space_id}, card_id={card_id}"
        )
    else:
        card_data = cards_data[0]

    # Add space_id to response if not present
    if "spaceId" not in card_data and "space_id" not in card_data:
        card_data["spaceId"] = space_id

    return Card.from_api_response(card_data)


def list_cards(
    client: ICafeClient,
    space_id: str,
    iql: Optional[str] = None,
    page: int = 1,
    max_records: str = "100",
    show_detail: str = "",
    show_associations: bool = False,
    is_desc: bool = False,
    order: str = "createTime",
    show_children: bool = False,
    show_okr: bool = False,
    show_accumulate: bool = False
) -> List[Card]:
    """
    List cards in a space with optional IQL filtering.

    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        iql: Optional IQL query expression (e.g., "流程状态=新建")
        page: Page number (default: 1)
        max_records: Maximum records per page, default "100", max value "100"
        show_detail: Display card content. Set to "true" to return card detail information
                   (returned in "detail" field). Default empty string.
        show_associations: Display associated card information. Default False.
        is_desc: Whether to sort in descending order. Default False (ascending by create time).
        order: Sort field for ordering results. Default "createTime".
               Supported fields: custom dropdown fields, single-select fields,
               lastModifiedTime, creatorId, issueStatusId, responsiblePeopleId, sequence.
               Text/content fields are NOT supported.
        show_children: Display child card information. Default False.
        show_okr: Display associated OKR information. Default False.
        show_accumulate: Display weekly actual working hour details. Default False.

    Returns:
        List of Card objects

    Raises:
        ValidationError: If space_id is empty or max_records exceeds 100

    Example:
        >>> # List all cards
        >>> cards = list_cards(client, "edc-scrum-352568")
        >>>
        >>> # List cards with IQL filter
        >>> cards = list_cards(client, "edc-scrum-352568", iql="流程状态=新建")
        >>>
        >>> # List cards with sorting by last modified time, descending
        >>> cards = list_cards(client, "edc-scrum-352568", order="lastModifiedTime", is_desc=True)
        >>>
        >>> # List cards with detail and associations
        >>> cards = list_cards(client, "edc-scrum-352568", show_detail="true", show_associations=True)
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")

    # Validate max_records - max value is 100
    try:
        max_records_int = int(max_records)
        if max_records_int > 100:
            raise ValidationError("max_records cannot exceed 100")
    except ValueError:
        raise ValidationError("max_records must be a valid number")

    path = f"/api/spaces/{space_id}/cards"
    params = {
        "page": page,
        "maxRecords": max_records,
    }

    if show_detail:
        params["showDetail"] = show_detail

    if show_associations:
        params["showAssociations"] = "true"

    if is_desc:
        params["isDesc"] = "true"

    if order:
        params["order"] = order

    if show_children:
        params["showChildren"] = "true"

    if show_okr:
        params["showOkr"] = "true"

    if show_accumulate:
        params["showAccumulate"] = "true"

    if iql:
        params["iql"] = iql

    response = client.get(path, params=params)
    
    # Handle different response formats
    cards_data = response.get("cards", response.get("data", []))
    
    if not isinstance(cards_data, list):
        cards_data = [response] if response else []
    
    cards = []
    for card_data in cards_data:
        # Ensure space_id is in card data
        if "spaceId" not in card_data and "space_id" not in card_data:
            card_data["spaceId"] = space_id
        cards.append(Card.from_api_response(card_data))
    
    return cards


def get_card_status(
    client: ICafeClient,
    space_id: str,
    issue_id: str
) -> Dict[str, Any]:
    """
    Get card status information.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_id: Issue/card ID
        
    Returns:
        Dictionary with status information
        
    Raises:
        ValidationError: If parameters are empty
        
    Example:
        >>> status = get_card_status(client, "edc-scrum-352568", "352568")
        >>> print(f"Status: {status.get('status')}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    issue_id = _parse_card_id(issue_id)
    if not issue_id:
        raise ValidationError("issue_id cannot be empty")
    
    path = f"/api/v2/space/{space_id}/issue/{issue_id}/status"
    response = client.post(path)
    
    return response


def get_dev_info(
    client: ICafeClient,
    space_id: str,
    issue_id: str
) -> DevInfo:
    """
    Get development data chain information for a card.
    
    This includes iCode reviews, pipelines, and branch information.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        issue_id: Issue/card ID
        
    Returns:
        DevInfo object with development information
        
    Raises:
        ValidationError: If parameters are empty
        
    Example:
        >>> dev_info = get_dev_info(client, "edc-scrum-352568", "352568")
        >>> print(f"Reviews: {len(dev_info.icode_reviews)}")
        >>> print(f"Pipelines: {len(dev_info.pipelines)}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    issue_id = _parse_card_id(issue_id)
    if not issue_id:
        raise ValidationError("issue_id cannot be empty")
    
    path = f"/api/v2/space/{space_id}/issue/{issue_id}/devInfo"
    response = client.get(path)
    
    # Ensure issue_id is in response
    if "issueId" not in response and "sequence" not in response:
        response["issueId"] = issue_id
    
    return DevInfo.from_api_response(response)


def get_comments(
    client: ICafeClient,
    space_id: str,
    sequence: str
) -> List[Comment]:
    """
    Get all comments for a card.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        sequence: Card sequence/ID
        
    Returns:
        List of Comment objects
        
    Raises:
        ValidationError: If parameters are empty
        
    Example:
        >>> comments = get_comments(client, "edc-scrum-352568", "352568")
        >>> for comment in comments:
        ...     print(f"{comment.author}: {comment.content}")
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    
    sequence = _parse_card_id(sequence)
    if not sequence:
        raise ValidationError("sequence cannot be empty")
    
    path = f"/api/v2/space/{space_id}/issue/comment"
    params = {"sequence": sequence}
    response = client.get(path, params=params)
    
    # Handle different response formats
    comments_data = response.get("comments", response.get("data", []))
    
    if not isinstance(comments_data, list):
        comments_data = [response] if response else []
    
    comments = []
    for comment_data in comments_data:
        # Ensure card_id is in comment data
        if "issueId" not in comment_data and "sequence" not in comment_data:
            comment_data["sequence"] = sequence
        comments.append(Comment.from_api_response(comment_data))
    
    return comments


def get_cards_with_dev_updates(
    client: ICafeClient,
    space_id: str,
    start_time: str,
    end_time: str,
    page: int = 1,
    max_records: int = 100
) -> List[Dict[str, Any]]:
    """
    Get cards that have development data chain updates in a time range.
    
    Args:
        client: Authenticated iCafe client
        space_id: Space identifier
        start_time: Start time (format: "YYYY-MM-DD HH:MM:SS")
        end_time: End time (format: "YYYY-MM-DD HH:MM:SS")
        page: Page number (default: 1)
        max_records: Maximum records per page (default: 100)
        
    Returns:
        List of dictionaries with card and dev update information
        
    Raises:
        ValidationError: If parameters are invalid
        
    Example:
        >>> cards = get_cards_with_dev_updates(
        ...     client,
        ...     "edc-scrum-352568",
        ...     "2024-01-01 00:00:00",
        ...     "2024-12-31 23:59:59"
        ... )
    """
    if not space_id or not space_id.strip():
        raise ValidationError("space_id cannot be empty")
    if not start_time or not end_time:
        raise ValidationError("start_time and end_time cannot be empty")
    
    path = f"/api/v2/space/{space_id}/devInfo/issues"
    data = {
        "startTime": start_time,
        "endTime": end_time,
        "page": page,
        "maxRecords": max_records,
    }
    
    response = client.post(path, json=data)
    
    # Handle different response formats
    issues = response.get("issues", response.get("data", []))
    
    if not isinstance(issues, list):
        issues = [response] if response else []
    
    return issues


def _parse_card_id(card_id: str) -> str:
    """
    Parse card ID to extract numeric part.
    
    Supports both formats:
    - "123" -> "123"
    - "space-123" -> "123"
    
    Args:
        card_id: Card ID in any format
        
    Returns:
        Numeric card ID
        
    Raises:
        InvalidParameterError: If card_id format is invalid
    """
    if not card_id or not isinstance(card_id, str):
        return ""
    
    card_id = card_id.strip()
    
    # If contains hyphen, split and take the last part
    if "-" in card_id:
        parts = card_id.split("-")
        card_id = parts[-1]
    
    # Validate it's numeric
    if not card_id.isdigit():
        raise InvalidParameterError(
            f"Invalid card_id format: {card_id}. "
            "Expected numeric ID or 'space-id' format."
        )
    
    return card_id