# Universal Broker Organization Automation

A secure Python toolkit for automating Snyk organization management with Universal Broker connections. This repository contains two complementary scripts that help you extract organizations from Snyk groups and connect them to Universal Broker instances at scale.

## 🔧 Scripts

### 1. `get_orgs_by_group.py`
Extracts all organizations from a Snyk group and saves them to a JSON file with pagination support.

**Features:**
- ✅ Fetches ALL organizations (handles pagination automatically)
- ✅ Filters out default organizations (`<GroupName>-default`)
- ✅ Secure path validation (prevents path traversal attacks)
- ✅ Rich metadata and exclusion tracking
- ✅ Clean filename generation

### 2. `scale_broker_for_orgs.py`
Connects Snyk organizations to Universal Broker connections by reading from the JSON output of the first script.

**Features:**
- ✅ Batch processing with configurable delays
- ✅ Skips excluded organizations automatically
- ✅ Comprehensive logging and error handling
- ✅ Secure path validation
- ✅ Progress tracking and summaries
- ✅ Debug mode for troubleshooting

## 🚀 Quick Start

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

3. **Set up your Snyk API token:**
   - Go to [Snyk Account Settings](https://app.snyk.io/account)
   - Generate an API token
   - Keep it secure and ready for use

### Usage

#### Step 1: Extract Organizations
```bash
python get_orgs_by_group.py \
  --group-id <your-group-id> \
  --api-token <your-snyk-api-token> \
  --output snyk_orgs_for_mygroup.json
```

**Output:** Creates a JSON file with all organizations, excluding default ones.

#### Step 2: Connect to Universal Broker
```bash
python scale_broker_for_orgs.py \
  --json-file snyk_orgs_for_mygroup.json \
  --tenant-id <your-tenant-id> \
  --connection-id <your-connection-id> \
  --api-token <your-snyk-api-token> \
  --integration-id <your-integration-id> \
  --integration-type github
```

**Output:** Creates a connection log with results for each organization.

## 📋 Command Reference

### `get_orgs_by_group.py`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--group-id` | ✅ | Snyk group ID to fetch organizations from |
| `--api-token` | ✅ | Snyk API token for authentication |
| `--output` | ❌ | Output JSON file path (auto-generated if not specified) |

**Example:**
```bash
python get_orgs_by_group.py --group-id abc123 --api-token token456
```

### `scale_broker_for_orgs.py`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--json-file` | ✅ | Path to JSON file from `get_orgs_by_group.py` |
| `--tenant-id` | ✅ | Snyk tenant ID |
| `--connection-id` | ✅ | Universal Broker connection ID |
| `--api-token` | ✅ | Snyk API token |
| `--integration-id` | ✅ | Integration ID for the broker connection |
| `--integration-type` | ✅ | Integration type (`github`, `gitlab`, `bitbucket`, etc.) |
| `--delay` | ❌ | Delay between API calls in seconds (default: 0.5) |
| `--output-log` | ❌ | Output log file (auto-generated if not specified) |
| `--debug` | ❌ | Enable debug output |

**Example:**
```bash
python scale_broker_for_orgs.py \
  --json-file snyk_orgs_for_mygroup.json \
  --tenant-id tenant123 \
  --connection-id conn456 \
  --api-token token789 \
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
    "total_organizations": 25,
    "excluded_count": 1
  },
  "organizations": {
    "orgs": [
      {
        "id": "org123",
        "name": "Frontend Team",
        "url": "https://api.snyk.io/org/org123"
      }
    ]
  },
  "excluded_organizations": [...]
}
```

### Connection Log Structure
```json
{
  "summary": {
    "total_organizations": 25,
    "successful_connections": 24,
    "failed_connections": 1,
    "success_rate": 96.0
  },
  "results": [...],
  "excluded_organizations": [...]
}
```

## 🔒 Security Features

Both scripts include comprehensive security measures:

- **Path Traversal Protection:** All file paths are validated and sanitized
- **Input Validation:** API parameters and file contents are validated
- **Safe File Operations:** Restricted to current working directory
- **Error Handling:** Graceful handling of API errors and network issues

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Error (401):**
   - Verify your Snyk API token is correct
   - Ensure the token has appropriate permissions

2. **Group Not Found (404):**
   - Check the group ID is correct
   - Verify you have access to the group

3. **Rate Limiting:**
   - Increase the `--delay` parameter
   - Default is 0.5 seconds between requests

4. **Path Errors:**
   - Ensure you're running from the correct directory
   - Use absolute paths if needed

### Debug Mode
Enable debug mode for detailed API request/response information:
```bash
python scale_broker_for_orgs.py [args] --debug
```

## 📊 Features Summary

| Feature | `get_orgs_by_group.py` | `scale_broker_for_orgs.py` |
|---------|----------------------|---------------------------|
| Pagination Support | ✅ | N/A |
| Exclusion Filtering | ✅ | ✅ |
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