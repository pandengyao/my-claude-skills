"""
Authentication configuration management for iCafe Skill.

This module provides utilities to load and manage authentication credentials
from configuration files.
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from .exceptions import AuthenticationError, ValidationError


class AuthConfig:
    """
    Manages authentication configuration for iCafe API.

    Supports loading credentials from:
    - YAML configuration files
    - Direct instantiation
    """
    
    def __init__(self, username: str, password: str):
        """
        Initialize authentication configuration.
        
        Args:
            username: iCafe username (email prefix)
            password: Virtual password for API access
            
        Raises:
            ValidationError: If username or password is empty
        """
        if not username or not username.strip():
            raise ValidationError("Username cannot be empty")
        if not password or not password.strip():
            raise ValidationError("Password cannot be empty")
        
        self.username = username.strip()
        self.password = password.strip()

    @classmethod
    def from_file(cls, config_path: str) -> "AuthConfig":
        """
        Load authentication configuration from a YAML file.

        Expected YAML structure:
        ```yaml
        auth:
          username: "your_username"
          password: "your_password"
        ```

        Args:
            config_path: Path to YAML configuration file (relative or absolute)

        Returns:
            AuthConfig instance

        Raises:
            AuthenticationError: If file doesn't exist or is malformed
            ValidationError: If required fields are missing
        """
        path = Path(config_path)

        # If path is relative, try multiple locations
        if not path.is_absolute():
            # Try current working directory first
            if path.exists():
                pass  # path is already valid
            else:
                # Try relative to the icafe_skill package directory
                # This helps when scripts are run from different locations
                package_dir = Path(__file__).parent.parent
                alt_path = package_dir / config_path
                if alt_path.exists():
                    path = alt_path
                else:
                    raise AuthenticationError(
                        f"Configuration file not found: {config_path}\n"
                        f"Tried locations:\n"
                        f"  - {Path.cwd() / config_path}\n"
                        f"  - {alt_path}"
                    )

        if not path.exists():
            raise AuthenticationError(
                f"Configuration file not found: {config_path}"
            )
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise AuthenticationError(
                f"Failed to parse YAML configuration: {e}"
            )
        except Exception as e:
            raise AuthenticationError(
                f"Failed to read configuration file: {e}"
            )
        
        if not isinstance(config, dict):
            raise ValidationError("Configuration file must contain a dictionary")
        
        auth_config = config.get("auth", {})
        if not isinstance(auth_config, dict):
            raise ValidationError("'auth' section must be a dictionary")
        
        username = auth_config.get("username")
        password = auth_config.get("password")
        
        if not username:
            raise ValidationError("Missing 'username' in auth configuration")
        if not password:
            raise ValidationError("Missing 'password' in auth configuration")
        
        return cls(username=username, password=password)

    @classmethod
    def from_test_config(cls, config_path: str = "config/config.yaml") -> "AuthConfig":
        """
        Load authentication configuration for testing.

        This is a convenience method that loads from the default test config location.

        Args:
            config_path: Path to configuration file (default: config/config.yaml)

        Returns:
            AuthConfig instance

        Raises:
            AuthenticationError: If file doesn't exist or is malformed
        """
        return cls.from_file(config_path)

    def to_dict(self) -> Dict[str, str]:
        """
        Convert authentication config to dictionary.
        
        Returns:
            Dictionary with 'username' and 'password' keys
        """
        return {
            "username": self.username,
            "password": self.password
        }
    
    def to_api_params(self, path: str = "") -> Dict[str, str]:
        """
        Convert to API parameter format.

        Different iCafe APIs use different authentication parameter names:
        - username/password: Most v2 APIs and POST body requests
        - u/pw: Legacy v1 APIs (/api/spaces/)

        Args:
            path: API path (e.g., '/api/v2/space/edc-scrum/issueTypes')

        Returns:
            Dictionary with appropriate auth parameter names
        """
        # Legacy v1 APIs use u/pw
        if path.startswith("/api/spaces/"):
            return {
                "u": self.username,
                "pw": self.password
            }

        # v2 APIs use username/password
        return {
            "username": self.username,
            "password": self.password
        }
    
    def __repr__(self) -> str:
        # Mask password for security
        masked_password = self.password[:4] + "*" * (len(self.password) - 4)
        return f"AuthConfig(username='{self.username}', password='{masked_password}')"


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Load full configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dictionary with full configuration
        
    Raises:
        ValidationError: If file doesn't exist or is malformed
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ValidationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise ValidationError(f"Failed to read configuration file: {e}")