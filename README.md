# Universal Broker Organization Automation

A secure Python toolkit for automating Snyk organization management with Universal Broker connections. This repository contains two complementary scripts that help you extract organizations from Snyk groups and connect them to Universal Broker instances at scale.

## 🔧 Scripts

### 1. `get_orgs_by_group.py`
Extracts all organizations from a Snyk group and saves them to a JSON file with pagination support.

**Features:**
- ✅ Fetches ALL organizations (handles pagination automatically)
- ✅ Secure path validation (prevents path traversal attacks)
- ✅ Rich metadata tracking
- ✅ Clean filename generation
- ✅ Uses environment variables for secure API token handling

### 2. `scale_broker_for_orgs.py`
Connects Snyk organizations to Universal Broker connections by reading from the JSON output of the first script.

**Features:**
- ✅ Batch processing with configurable delays
- ✅ Comprehensive logging and error handling
- ✅ Secure path validation
- ✅ Progress tracking and summaries
- ✅ Debug mode for troubleshooting
- ✅ Uses environment variables for secure credential handling

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- Python 3.7 or higher
- pip (Python package installer)

**Snyk Requirements:**
- Valid Snyk account with API access
- Snyk API token with appropriate permissions
- Snyk tenant ID (for Universal Broker operations)
- Access to the Snyk group you want to process

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd UB-repo
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Required packages:**
   - `requests` - For HTTP API calls to Snyk

3. **Get your Snyk credentials:**
   - **API Token:** Go to [Snyk Account Settings](https://app.snyk.io/account) → Generate API token
   - **Tenant ID:** Found in your Snyk URL or contact your Snyk admin
   - **Group ID:** Found in the Snyk group URL you want to process

### Usage

#### Step 1: Set Environment Variables
```bash
export SNYK_TOKEN=your_api_token_here
export TENANT_ID=your_tenant_id_here
```

#### Step 2: Extract Organizations
```bash
python get_orgs_by_group.py --group-id <your-group-id>
```

**Output:** Creates a JSON file with all organizations (e.g., `snyk_orgs_for_GroupName.json`).

#### Step 3: Connect to Universal Broker
```bash
python scale_broker_for_orgs.py \
  --json-file snyk_orgs_for_GroupName.json \
  --connection-id <your-connection-id> \
  --integration-id <your-integration-id> \
  --integration-type github
```

**Output:** Creates `connection_log.json` with results for each organization.

## 📋 Command Reference

### `get_orgs_by_group.py`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--group-id` | ✅ | Snyk group ID to fetch organizations from |
| `--output` | ❌ | Output JSON file path (auto-generated if not specified) |

**Environment Variables:**
- `SNYK_TOKEN` - Snyk API token for authentication ✅ Required
- `TENANT_ID` - Snyk tenant ID (optional for this script, but useful for workflow)

**Example:**
```bash
export SNYK_TOKEN=your_token_here
export TENANT_ID=your_tenant_id_here
python get_orgs_by_group.py --group-id abc123
```

### `scale_broker_for_orgs.py`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--json-file` | ✅ | Path to JSON file from `get_orgs_by_group.py` |
| `--connection-id` | ✅ | Universal Broker connection ID |
| `--integration-id` | ✅ | Integration ID for the broker connection |
| `--integration-type` | ✅ | Integration type (`github`, `gitlab`, `bitbucket`, etc.) |
| `--delay` | ❌ | Delay between API calls in seconds (default: 0.5) |
| `--output-log` | ❌ | Output log file (default: `connection_log.json`) |
| `--debug` | ❌ | Enable debug output |

**Environment Variables:**
- `SNYK_TOKEN` - Snyk API token for authentication ✅ Required
- `TENANT_ID` - Snyk tenant ID ✅ Required

**Example:**
```bash
# Environment variables should already be set from previous step
python scale_broker_for_orgs.py \
  --json-file snyk_orgs_for_GroupName.json \
  --connection-id conn456 \
  --integration-id github-integration \
  --integration-type github \
  --delay 1.0 \
  --debug
```

## 📄 Output Files

### Organizations JSON Structure
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

### Connection Log Structure
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

## � Security & Best Practices

### Environment Variables
Both scripts use environment variables for sensitive credentials:
- **More Secure:** Tokens don't appear in command history or process lists
- **Convenient:** Export once, use for both scripts
- **Standard Practice:** Industry standard for handling secrets

### Security Features
Both scripts include comprehensive security measures:

- **Path Traversal Protection:** All file paths are validated and sanitized
- **Input Validation:** API parameters and file contents are validated  
- **Safe File Operations:** Restricted to current working directory
- **Error Handling:** Graceful handling of API errors and network issues

## 🐛 Troubleshooting

### Prerequisites Check
Before running the scripts, ensure you have:

**For `get_orgs_by_group.py`:**
- ✅ Python 3.7+ installed
- ✅ `requests` library installed (`pip install requests`)
- ✅ `SNYK_TOKEN` environment variable set
- ✅ Valid Snyk group ID
- ✅ API token has permissions to read the group

**For `scale_broker_for_orgs.py`:**
- ✅ All requirements from first script
- ✅ `TENANT_ID` environment variable set
- ✅ Valid Universal Broker connection ID
- ✅ Valid integration ID and type
- ✅ JSON file from first script exists

### Common Issues

1. **Authentication Error (401):**
   ```
   Error: Authentication failed. Please check your API token.
   ```
   - Verify your `SNYK_TOKEN` is correct and not expired
   - Ensure the token has appropriate permissions
   - Check if you copied the token correctly (no extra spaces)

2. **Group Not Found (404):**
   ```
   Error: Group ID 'abc123' not found or you don't have access to it.
   ```
   - Check the group ID is correct
   - Verify you have access to the group
   - Ensure you're using the right Snyk organization

3. **Environment Variable Not Set:**
   ```
   Error: SNYK_TOKEN environment variable is not set.
   Error: TENANT_ID environment variable is not set.
   ```
   - Export the required environment variables:
     ```bash
     export SNYK_TOKEN=your_token_here
     export TENANT_ID=your_tenant_id_here
     ```

4. **Rate Limiting:**
   ```
   Error: Too many requests
   ```
   - Increase the `--delay` parameter (default: 0.5 seconds)
   - Try: `--delay 1.0` or higher

5. **Path Errors:**
   ```
   Error: Output path must be within /current/directory
   ```
   - Ensure you're running from the correct directory
   - Use relative paths or ensure files are in current directory
   - Check file permissions

6. **JSON Structure Errors:**
   ```
   Error: Unsupported JSON structure
   ```
   - Ensure the JSON file was created by `get_orgs_by_group.py`
   - Check the JSON file isn't corrupted
   - Verify the file contains organization data

### Debug Mode
Enable debug mode for detailed API request/response information:
```bash
python scale_broker_for_orgs.py [args] --debug
```

## 📊 Features Summary

| Feature | `get_orgs_by_group.py` | `scale_broker_for_orgs.py` |
|---------|----------------------|---------------------------|
| Pagination Support | ✅ | N/A |
| Environment Variables | ✅ | ✅ |
| Security Validation | ✅ | ✅ |
| Progress Tracking | ✅ | ✅ |
| Error Handling | ✅ | ✅ |
| Debug Mode | ❌ | ✅ |
| Rate Limiting | ❌ | ✅ |
| Comprehensive Logging | ✅ | ✅ |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.