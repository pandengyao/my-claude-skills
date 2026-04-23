#!/usr/bin/env python3
"""
Weiyun Log Query Tool
Query logs from Weiyun LogHub API with authentication
"""

import argparse
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

# Default config path (relative to script location)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config(config_path: Optional[Path] = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Please create a config.json with your API credentials.\n"
            f"Example format:\n"
            f'{{\n'
            f'  "ak": "your_access_key",\n'
            f'  "sk": "your_secret_key"\n'
            f'}}'
        )
    
    with open(config_path, 'r') as f:
        return json.load(f)


def generate_signature(sk: str, http_method: str, path: str, timestamp: str, nonce: str) -> str:
    """
    Generate HMAC-SHA256 signature for authentication.
    
    Signature algorithm:
    string_to_sign = HTTP_METHOD + "\n" + PATH + "\n" + TIMESTAMP + "\n" + NONCE
    signature = Base64(HMAC-SHA256(string_to_sign, SecretKey))
    
    Note: PATH should have the /eci-cloud-loghub prefix removed for signing.
    """
    # Remove /eci-cloud-loghub prefix from path for signature calculation
    sign_path = path
    if sign_path.startswith('/eci-cloud-loghub'):
        sign_path = sign_path[len('/eci-cloud-loghub'):]
    
    # Build sign string: HTTP_METHOD + \n + PATH + \n + TIMESTAMP + \n + NONCE
    sign_string = f"{http_method}\n{sign_path}\n{timestamp}\n{nonce}"
    
    # HMAC-SHA256 with secret key
    signature = hmac.new(
        sk.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Base64 encode
    import base64
    return base64.b64encode(signature).decode('utf-8')


def build_headers(ak: str, sk: str, http_method: str = "POST", path: str = "/eci-cloud-loghub/v1/openApi/queryLog/conditionQuery") -> dict:
    """
    Build authentication headers.
    
    Args:
        ak: Access Key
        sk: Secret Key
        http_method: HTTP method (default: POST)
        path: API path (default: /eci-cloud-loghub/v1/openApi/queryLog/conditionQuery)
    """
    timestamp = str(int(time.time() * 1000))
    nonce = timestamp  # Using timestamp as nonce
    signature = generate_signature(sk, http_method, path, timestamp, nonce)
    
    return {
        'X-AK': ak,
        'X-Timestamp': timestamp,
        'X-Nonce': nonce,
        'X-Signature': signature,
        'Content-Type': 'application/json'
    }


def query_logs(
    api_url: str,
    ak: str,
    sk: str,
    must: dict,
    start_time: str,
    end_time: str,
    timeout: int = 30
) -> dict:
    """
    Query logs from Weiyun LogHub API.
    
    Args:
        api_url: API endpoint URL
        ak: Access Key
        sk: Secret Key
        must: Query conditions (matchPhraseList, participleMatchList, etc.)
        start_time: Start timestamp in milliseconds
        end_time: End timestamp in milliseconds
        timeout: Request timeout in seconds
    
    Returns:
        API response as dictionary
    """
    # Extract path from URL for signature
    from urllib.parse import urlparse
    parsed_url = urlparse(api_url)
    path = parsed_url.path
    
    headers = build_headers(ak, sk, http_method="POST", path=path)
    
    payload = {
        "must": must,
        "endTime": end_time,
        "startTime": start_time
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    response.raise_for_status()
    return response.json()


def parse_match_phrase(key: str, value: str) -> dict:
    """Parse a match phrase condition."""
    return {key: value}


def main():
    parser = argparse.ArgumentParser(
        description='Query logs from Weiyun LogHub API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic query with product and app name
  %(prog)s --product new-gc-qa --app new-gc-dashboard-qa --message "error"
  
  # Query with custom time range (timestamps in milliseconds)
  %(prog)s --product new-gc-qa --start 1766661652540 --end 1766662552541
  
  # Query with multiple message keywords
  %(prog)s --product new-gc-qa --app new-gc-dashboard-qa --message "requestId" --message "error"
  
  # Use custom config file
  %(prog)s --config /path/to/config.json --product new-gc-qa
  
  # Output raw JSON
  %(prog)s --product new-gc-qa --output json
'''
    )
    
    # Authentication options
    parser.add_argument('--config', '-c', type=Path,
                        help='Path to config JSON file (default: skill config.json)')
    parser.add_argument('--ak', type=str, help='Access Key (overrides config)')
    parser.add_argument('--sk', type=str, help='Secret Key (overrides config)')
    
    # API options
    parser.add_argument('--url', type=str,
                        default='https://developer.weiyun.baidu.com/eci-cloud-loghub/v1/openApi/queryLog/conditionQuery',
                        help='API endpoint URL')
    
    # Query conditions - match phrases
    parser.add_argument('--product', type=str,
                        help='Product name (weiyun_prod_name)')
    parser.add_argument('--app', type=str,
                        help='App name (weiyun_app_name)')
    parser.add_argument('--match', '-m', nargs=2, action='append', metavar=('KEY', 'VALUE'),
                        help='Custom match phrase (can be used multiple times)')
    
    # Query conditions - participle match
    parser.add_argument('--message', type=str, action='append',
                        help='Message keyword to search (can be used multiple times)')
    
    # Time range
    parser.add_argument('--start', type=str,
                        help='Start timestamp in milliseconds')
    parser.add_argument('--end', type=str,
                        help='End timestamp in milliseconds')
    parser.add_argument('--last', type=str,
                        help='Time range from now (e.g., "1h", "30m", "1d")')
    
    # Output options
    parser.add_argument('--output', '-o', choices=['json', 'pretty', 'logs'],
                        default='pretty', help='Output format')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Load credentials
    try:
        config = {}
        if args.config or (not args.ak or not args.sk):
            config = load_config(args.config)
        
        ak = args.ak or config.get('ak')
        sk = args.sk or config.get('sk')
        
        if not ak or not sk:
            parser.error("Access Key and Secret Key are required (via --ak/--sk or config file)")
    except FileNotFoundError as e:
        parser.error(str(e))
    
    # Build must conditions
    must = {}
    match_phrase_list = []
    
    # Add product and app as match phrases
    if args.product:
        match_phrase_list.append({"weiyun_prod_name": args.product})
    if args.app:
        match_phrase_list.append({"weiyun_app_name": args.app})
    
    # Add custom match phrases
    if args.match:
        for key, value in args.match:
            match_phrase_list.append({key: value})
    
    if match_phrase_list:
        must['matchPhraseList'] = match_phrase_list
    
    # Add message keywords
    if args.message:
        must['participleMatchList'] = [{"message": msg} for msg in args.message]
    
    # Handle time range
    end_time = args.end
    start_time = args.start
    
    if args.last and (not start_time or not end_time):
        # Parse relative time
        now = int(time.time() * 1000)
        unit = args.last[-1]
        value = int(args.last[:-1])
        
        if unit == 's':
            delta = value * 1000
        elif unit == 'm':
            delta = value * 60 * 1000
        elif unit == 'h':
            delta = value * 60 * 60 * 1000
        elif unit == 'd':
            delta = value * 24 * 60 * 60 * 1000
        else:
            parser.error(f"Unknown time unit: {unit}. Use s/m/h/d")
        
        if not end_time:
            end_time = str(now)
        if not start_time:
            start_time = str(now - delta)
    
    if not start_time or not end_time:
        parser.error("Time range is required. Use --start/--end or --last")
    
    # Execute query
    try:
        result = query_logs(
            api_url=args.url,
            ak=ak,
            sk=sk,
            must=must,
            start_time=start_time,
            end_time=end_time,
            timeout=args.timeout
        )
        
        if args.output == 'json':
            print(json.dumps(result, ensure_ascii=False))
        elif args.output == 'logs':
            # Extract and print just the log messages
            if 'data' in result and 'logInfoList' in result['data']:
                for log in result['data']['logInfoList']:
                    if 'message' in log:
                        print(log['message'])
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:  # pretty
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()