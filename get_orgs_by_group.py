"""
Script to extract all organizations from a Snyk group ID using the Snyk API.
Saves the results to a JSON file.

Usage:
    1. First, export your Snyk API token and tenant ID:
       export SNYK_TOKEN=your_api_token_here
       export SNYK_TENANT_ID=your_tenant_id_here
    
    2. Then run the script:
       python get_orgs_by_group.py --group-id <group_id> [--output <output_file>]

"""

import requests
import json
import argparse
import sys
import os
import re


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
    if not abs_user_path.endswith('.json'):
        raise ValueError("Output file must have .json extension")
    
    return abs_user_path


def get_snyk_organizations(group_id, api_token):
    """
    Fetch all organizations from a Snyk group using the API with pagination support.
    
    Args:
        group_id (str): The Snyk group ID
        api_token (str): The Snyk API token
        
    Returns:
        dict: API response containing all organizations data
        
    Raises:
        requests.RequestException: If the API request fails
    """
    headers = {
        "Authorization": f"token {api_token}",
        "Content-Type": "application/json"
    }
    
    # Variables for pagination
    all_orgs = []
    page = 1
    per_page = 100  
    total_pages = None
    base_response = None
    
    try:
        print(f"Fetching organizations from group ID: {group_id}")
        
        while True:
            url = f"https://api.snyk.io/v1/group/{group_id}/orgs"
            params = {
                "page": page,
                "perPage": per_page
            }
            
            print(f"  Fetching page {page}" + (f" of {total_pages}" if total_pages else ""))
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Store the base response structure from the first page
            if base_response is None:
                base_response = data.copy()
                base_response['orgs'] = []  
            
            # Add organizations from this page
            orgs_on_page = data.get('orgs', [])
            all_orgs.extend(orgs_on_page)
            
            # Check if we have more pages
            if len(orgs_on_page) < per_page:
                # If we got fewer orgs than requested, we're on the last page
                print(f"  Completed: Found {len(all_orgs)} total organizations")
                break
            
            page += 1
            
            # Prevent infinite loops
            if page > 50:  # Assuming max 5000 organizations (50 * 100)
                print(f"  Warning: Stopped at page {page} to prevent infinite loop")
                break
        
        # Combine all organizations into the response
        base_response['orgs'] = all_orgs
        
        return base_response
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise requests.RequestException("Authentication failed. Please check your API token.")
        elif response.status_code == 404:
            raise requests.RequestException(f"Group ID '{group_id}' not found or you don't have access to it.")
        else:
            raise requests.RequestException(f"HTTP Error {response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Request failed: {e}")


def save_to_json(data, validated_output_file):
    """
    Save data to a JSON file with proper formatting.
    
    Args:
        data (dict): Data to save
        validated_output_file (str): Pre-validated output file path
    """
    try:
        with open(validated_output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved organizations data to: {validated_output_file}")
    except IOError as e:
        raise IOError(f"Failed to write to file '{validated_output_file}': {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract all organizations from a Snyk group ID and save to JSON file"
    )
    
    parser.add_argument(
        "--group-id",
        required=True,
        help="Snyk group ID to fetch organizations from"
    )
    
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: snyk_orgs_for_<group_name>.json)"
    )
    
    args = parser.parse_args()
    
    # Get API token from environment variable
    api_token = os.getenv('SNYK_TOKEN')
    if not api_token:
        print("Error: SNYK_TOKEN environment variable is not set.", file=sys.stderr)
        print("Please export your Snyk API token:", file=sys.stderr)
        print("  export SNYK_TOKEN=your_api_token_here", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Fetch organizations from Snyk API 
        orgs_data = get_snyk_organizations(args.group_id, api_token)
        
        # Extract group name directly from the API response
        group_name = orgs_data.get("name", args.group_id)
        print(f"Found group name: {group_name}")
        
        # Clean the group name to be filesystem-safe
        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_name)
        clean_group_name = re.sub(r'\s+', '_', clean_group_name)
        clean_group_name = clean_group_name.strip('_')
        
        # Generate default output filename if not provided
        if args.output is None:
            args.output = f"snyk_orgs_for_{clean_group_name}.json"
        
        # Validate and sanitize the output path
        try:
            validated_output_path = sanitize_output_path(args.output)
        except ValueError as e:
            print(f"Error with output path: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Get organizations from the API response
        orgs = orgs_data.get("orgs", [])
        
        print(f"Found {len(orgs)} organizations")
        
        # Add metadata to the response
        enriched_data = {
            "metadata": {
                "group_id": args.group_id,
                "group_name": group_name,
                "total_organizations": len(orgs)
            },
            "organizations": orgs_data
        }
        
        # Save to JSON file
        save_to_json(enriched_data, validated_output_path)
        
        # Print summary
        org_count = len(orgs)
        print(f"\nSummary:")
        print(f"- Group ID: {args.group_id}")
        print(f"- Group Name: {group_name}")
        print(f"- Total organizations found: {org_count}")
        print(f"- Output file: {validated_output_path}")
        
        if org_count > 0:
            print(f"\nFirst few organizations:")
            for i, org in enumerate(orgs[:3]):
                print(f"  {i+1}. {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
            if org_count > 3:
                print(f"  ... and {org_count - 3} more")
        
    except (requests.RequestException, IOError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

