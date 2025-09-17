# Universal Broker Multi-Org Connector


**Automate Snyk organization management and integrate a single Universal Broker connection across multiple organizations with Python scripts.**

![Snyk OSS Example](https://raw.githubusercontent.com/snyk-labs/oss-images/main/oss-example.jpg)

This repo provides:
- Extraction of Snyk organizations by group
- Bulk integration of a Universal Broker connection to multiple organizations


## Scripts

### `get_orgs_by_group.py`
Extracts all organizations from a Snyk group and saves them to a JSON file.

### `scale_broker_for_orgs.py`
Integrates organizations to a single Universal Broker connection using the JSON output from the first script. Please remove organizations from the JSON that you don't want to scale the connection out for.

## Requirements

- Python 3.7+
- pip
- Snyk account with API access
- **Environment variables only:**
  - `SNYK_API_TOKEN` (required)
  - `SNYK_TENANT_ID` (required)


> **Note:** All instructions below work in both `zsh` and `bash` shells.

## Installation

### Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

## Usage

### 1. Export credentials
```bash
export SNYK_API_TOKEN=your_api_token_here
export SNYK_TENANT_ID=your_tenant_id_here
```

### 2. Extract organizations
```bash
python get_orgs_by_group.py --group-id <your-group-id>
```

### 3. Connect organizations to Universal Broker
```bash
python scale_broker_for_orgs.py \
  --json-file snyk_orgs_for_GroupName.json \
  --connection-id <your-connection-id> \
  --integration-id <your-integration-id> \
  --integration-type github
```

## Command Reference

### `get_orgs_by_group.py`
| Argument      | Required | Description                                 |
|--------------|----------|---------------------------------------------|
| --group-id   | Yes      | Snyk group ID to fetch organizations from   |
| --output     | No       | Output JSON file path (auto-generated)      |

### `scale_broker_for_orgs.py`
| Argument         | Required | Description                                 |
|------------------|----------|---------------------------------------------|
| --json-file      | Yes      | Path to JSON file from previous script      |
| --connection-id  | Yes      | Universal Broker connection ID              |
| --integration-id | Yes      | Integration ID for the broker connection    |
| --integration-type| Yes     | Integration type (github, gitlab, etc.)     |
| --output-log     | No       | Output log file (default: auto-generated)   |


## Output Files

### Organizations JSON
```json
{
  "metadata": {
    "group_id": "abc123",
    "group_name": "My Company",
    "total_organizations": 25
  },
  "organizations": {
    "orgs": [
      {
        "id": "org123",
        "name": "Frontend Team",
        "url": "https://api.snyk.io/org/org123"
      }
    ]
  }
}
```

### Connection Log JSON
```json
{
  "summary": {
    "total_organizations": 25,
    "successful_connections": 24,
    "failed_connections": 1,
    "tenant_id": "tenant123",
    "connection_id": "conn456",
    "timestamp": "2025-07-24T14:28:00.123456"
  },
  "results": [
    {
      "org_id": "org123",
      "org_name": "Frontend Team",
      "success": true,
      "response": {"status": "connected"},
      "timestamp": "2025-07-24T14:28:01.123456"
    }
  ]
}
```

## License

MIT 