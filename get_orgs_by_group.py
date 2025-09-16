import requests
import json
import argparse
import sys
import os
import re
from datetime import datetime


# Validate and sanitize output file paths
def sanitize_output_path(user_path, base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()

    abs_user_path = os.path.abspath(user_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    if not abs_user_path.startswith(abs_base_dir):
        raise ValueError(f"Output path must be within {abs_base_dir}")
    
    if not abs_user_path.endswith('.json'):
        raise ValueError("Output file must have .json extension")
    
    return abs_user_path


# Fetch organizations from Snyk Group
def get_snyk_organizations(group_id, api_token):
    headers = {
        "Authorization": f"token {api_token}",
        "Content-Type": "application/json"
    }
    
    all_orgs = []
    page = 1
    per_page = 100
    base_response = None
    
    try:
        print(f"Fetching organizations from group ID: {group_id}")
        
        while True:
            url = f"https://api.snyk.io/v1/group/{group_id}/orgs"
            params = {
                "page": page,
                "perPage": per_page
            }
            
            print(f"  Fetching page {page}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if base_response is None:
                base_response = data.copy()
                base_response['orgs'] = []  
            
            orgs_on_page = data.get('orgs', [])
            all_orgs.extend(orgs_on_page)
            
            if len(orgs_on_page) < per_page:
                print(f"  Completed: Found {len(all_orgs)} total organizations")
                break
            
            page += 1
            
            if page > 50: 
                print(f"  Warning: Stopped at page {page} to prevent infinite loop")
                break
        
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



# Save data to a JSON file 
def save_to_json(data, validated_output_file):
    try:
        with open(validated_output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved organizations data to: {validated_output_file}")
    except IOError as e:
        raise IOError(f"Failed to write to file '{validated_output_file}': {e}")



def main():
    """Main function to handle command line arguments and orchestrate the process."""
    parser = argparse.ArgumentParser(
        description="Extract all organizations from a Snyk group ID and save to JSON file"
    )
    
    parser.add_argument(
        "--group-id",
        required=True,
        help="Snyk group ID to fetch organizations from"
    )
    
    #Remove this
    
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: snyk_orgs_for_<group_name>.json)"
    )
    

    args = parser.parse_args()
    api_token = os.environ.get('SNYK_API_TOKEN')
    if not api_token:
        print("Error: SNYK_API_TOKEN environment variable must be set", file=sys.stderr)
        sys.exit(1)

    try:
        # Fetch organizations from Snyk API
        orgs_data = get_snyk_organizations(args.group_id, api_token)

        # Extract group name and clean it to be filesystem-safe
        group_name = orgs_data.get("name", args.group_id)
        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_name)
        clean_group_name = re.sub(r'\s+', '_', clean_group_name)
        clean_group_name = clean_group_name.strip('_')

        # Generate default output filename if not provided
        if args.output is None:
            args.output = f"snyk_orgs_for_{clean_group_name}.json"

        # Validate and sanitize the output
        validated_output_path = sanitize_output_path(args.output)

        # Get organizations from the response
        organizations = orgs_data.get("orgs", [])

        # Add metadata to the response
        enriched_data = {
            "metadata": {
                "group_id": args.group_id,
                "group_name": group_name,
                "timestamp": datetime.now().isoformat(),
                "total_organizations": len(organizations),
                "api_endpoint": f"https://api.snyk.io/v1/group/{args.group_id}/orgs"
            },
            "organizations": orgs_data
        }

        # Save to JSON file
        save_to_json(enriched_data, validated_output_path)

        # Print summary
        print(f"\nSummary:")
        print(f"- Group ID: {args.group_id}")
        print(f"- Group Name: {group_name}")
        print(f"- Total organizations: {len(organizations)}")
        print(f"- Output file: {validated_output_path}")

        if len(organizations) > 0:
            print(f"\nFirst few organizations:")
            for i, org in enumerate(organizations[:3]):
                print(f"  {i+1}. {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
            if len(organizations) > 3:
                print(f"  ... and {len(organizations) - 3} more")
    except (requests.RequestException, IOError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

