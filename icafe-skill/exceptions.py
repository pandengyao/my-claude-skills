"""
Custom exceptions for iCafe Skill.

This module defines all custom exceptions used throughout the iCafe SDK.
All exceptions inherit from ICafeError base class.
"""


class ICafeError(Exception):
    """
    Base exception class for all iCafe-related errors.
    
    All custom exceptions in this SDK inherit from this class.
    """
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class AuthenticationError(ICafeError):
    """
    Raised when authentication fails.
    
    This typically occurs when:
    - Username or password is incorrect
    - Credentials are missing
    - Virtual password has expired
    """
    pass


class AuthorizationError(ICafeError):
    """
    Raised when user doesn't have permission for an operation.
    
    This occurs when:
    - User doesn't have access to the specified space
    - User doesn't have permission to modify a card
    - Operation requires elevated privileges
    """
    pass


class ResourceNotFoundError(ICafeError):
    """
    Raised when a requested resource doesn't exist.
    
    This occurs when:
    - Card ID doesn't exist
    - Space ID is invalid
    - Comment ID is not found
    - Plan ID doesn't exist
    """
    pass


class ResourceConflictError(ICafeError):
    """
    Raised when there's a conflict with existing resources.

    This occurs when:
    - Trying to create a duplicate card
    - Concurrent modification conflicts
    - Invalid state transitions
    """
    pass


class MissingRequiredFieldsError(ICafeError):
    """
    Raised when attempting to transition to a status without required fields.

    This occurs when:
    - Updating card status without filling required fields for the target status
    - Status transition is blocked by missing required fields

    Attributes:
        missing_fields: List of field names that are missing
        current_status: Current status of the card
        target_status: Target status being attempted
        field_options: Optional dictionary mapping field names to available options
    """

    def __init__(self, message: str, missing_fields: list = None,
                 current_status: str = None, target_status: str = None,
                 field_options: dict = None):
        """
        Initialize missing required fields error.

        Args:
            message: Error message
            missing_fields: List of field names that are missing
            current_status: Current status of the card
            target_status: Target status being attempted
            field_options: Dictionary mapping field names to available options
        """
        details = {}
        if missing_fields:
            details['missing_fields'] = missing_fields
        if current_status:
            details['current_status'] = current_status
        if target_status:
            details['target_status'] = target_status
        if field_options:
            details['field_options'] = field_options
        super().__init__(message, details)
        self.missing_fields = missing_fields or []
        self.current_status = current_status
        self.target_status = target_status
        self.field_options = field_options or {}


class ValidationError(ICafeError):
    """
    Raised when input validation fails.
    
    This occurs when:
    - Required fields are missing
    - Field values are invalid
    - Data format is incorrect
    """
    pass


class InvalidParameterError(ICafeError):
    """
    Raised when a parameter value is invalid.
    
    This occurs when:
    - Space ID format is incorrect
    - Card ID format is invalid
    - Date format is wrong
    - Email format is invalid
    """
    pass


class NetworkError(ICafeError):
    """
    Raised when a network-related error occurs.
    
    This occurs when:
    - Connection to API server fails
    - DNS resolution fails
    - SSL/TLS errors
    """
    pass


class TimeoutError(ICafeError):
    """
    Raised when a request times out.
    
    This occurs when:
    - Request exceeds configured timeout
    - Server is not responding
    - Network is too slow
    """
    pass


class APIError(ICafeError):
    """
    Raised when the API returns an unexpected error.
    
    This is a catch-all for server-side errors that don't fit
    into other specific exception categories.
    """
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        """
        Initialize API error with additional context.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Raw response body
        """
        details = {}
        if status_code:
            details['status_code'] = status_code
        if response_body:
            details['response_body'] = response_body
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body