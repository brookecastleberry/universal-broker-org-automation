"""
Script to extract all organizations from a Snyk group ID using the Snyk API.
Saves the results to a JSON file.

Usage:
    python get_orgs.py --group-id <group_id> --api-token <api_token> [--output <output_file>]
"""

import requests
import json
import argparse
import sys
from datetime import datetime


def get_snyk_organizations(group_id, api_token):
    """
    Fetch all organizations from a Snyk group using the API.
    
    Args:
        group_id (str): The Snyk group ID
        api_token (str): The Snyk API token
        
    Returns:
        dict: API response containing organizations data
        
    Raises:
        requests.RequestException: If the API request fails
    """
    url = f"https://api.snyk.io/v1/group/{group_id}/orgs"

    headers = {
        "Authorization": f"token {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Fetching organizations from group ID: {group_id}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise requests.RequestException("Authentication failed. Please check your API token.")
        elif response.status_code == 404:
            raise requests.RequestException(f"Group ID '{group_id}' not found or you don't have access to it.")
        else:
            raise requests.RequestException(f"HTTP Error {response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Request failed: {e}")


def save_to_json(data, output_file):
    """
    Save data to a JSON file with proper formatting.
    
    Args:
        data (dict): Data to save
        output_file (str): Output file path
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved organizations data to: {output_file}")
    except IOError as e:
        raise IOError(f"Failed to write to file '{output_file}': {e}")


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
    
    parser.add_argument(
        "--api-token",
        required=True,
        help="Snyk API token for authentication"
    )
    
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: snyk_orgs_for_<group_name>.json)"
    )
    
    args = parser.parse_args()
    
    try:
        # Fetch organizations from Snyk API (includes group name)
        orgs_data = get_snyk_organizations(args.group_id, args.api_token)
        
        # Extract group name directly from the API response
        group_name = orgs_data.get("name", args.group_id)
        print(f"Found group name: {group_name}")
        
        # Clean the group name to be filesystem-safe
        import re
        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_name)
        clean_group_name = re.sub(r'\s+', '_', clean_group_name)
        clean_group_name = clean_group_name.strip('_')
        
        # Generate default output filename if not provided
        if args.output is None:
            args.output = f"snyk_orgs_for_{clean_group_name}.json"
        
        # Filter out the specific organization named "<GroupName>-default"
        original_orgs = orgs_data.get("orgs", [])
        filtered_orgs = []
        excluded_orgs = []
        
        # Create the expected default organization name (use original group name for matching)
        expected_default_name = f"{group_name}-default"
        
        for org in original_orgs:
            org_name = org.get("name", "")
            # Check if the organization name exactly matches "<GroupName>-default"
            if org_name.lower() == expected_default_name.lower():
                excluded_orgs.append(org)
                print(f"Excluding organization: {org_name} (matches '{expected_default_name}' pattern)")
            else:
                filtered_orgs.append(org)
        
        # Update the orgs data with filtered organizations
        orgs_data["orgs"] = filtered_orgs
        
        print(f"Original organizations: {len(original_orgs)}")
        print(f"Filtered organizations: {len(filtered_orgs)}")
        print(f"Excluded organizations: {len(excluded_orgs)}")
        
        # Add metadata to the response
        enriched_data = {
            "metadata": {
                "group_id": args.group_id,
                "group_name": group_name,
                "timestamp": datetime.now().isoformat(),
                "total_organizations": len(filtered_orgs),
                "original_count": len(original_orgs),
                "excluded_count": len(excluded_orgs),
                "filter_criteria": f"Excluded organization named '{expected_default_name}'",
                "api_endpoint": f"https://api.snyk.io/v1/group/{args.group_id}/orgs"
            },
            "organizations": orgs_data,
            "excluded_organizations": excluded_orgs
        }
        
        # Save to JSON file
        save_to_json(enriched_data, args.output)
        
        # Print summary
        org_count = len(filtered_orgs)
        print(f"\nSummary:")
        print(f"- Group ID: {args.group_id}")
        print(f"- Group Name: {group_name}")
        print(f"- Total organizations found: {org_count}")
        print(f"- Organizations excluded: {len(excluded_orgs)}")
        print(f"- Output file: {args.output}")
        
        if org_count > 0:
            print(f"\nFirst few organizations:")
            for i, org in enumerate(filtered_orgs[:3]):
                print(f"  {i+1}. {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
            if org_count > 3:
                print(f"  ... and {org_count - 3} more")
        
        if excluded_orgs:
            print(f"\nExcluded organizations:")
            for org in excluded_orgs:
                print(f"  - {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
        
    except (requests.RequestException, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

