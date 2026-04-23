"""
Data models for iCafe Skill.

This module defines data classes for representing iCafe entities
such as cards, issues, comments, and plans.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class CardRelation:
    """
    Represents a relation to another card (parent, child, or related issue).

    Used to display card relationship information without full card details.
    """
    sequence: str
    space_prefix_code: str
    title: Optional[str] = None
    space_name: Optional[str] = None
    card_type: Optional[str] = None
    status: Optional[str] = None

    @property
    def full_id(self) -> str:
        """Get full card ID in format 'space_prefix_code-sequence'."""
        return f"{self.space_prefix_code}-{self.sequence}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "CardRelation":
        """
        Create CardRelation instance from API response.

        Args:
            data: Raw API response data (parent, children, or relIssues object)

        Returns:
            CardRelation instance
        """
        return cls(
            sequence=str(data.get("sequence", "")),
            space_prefix_code=data.get("spacePrefixCode", data.get("space_prefix_code", "")),
            title=data.get("title"),
            space_name=data.get("spaceName", data.get("space_name")),
            card_type=data.get("type", data.get("issueType")),
            status=data.get("status", data.get("issueStatus")),
        )


@dataclass
class Card:
    """
    Represents an iCafe card.

    This is the primary data structure for querying and displaying
    card information.
    """

    space_id: str
    card_id: str
    title: str
    sequence: str = ""
    detail: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    creator: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    plan: Optional[str] = None
    # 卡片关联信息
    parent: Optional[CardRelation] = None
    children: List[CardRelation] = field(default_factory=list)
    related_issues: List[CardRelation] = field(default_factory=list)
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_id(self) -> str:
        """Get full card ID in format 'space_id-card_id'."""
        return f"{self.space_id}-{self.card_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Card":
        """
        Create Card instance from API response.

        Args:
            data: Raw API response data

        Returns:
            Card instance
        """
        # Fields that are explicitly processed - these will NOT be stored in extra_fields
        processed_keys = {
            "spaceId", "space_id", "spacePrefixCode",
            "id", "card_id", "sequence",
            "title", "detail", "description",
            "type", "issueType",
            "status", "issueStatus",
            "assignee", "owner", "responsiblePeople",
            "priority",
            "creator", "createdUser",
            "createdTime", "createTime", "created_at",
            "lastModifiedTime", "updateTime", "updated_at",
            "plan",
            "parent",
            "children",
            "relIssues",
            "rel_issue_space_pre_seq",
        }

        # Extract fields with flexible key names
        # Handle type field (can be string or dict with 'name' key)
        type_value = data.get("type", data.get("issueType"))
        if isinstance(type_value, dict):
            type_value = type_value.get("name", "")

        # Handle assignee (can be string, dict, or list in responsiblePeople)
        assignee_value = data.get("assignee", data.get("owner"))
        if not assignee_value:
            # Try to get from responsiblePeople list
            responsible_people = data.get("responsiblePeople", [])
            if responsible_people and len(responsible_people) > 0:
                person = responsible_people[0]
                if isinstance(person, dict):
                    assignee_value = person.get("username", person.get("name", ""))
                else:
                    assignee_value = str(person)

        # Handle creator (can be string or dict in createdUser)
        creator_value = data.get("creator")
        if not creator_value:
            created_user = data.get("createdUser", {})
            if isinstance(created_user, dict):
                creator_value = created_user.get("username", created_user.get("name", ""))
            else:
                creator_value = str(created_user)

        # Handle created_at (can be createdTime or createTime)
        created_at_value = data.get("createdTime", data.get("createTime", data.get("created_at")))

        # Handle updated_at (can be lastModifiedTime or updateTime)
        updated_at_value = data.get("lastModifiedTime", data.get("updateTime", data.get("updated_at")))

        # Handle parent relation
        parent_value = None
        parent_data = data.get("parent")
        if parent_data and isinstance(parent_data, dict):
            parent_value = CardRelation.from_api_response(parent_data)

        # Handle children list
        children_value = []
        children_data = data.get("children", [])
        if children_data and isinstance(children_data, list):
            children_value = [CardRelation.from_api_response(c) for c in children_data if isinstance(c, dict)]

        # Handle related issues list
        related_issues_value = []
        rel_issues_data = data.get("relIssues", [])
        if rel_issues_data and isinstance(rel_issues_data, list):
            related_issues_value = [CardRelation.from_api_response(r) for r in rel_issues_data if isinstance(r, dict)]

        # Store extra fields that were not explicitly processed
        extra_fields = {k: v for k, v in data.items() if k not in processed_keys}

        # Parse properties list into a dictionary if present
        # properties is a list of dicts: [{'propertyName': 'xxx', 'value': 'yyy', ...}, ...]
        if "properties" in extra_fields and isinstance(extra_fields["properties"], list):
            properties_dict = {}
            for prop in extra_fields["properties"]:
                if isinstance(prop, dict):
                    prop_name = prop.get("propertyName")
                    if prop_name:
                        # Store displayValue (the human-readable value)
                        properties_dict[prop_name] = prop.get("displayValue", prop.get("value", ""))
            # Replace the properties list with the parsed dictionary
            extra_fields["properties"] = properties_dict

        return cls(
            space_id=data.get("spaceId", data.get("space_id", data.get("spacePrefixCode", ""))),
            # card_id: 主标识符，用于 API 操作
            card_id=str(data.get("card_id", data.get("id", data.get("sequence", "")))),
            title=data.get("title", ""),
            # sequence: iCafe 系统分配的序列号
            sequence=str(data.get("sequence", "")),
            detail=data.get("detail", data.get("description")),
            type=type_value,
            status=data.get("status", data.get("issueStatus")),
            assignee=assignee_value,
            priority=data.get("priority"),
            creator=creator_value,
            created_at=created_at_value,
            updated_at=updated_at_value,
            plan=data.get("plan"),
            parent=parent_value,
            children=children_value,
            related_issues=related_issues_value,
            extra_fields=extra_fields,
        )


@dataclass
class Issue:
    """
    Represents an issue for card creation.

    This structure is used when creating new cards via the API.
    """

    title: str
    detail: str
    type: str
    creator: str
    fields: Dict[str, str] = field(default_factory=dict)
    notify_emails: List[str] = field(default_factory=list)
    comment: Optional[str] = None
    # 新增字段
    parent: Optional[str] = None           # 父卡片序号（sequence）
    parent_space_prefix_code: Optional[str] = None  # 父卡片所属空间前缀
    rel_issue_space_pre_seq: Optional[str] = None  # 关联卡片（空间标识-序号）
    
    def to_api_format(self) -> Dict[str, Any]:
        """
        Convert to API request format.

        Returns:
            Dictionary in the format expected by iCafe API
        """
        result = {
            "title": self.title,
            "detail": self.detail,
            "type": self.type,
            "creator": self.creator,
            "fields": self.fields,
        }

        if self.notify_emails:
            result["notifyEmails"] = self.notify_emails

        if self.comment:
            result["comment"] = self.comment

        # 新增字段序列化
        if self.parent:
            result["parent"] = self.parent

        if self.parent_space_prefix_code:
            result["parentSpacePrefixCode"] = self.parent_space_prefix_code

        if self.rel_issue_space_pre_seq:
            result["relIssueSpacePreSeq"] = self.rel_issue_space_pre_seq

        return result
    
    @classmethod
    def create(
        cls,
        title: str,
        detail: str,
        type: str,
        creator: str,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        notify_emails: Optional[List[str]] = None,
        comment: Optional[str] = None,
        parent: Optional[str] = None,
        parent_space_prefix_code: Optional[str] = None,
        rel_issue_space_pre_seq: Optional[str] = None,
    ) -> "Issue":
        """
        Create an Issue with common fields.

        Args:
            title: Card title
            detail: Card description
            type: Card type (e.g., "Story", "Task", "Bug")
            creator: Creator username
            assignee: Assignee username
            status: Initial status (e.g., "新建")
            priority: Priority level (e.g., "P1-High")
            notify_emails: List of emails to notify
            comment: Initial comment
            parent: Parent card sequence number
            parent_space_prefix_code: Parent card's space prefix code
            rel_issue_space_pre_seq: Related issue (space_prefix-sequence)

        Returns:
            Issue instance
        """
        fields = {}

        if assignee:
            fields["负责人"] = assignee
        if status:
            fields["流程状态"] = status
        if priority:
            fields["优先级"] = priority

        return cls(
            title=title,
            detail=detail,
            type=type,
            creator=creator,
            fields=fields,
            notify_emails=notify_emails or [],
            comment=comment,
            parent=parent,
            parent_space_prefix_code=parent_space_prefix_code,
            rel_issue_space_pre_seq=rel_issue_space_pre_seq,
        )


@dataclass
class Comment:
    """
    Represents a card comment.
    """
    
    comment_id: str
    card_id: str
    content: str
    author: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Comment":
        """
        Create Comment instance from API response.
        
        Args:
            data: Raw API response data
            
        Returns:
            Comment instance
        """
        return cls(
            comment_id=str(data.get("id", data.get("commentId", ""))),
            card_id=str(data.get("issueId", data.get("sequence", ""))),
            content=data.get("content", data.get("comment", "")),
            author=data.get("author", data.get("creator", "")),
            created_at=data.get("createTime", data.get("created_at")),
            updated_at=data.get("updateTime", data.get("updated_at")),
        )


@dataclass
class Plan:
    """
    Represents an iCafe plan.
    """

    plan_id: str
    name: str
    space_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    is_milestone: bool = False
    parent_plan_id: Optional[str] = None
    status: Optional[str] = None
    children: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Plan":
        """
        Create Plan instance from API response.

        Args:
            data: Raw API response data

        Returns:
            Plan instance
        """
        # Handle nested result structure
        if "result" in data:
            data = data["result"]

        return cls(
            plan_id=str(data.get("id", data.get("planId", ""))),
            name=data.get("name", ""),
            space_id=data.get("spaceId", ""),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            description=data.get("desc", data.get("description")),
            is_milestone=data.get("isMilestone", False),
            parent_plan_id=data.get("parentId"),
            status=data.get("status"),
            children=data.get("children", []),
        )


@dataclass
class DevInfo:
    """
    Represents development data chain information.
    """
    
    card_id: str
    icode_reviews: List[Dict[str, Any]] = field(default_factory=list)
    pipelines: List[Dict[str, Any]] = field(default_factory=list)
    branches: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "DevInfo":
        """
        Create DevInfo instance from API response.
        
        Args:
            data: Raw API response data
            
        Returns:
            DevInfo instance
        """
        return cls(
            card_id=str(data.get("issueId", data.get("sequence", ""))),
            icode_reviews=data.get("icodeReviews", data.get("reviews", [])),
            pipelines=data.get("pipelines", []),
            branches=data.get("branches", []),
        )


@dataclass
class FieldConfig:
    """
    Represents field configuration for a card type.
    """

    field_name: str
    field_type: str
    required: bool = False
    options: List[str] = field(default_factory=list)
    default_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "FieldConfig":
        """
        Create FieldConfig instance from API response.

        Args:
            data: Raw API response data

        Returns:
            FieldConfig instance
        """
        return cls(
            field_name=data.get("name", data.get("fieldName", "")),
            field_type=data.get("type", data.get("fieldType", "string")),
            required=data.get("required", False),
            options=data.get("options", []),
            default_value=data.get("defaultValue"),
        )


@dataclass
class FieldGap:
    """
    Field gap information, representing the difference between
    the current card and target status cards.
    """
    field_display: str          # Field display name (e.g., "Bug问题原因")
    field_name: str             # Internal field name
    field_type: str             # Field type (select_list, user_picker, etc.)
    is_required: bool           # Whether this is a required field
    current_value: Any          # Current card value
    sample_values: List[Any]    # Sample values from target status cards
    most_common_value: Any      # Most common value in samples
    options: List[str]          # Valid options (for select fields)
    default_value: Any          # Default value (if available)
    suggestion: str             # Suggested value based on analysis
    needs_fill: bool            # Whether the field needs to be filled
    reason: str                 # Reason for needing to fill

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DetectRequiredFieldsResult:
    """
    Result of required fields detection analysis.
    """
    space_id: str
    card_id: str
    current_status: str
    target_status: str
    issue_type: str
    can_transition: bool                      # Whether the status can be transitioned

    # Field analysis
    required_fields: List[FieldGap]            # All required fields from type config
    fields_needing_fill: List[FieldGap]        # Fields that need to be filled
    fields_unchanged: List[FieldGap]           # Required fields already satisfied

    # Sample card information
    sample_card_ids: List[str]                # Sample card IDs analyzed
    sample_card_count: int                    # Number of sample cards found

    # Summary information
    total_required_fields: int
    fields_to_fill_count: int
    confidence: float                         # Confidence level (0.0 - 1.0)

    # Recommendations
    recommended_fields: Dict[str, Any]        # Suggested field values
    warnings: List[str]                       # Warning messages

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        """
        result = {
            "space_id": self.space_id,
            "card_id": self.card_id,
            "current_status": self.current_status,
            "target_status": self.target_status,
            "issue_type": self.issue_type,
            "can_transition": self.can_transition,
            "required_fields": [f.to_dict() for f in self.required_fields],
            "fields_needing_fill": [f.to_dict() for f in self.fields_needing_fill],
            "fields_unchanged": [f.to_dict() for f in self.fields_unchanged],
            "sample_card_ids": self.sample_card_ids,
            "sample_card_count": self.sample_card_count,
            "total_required_fields": self.total_required_fields,
            "fields_to_fill_count": self.fields_to_fill_count,
            "confidence": self.confidence,
            "recommended_fields": self.recommended_fields,
            "warnings": self.warnings,
        }
        return result

    def get_suggested_update_fields(self) -> Dict[str, str]:
        """
        Get suggested fields for update_card() call.

        Returns:
            Dictionary of field names to suggested values
        """
        fields = {}
        for field in self.fields_needing_fill:
            if field.suggestion and field.suggestion != "(None)":
                fields[field.field_name] = field.suggestion
        return fields