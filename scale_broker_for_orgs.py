"""
Script to connect Snyk organizations to Universal Broker connection.
Reads organizations from a JSON file and connects each one to a provided Universal Broker connection.

"""

import requests
import json
import argparse
import sys
import os
import time
from datetime import datetime


def sanitize_input_path(user_path, base_dir=None):
    """
    Validate input file paths to prevent path traversal attacks.
    
    Args:
        user_path (str): User-provided file path
        base_dir (str): Base directory to restrict reads to (default: current dir)
    
    Returns:
        str: Validated absolute path
        
    Raises:
        ValueError: If path is outside allowed directory or invalid
        FileNotFoundError: If file doesn't exist
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    # Convert to absolute paths
    abs_user_path = os.path.abspath(user_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    # Check if the path is within the allowed directory
    if not abs_user_path.startswith(abs_base_dir):
        raise ValueError(f"Input path must be within {abs_base_dir}")
    
    # Check if file exists
    if not os.path.exists(abs_user_path):
        raise FileNotFoundError(f"File not found: {user_path}")
    
    # Ensure it's a JSON file
    if not abs_user_path.endswith('.json'):
        raise ValueError("Input file must be a JSON file")
    
    return abs_user_path


def sanitize_output_path(user_path, base_dir=None):
    """
    Validate and sanitize output file paths to prevent path traversal.
    
    Args:
        user_path (str): User-provided file path
        base_dir (str): Base directory to restrict writes to (default: current dir)
    
    Returns:
        str: Validated absolute path
        
    Raises:
        ValueError: If path is outside allowed directory or invalid
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    # Convert to absolute paths
    abs_user_path = os.path.abspath(user_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    # Check if the path is within the allowed directory
    if not abs_user_path.startswith(abs_base_dir):
        raise ValueError(f"Output path must be within {abs_base_dir}")
    
    # Ensure it's a valid file extension
    if not abs_user_path.endswith(('.json', '.log')):
        raise ValueError("Output file must have .json or .log extension")
    
    return abs_user_path


def load_organizations_from_json(validated_json_file_path):
    """
    Load organizations data from JSON file.
    
    Args:
        validated_json_file_path: Pre-validated path to the JSON file containing organizations
        
    Returns:
        list: List of organizations
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    try:
        with open(validated_json_file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if 'organizations' in data and 'orgs' in data['organizations']:
            # Structure from get_orgs_by_group.py with metadata
            orgs = data['organizations']['orgs']
        elif 'orgs' in data:
            # Direct structure from Snyk API
            orgs = data['orgs']
        elif isinstance(data, list):
            # Direct list of organizations
            orgs = data
        else:
            raise ValueError("Unsupported JSON structure. Expected 'orgs' key or list of organizations.")
        
        print(f"Loaded {len(orgs)} organizations from {validated_json_file_path}")
        
        return orgs
        
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {validated_json_file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {validated_json_file_path}: {e}")
    except ValueError as e:
        raise ValueError(f"Path validation error: {e}")


def connect_org_to_broker(tenant_id, connection_id, org_id, api_token, integration_id, integration_type, debug=False):
    """
    Connect a Snyk organization to a Universal Broker connection.
    
    Args:
        tenant_id (str): Snyk tenant ID
        connection_id (str): Universal Broker connection ID
        org_id (str): Snyk organization ID
        api_token (str): Snyk API token
        integration_id (str): Integration ID for the connection
        integration_type (str): Type of integration (e.g., 'github', 'gitlab', etc.)
        debug (bool): Enable debug output
        
    Returns:
        tuple: (success: bool, response_data: dict)
    """
    url = f"https://api.snyk.io/rest/tenants/{tenant_id}/brokers/connections/{connection_id}/orgs/{org_id}/integration?version=2024-02-08~experimental"
    
    headers = {
        "Authorization": f"token {api_token}",
        "Content-Type": "application/vnd.api+json"
    }
    
    # Request body as required by the API
    request_body = {
        "data": {
            "integration_id": integration_id,
            "type": integration_type
        }
    }
    
    if debug:
        print(f"    DEBUG: URL: {url}")
        print(f"    DEBUG: Headers: {headers}")
        print(f"    DEBUG: Body: {request_body}")
    
    try:
        response = requests.post(url, headers=headers, json=request_body)
        
        if debug:
            print(f"    DEBUG: Response Status: {response.status_code}")
            print(f"    DEBUG: Response Headers: {dict(response.headers)}")
            print(f"    DEBUG: Response Body: {response.text[:500]}")
        
        if response.status_code == 201:
            return True, response.json() if response.content else {"status": "success"}
        elif response.status_code == 200:
            return True, response.json() if response.content else {"status": "success"}
        elif response.status_code == 409:
            # Organization might already be connected
            return True, {"status": "already_connected", "message": "Organization already connected to broker"}
        else:
            return False, {
                "status_code": response.status_code,
                "error": response.text,
                "url": url,
                "message": f"Failed to connect organization {org_id}"
            }
            
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e), "message": f"Request failed for organization {org_id}"}


def main():
    """Main function to handle command line arguments and orchestrate the connection process."""
    parser = argparse.ArgumentParser(
        description="Connect Snyk organizations to Universal Broker connections"
    )
    
    parser.add_argument(
        "--json-file",
        required=True,
        help="Path to JSON file containing organizations data"
    )
    
    parser.add_argument(
        "--connection-id",
        required=True,
        help="Universal Broker connection ID"
    )
    
    parser.add_argument(
        "--integration-id",
        required=True,
        help="Integration ID for the broker connection"
    )
    
    parser.add_argument(
        "--integration-type",
        required=True,
        help="Type of integration (e.g., 'github', 'gitlab', 'bitbucket', etc.)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between API calls in seconds (default: 0.5)"
    )
    
    parser.add_argument(
        "--output-log",
        default=None,
        help="Output file to save connection results (default: connection_log_<timestamp>.json)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output to see detailed API requests and responses"
    )
    
    args = parser.parse_args()
    
    # Get API token and tenant ID from environment variables
    api_token = os.getenv('SNYK_TOKEN')
    if not api_token:
        print("Error: SNYK_TOKEN environment variable is not set.", file=sys.stderr)
        print("Please export your Snyk API token:", file=sys.stderr)
        print("  export SNYK_TOKEN=your_api_token_here", file=sys.stderr)
        sys.exit(1)
    
    tenant_id = os.getenv('TENANT_ID')
    if not tenant_id:
        print("Error: TENANT_ID environment variable is not set.", file=sys.stderr)
        print("Please export your Snyk tenant ID:", file=sys.stderr)
        print("  export TENANT_ID=your_tenant_id_here", file=sys.stderr)
        sys.exit(1)
    
    # Generate default log filename if not provided
    if args.output_log is None:
        args.output_log = "connection_log.json"    
    try:
        # Validate paths early in main function
        validated_json_path = sanitize_input_path(args.json_file)
        validated_log_path = sanitize_output_path(args.output_log)
        
        # Load organizations from JSON file
        organizations = load_organizations_from_json(validated_json_path)
        
        if not organizations:
            print("No organizations found in the JSON file.")
            return
        
        # Initialize counters and results
        total_orgs = len(organizations)
        successful_connections = 0
        failed_connections = 0
        results = []
        
        print(f"\nStarting connection process for {total_orgs} organizations...")
        print(f"Tenant ID: {tenant_id}")
        print(f"Connection ID: {args.connection_id}")
        print(f"Delay between calls: {args.delay} seconds")
        print("-" * 60)
        
        # Process each organization
        for i, org in enumerate(organizations, 1):
            org_id = org.get('id')
            org_name = org.get('name', 'Unknown')
            
            if not org_id:
                print(f"[{i}/{total_orgs}] Skipping organization (missing ID): {org_name}")
                failed_connections += 1
                results.append({
                    "org_id": None,
                    "org_name": org_name,
                    "success": False,
                    "error": "Missing organization ID",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            print(f"[{i}/{total_orgs}] Connecting {org_name} (ID: {org_id})...")
            
            # Connect organization to broker
            success, response_data = connect_org_to_broker(
                tenant_id, 
                args.connection_id, 
                org_id, 
                api_token,
                args.integration_id,
                args.integration_type,
                args.debug
            )
            
            # Record result
            result = {
                "org_id": org_id,
                "org_name": org_name,
                "success": success,
                "response": response_data,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            
            if success:
                successful_connections += 1
                status = response_data.get('status', 'connected')
                print(f"  ✅ Success - {status}")
            else:
                failed_connections += 1
                error_msg = response_data.get('message', 'Unknown error')
                print(f"  ❌ Failed - {error_msg}")
            
            # Add delay between requests to avoid rate limiting
            if i < total_orgs:
                time.sleep(args.delay)
        
        # Save results to log file
        log_data = {
            "summary": {
                "total_organizations": total_orgs,
                "successful_connections": successful_connections,
                "failed_connections": failed_connections,
                "tenant_id": tenant_id,
                "connection_id": args.connection_id,
                "timestamp": datetime.now().isoformat()
            },
            "results": results
        }
        
        # Validate and sanitize the output log path
        safe_log_path = validated_log_path
        
        with open(safe_log_path, 'w') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("-" * 60)
        print(f"\nConnection Summary:")
        print(f"  Total organizations processed: {total_orgs}")
        print(f"  Successful connections: {successful_connections}")
        print(f"  Failed connections: {failed_connections}")
        print(f"  Log file: {validated_log_path}")
        
        if failed_connections > 0:
            print(f"\nFailed organizations:")
            for result in results:
                if not result['success']:
                    error_msg = result['response'].get('message', 'Unknown error')
                    print(f"  - {result['org_name']} (ID: {result['org_id']}): {error_msg}")
        
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()