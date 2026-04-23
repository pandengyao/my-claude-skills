#!/usr/bin/env python3
"""
iAPI Client - HTTP client for iAPI MCP Controller
Handles authentication and all API operations
"""

import os
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests


class IapiClient:
    """Client for interacting with iAPI MCP Controller"""

    BASE_URL = "https://iapi.now.baidu-int.com"

    def __init__(self):
        self.session = requests.Session()
        self.auth_token = self._get_auth_token()
        if self.auth_token:
            self.session.headers.update({
                'x-ac-Authorization': self.auth_token,
                'Content-Type': 'application/json'
            })

    def _get_auth_token(self) -> Optional[str]:
        """
        Get authentication token from environment variable or login file
        Priority: COMATE_AUTH_TOKEN env var > ~/.comate/login file
        """
        # Try environment variable first
        token = os.environ.get('COMATE_AUTH_TOKEN')

        # If not in env, try login file
        if not token:
            login_file = Path.home() / '.comate' / 'login'
            if login_file.exists():
                try:
                    token = login_file.read_text().strip()
                except Exception as e:
                    print(f"Warning: Failed to read login file: {e}", file=sys.stderr)

        # Add Bearer- prefix if not present
        if token and not token.startswith('Bearer-'):
            token = f'Bearer-{token}'

        return token

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and extract data"""
        try:
            result = response.json()
            if result.get('code') == 200:
                return {'success': True, 'data': result.get('data')}
            else:
                return {
                    'success': False,
                    'error': result.get('msg', 'Unknown error'),
                    'code': result.get('code')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse response: {str(e)}'
            }

    def get_api_detail(self, api_id: str, export_type: str = 'swagger') -> Dict[str, Any]:
        """
        Get API detail information

        Args:
            api_id: API ID (can be comma-separated multiple IDs)
            export_type: Export format, 'swagger' or 'markdown' (default: 'swagger')

        Returns:
            Dict with success status and data/error
        """
        url = f"{self.BASE_URL}/api/v1/iapi/api/detail"
        params = {
            'apiId': api_id,
            'exportType': export_type
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_api_list(self, project_id: str) -> Dict[str, Any]:
        """
        Get API list for a project

        Args:
            project_id: Project ID

        Returns:
            Dict with success status and data/error
        """
        url = f"{self.BASE_URL}/api/v1/iapi/api/list"
        params = {'projectId': project_id}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_editable_projects(self) -> Dict[str, Any]:
        """
        Get list of projects that the user can edit

        Returns:
            Dict with success status and data/error
        """
        url = f"{self.BASE_URL}/api/v1/iapi/projects/editable"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_projects(self) -> Dict[str, Any]:
        """
        Get all projects accessible to the user

        Returns:
            Dict with success status and data/error
        """
        url = f"{self.BASE_URL}/api/v1/iapi/projects/user"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_openapi(
        self,
        project_id: str,
        swagger_data: str,
        api_overwrite_mode: str = 'SKIP',
        schema_overwrite_mode: str = 'SKIP'
    ) -> Dict[str, Any]:
        """
        Import OpenAPI/Swagger specification into a project

        Args:
            project_id: Target project ID
            swagger_data: OpenAPI/Swagger JSON or YAML content
            api_overwrite_mode: How to handle existing APIs: 'SKIP', 'OVERWRITE', 'MERGE' (default: 'SKIP')
            schema_overwrite_mode: How to handle existing schemas: 'SKIP', 'OVERWRITE', 'MERGE' (default: 'SKIP')

        Returns:
            Dict with success status and import result
        """
        url = f"{self.BASE_URL}/api/v1/iapi/import/openapi"
        payload = {
            'projectId': project_id,
            'swaggerData': swagger_data,
            'apiOverwriteMode': api_overwrite_mode,
            'schemaOverwriteMode': schema_overwrite_mode
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def search_apis(
        self,
        query: str,
        num: int = 10,
        project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search APIs by natural language query

        Args:
            query: Natural language search query
            num: Maximum number of results to return (default: 10)
            project_ids: Optional list of project IDs to limit search scope

        Returns:
            Dict with success status and search results
        """
        url = f"{self.BASE_URL}/api/v1/iapi/api/search"
        payload = {
            'query': query,
            'num': num
        }
        if project_ids:
            payload['projectIds'] = project_ids

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return self._handle_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='iAPI Client CLI')
    parser.add_argument('action', choices=[
        'get-api-detail',
        'get-api-list',
        'get-editable-projects',
        'get-user-projects',
        'import-openapi',
        'search-apis'
    ])
    parser.add_argument('--api-id', help='API ID (for get-api-detail)')
    parser.add_argument('--export-type', default='swagger', help='Export type: swagger or markdown')
    parser.add_argument('--project-id', help='Project ID')
    parser.add_argument('--swagger-file', help='Path to OpenAPI/Swagger file (for import)')
    parser.add_argument('--api-overwrite', default='SKIP', help='API overwrite mode: SKIP, OVERWRITE, MERGE')
    parser.add_argument('--schema-overwrite', default='SKIP', help='Schema overwrite mode: SKIP, OVERWRITE, MERGE')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--num', type=int, default=10, help='Number of search results')
    parser.add_argument('--project-ids', nargs='+', help='Project IDs for search scope')

    args = parser.parse_args()

    client = IapiClient()

    if not client.auth_token:
        print("Error: No authentication token found. Set COMATE_AUTH_TOKEN or create ~/.comate/login", file=sys.stderr)
        sys.exit(1)

    result = None

    if args.action == 'get-api-detail':
        if not args.api_id:
            print("Error: --api-id required", file=sys.stderr)
            sys.exit(1)
        result = client.get_api_detail(args.api_id, args.export_type)

    elif args.action == 'get-api-list':
        if not args.project_id:
            print("Error: --project-id required", file=sys.stderr)
            sys.exit(1)
        result = client.get_api_list(args.project_id)

    elif args.action == 'get-editable-projects':
        result = client.get_editable_projects()

    elif args.action == 'get-user-projects':
        result = client.get_user_projects()

    elif args.action == 'import-openapi':
        if not args.project_id or not args.swagger_file:
            print("Error: --project-id and --swagger-file required", file=sys.stderr)
            sys.exit(1)
        swagger_data = Path(args.swagger_file).read_text()
        result = client.import_openapi(
            args.project_id,
            swagger_data,
            args.api_overwrite,
            args.schema_overwrite
        )

    elif args.action == 'search-apis':
        if not args.query:
            print("Error: --query required", file=sys.stderr)
            sys.exit(1)
        result = client.search_apis(args.query, args.num, args.project_ids)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
