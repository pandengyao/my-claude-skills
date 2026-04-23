"""
HTTP client for iCafe API.

This module provides a unified HTTP client that handles:
- Request/response processing
- Authentication injection
- Error handling and retries
- Logging and debugging
"""

import time
import logging
from typing import Optional, Dict, Any, Union
import requests
from urllib.parse import urljoin

from .auth import AuthConfig
from .exceptions import (
    ICafeError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    NetworkError,
    TimeoutError as ICafeTimeoutError,
    APIError,
)


logger = logging.getLogger(__name__)


class ICafeClient:
    """
    HTTP client for iCafe API operations.
    
    Handles all HTTP communication with the iCafe API server,
    including authentication, retries, and error handling.
    """
    
    DEFAULT_BASE_URL = "http://icafeapi.baidu-int.com"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BACKOFF = 1.5
    
    def __init__(
        self,
        auth: AuthConfig,
        base_url: str = None,
        timeout: int = None,
        max_retries: int = None,
        retry_backoff: float = None,
    ):
        """
        Initialize the iCafe HTTP client.
        
        Args:
            auth: Authentication configuration
            base_url: Base URL for API server (default: http://icafeapi.baidu-int.com)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries (default: 3)
            retry_backoff: Backoff multiplier for retries (default: 1.5)
        """
        self.auth = auth
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.retry_backoff = retry_backoff or self.DEFAULT_RETRY_BACKOFF
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "iCafe-Skill/0.1.0",
            "Accept": "application/json",
        })
        
        logger.info(
            f"Initialized ICafeClient: base_url={self.base_url}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}"
        )
    
    def _build_url(self, path: str) -> str:
        """
        Build full URL from path.
        
        Args:
            path: API path (e.g., '/api/spaces/test/cards/123')
            
        Returns:
            Full URL
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(self.base_url, path)
    
    def _inject_auth(self, params: Optional[Dict[str, Any]],
               json: Optional[Dict[str, Any]] = None,
               data: Optional[Dict[str, Any]] = None,
               path: str = "") -> Dict[str, Any]:
        """
        Inject authentication parameters into request.

        Args:
            params: Query parameters
            json: JSON body
            data: Form data
            path: API path (for determining auth param names)

        Returns:
            Updated params/json/data with auth added
        """
        # Determine auth params based on request context
        auth_params = self.auth.to_api_params(path=path)

        # Inject into appropriate location
        if params is not None:
            params = params or {}
            params.update(auth_params)
            return params
        elif json is not None:
            json.update(auth_params)
            return json
        elif data is not None:
            data.update(auth_params)
            return data

        return auth_params
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and convert errors to exceptions.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            AuthenticationError: For 401 errors
            AuthorizationError: For 403 errors
            ResourceNotFoundError: For 404 errors
            APIError: For other HTTP errors
        """
        # Log response
        logger.debug(
            f"Response: status={response.status_code}, "
            f"size={len(response.content)} bytes, "
            f"time={response.elapsed.total_seconds():.2f}s"
        )
        
        # Handle successful responses
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                # Response is not JSON, return text
                return {"text": response.text}
        
        # Handle error responses
        error_body = response.text
        
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Please check your username and password.",
                details={"status_code": 401, "response": error_body}
            )
        
        if response.status_code == 403:
            raise AuthorizationError(
                "Permission denied. You don't have access to this resource.",
                details={"status_code": 403, "response": error_body}
            )
        
        if response.status_code == 404:
            raise ResourceNotFoundError(
                "Resource not found. Please check the space ID, card ID, or other identifiers.",
                details={"status_code": 404, "response": error_body}
            )
        
        if response.status_code == 400:
            raise APIError(
                f"Bad request: {error_body}",
                status_code=400,
                response_body=error_body
            )
        
        if response.status_code >= 500:
            raise APIError(
                f"Server error: {error_body}",
                status_code=response.status_code,
                response_body=error_body
            )
        
        # Generic error
        raise APIError(
            f"API request failed with status {response.status_code}: {error_body}",
            status_code=response.status_code,
            response_body=error_body
        )
    
    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        Execute HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            **kwargs: Additional arguments for requests
            
        Returns:
            HTTP response
            
        Raises:
            NetworkError: For connection errors
            ICafeTimeoutError: For timeout errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Request attempt {attempt + 1}/{self.max_retries}: "
                    f"{method} {url}"
                )
                
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"Request error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = self.retry_backoff ** attempt
                logger.debug(f"Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
        
        # All retries failed
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise ICafeTimeoutError(
                f"Request timed out after {self.max_retries} attempts",
                details={"timeout": self.timeout}
            )
        else:
            raise NetworkError(
                f"Network error after {self.max_retries} attempts: {last_exception}",
                details={"original_error": str(last_exception)}
            )
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute GET request.

        Args:
            path: API path
            params: Query parameters (auth will be auto-injected)
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response
        """
        url = self._build_url(path)
        params = self._inject_auth(params, path=path)

        logger.info(f"GET {path}")
        logger.debug(f"Params: {self._mask_sensitive_data(params)}")

        response = self._request_with_retry(
            method="GET",
            url=url,
            params=params,
            **kwargs
        )

        return self._handle_response(response)
    
    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute POST request.

        Args:
            path: API path
            data: Form data (auth will be auto-injected if present)
            json: JSON body (auth will be auto-injected if present)
            params: Query parameters (auth will be auto-injected)
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response
        """
        url = self._build_url(path)

        # Inject auth into appropriate location
        if params is not None:
            params = self._inject_auth(params, path=path)
        elif json is not None:
            json = self._inject_auth(json, path=path)
        elif data is not None:
            data = self._inject_auth(data, path=path)
        else:
            # No parameters, use query params
            params = self._inject_auth(None, path=path)

        logger.info(f"POST {path}")
        if params:
            logger.debug(f"Params: {self._mask_sensitive_data(params)}")
        if json:
            logger.debug(f"JSON body: {self._mask_sensitive_data(json)}")

        response = self._request_with_retry(
            method="POST",
            url=url,
            data=data,
            json=json,
            params=params,
            **kwargs
        )

        return self._handle_response(response)
    
    def _mask_sensitive_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mask sensitive data in logs.
        
        Args:
            data: Data dictionary
            
        Returns:
            Dictionary with sensitive fields masked
        """
        if not data:
            return {}
        
        masked = data.copy()
        sensitive_keys = ["password", "pw", "token", "secret"]
        
        for key in sensitive_keys:
            if key in masked:
                value = str(masked[key])
                if len(value) > 4:
                    masked[key] = value[:4] + "*" * (len(value) - 4)
                else:
                    masked[key] = "***"
        
        return masked
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("HTTP session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()