import requests
import json
import argparse
import sys
import os
from datetime import datetime


# Validate and sanitize input file paths 
def sanitize_input_path(user_path, base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()
    
    abs_user_path = os.path.abspath(user_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    if not abs_user_path.startswith(abs_base_dir):
        raise ValueError(f"Input path must be within {abs_base_dir}")

    if not os.path.exists(abs_user_path):
        raise FileNotFoundError(f"File not found: {user_path}")
    
    if not abs_user_path.endswith('.json'):
        raise ValueError("Input file must be a JSON file")
    
    return abs_user_path


# Validate and sanitize output file paths
def sanitize_output_path(user_path, base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()
    
    abs_user_path = os.path.abspath(user_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    if not abs_user_path.startswith(abs_base_dir):
        raise ValueError(f"Output path must be within {abs_base_dir}")
    
    if not abs_user_path.endswith(('.json', '.log')):
        raise ValueError("Output file must have .json or .log extension")
    
    return abs_user_path


# Connect organization to Universal Broker
def connect_org_to_broker(tenant_id, connection_id, org_id, api_token, integration_id, integration_type):
    url = f"https://api.snyk.io/rest/tenants/{tenant_id}/brokers/connections/{connection_id}/orgs/{org_id}/integration?version=2024-02-08~experimental"
    
    headers = {
        "Authorization": f"token {api_token}",
        "Content-Type": "application/vnd.api+json"
    }
    
    request_body = {
        "data": {
            "integration_id": integration_id,
            "type": integration_type
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=request_body)
        
        if response.status_code in [200, 201]:
            return True, response.json() if response.content else {"status": "success"}
        elif response.status_code == 409:
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
        "--output-log",
        default=None,
        help="Output file to save connection results (default: connection_log_<timestamp>.json)"
    )
    
    args = parser.parse_args()
    
    # Get tenant ID from argument or environment variable
    tenant_id = os.environ.get('SNYK_TENANT_ID')
    api_token = os.environ.get('SNYK_API_TOKEN')
    if not tenant_id:
        print("Error: SNYK_TENANT_ID environment variable must be set", file=sys.stderr)
        sys.exit(1)
    if not api_token:
        print("Error: SNYK_API_TOKEN environment variable must be set", file=sys.stderr)
        sys.exit(1)
    
    # Generate default log filename if not provided
    if args.output_log is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_log = f"connection_log_{timestamp}.json"
    
    try:
        # Validate paths early in main function
        validated_json_path = sanitize_input_path(args.json_file)
        validated_log_path = sanitize_output_path(args.output_log)
        
        # Load organizations from JSON file
        with open(validated_json_path, 'r') as f:
            data = json.load(f)
        
        if 'organizations' in data and 'orgs' in data['organizations']:
            organizations = data['organizations']['orgs']
        elif 'orgs' in data:
            organizations = data['orgs']
        elif isinstance(data, list):
            organizations = data
        else:
            raise ValueError("Unsupported JSON structure. Expected 'orgs' key or list of organizations.")
        
        if not organizations:
            print("No organizations found in the JSON file.")
            return
        
        print(f"Loaded {len(organizations)} organizations")
        
        # Initialize counters and results
        total_orgs = len(organizations)
        successful_connections = 0
        failed_connections = 0
        results = []
        
        print(f"Starting connection process...")
        print(f"Tenant ID: {tenant_id}")
        print(f"Connection ID: {args.connection_id}")
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
            
            success, response_data = connect_org_to_broker(
                tenant_id, 
                args.connection_id, 
                org_id, 
                api_token,
                args.integration_id,
                args.integration_type
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
        
        with open(validated_log_path, 'w') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print("-" * 60)
        print(f"\nConnection Summary:")
        print(f"  Total organizations: {total_orgs}")
        print(f"  Successful connections: {successful_connections}")
        print(f"  Failed connections: {failed_connections}")
        print(f"  Success rate: {(successful_connections/total_orgs)*100:.1f}%")
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