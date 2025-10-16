# jirahhh

Utilities for creating and managing Jira issues with proper formatting and markdown support.

## Features

- Create, update, view, and search Jira issues from the command line
- Automatic conversion of Markdown files to Jira wiki markup
- Support for custom fields and security levels via configuration
- Multiple environment support (staging, production, etc.)
- Proxy support for corporate networks
- Generic API access for advanced use cases

## Installation

### Using uv (Recommended)

No installation required! Run directly with `uv`:

```bash
uvx --from git+https://github.com/shanemcd/jirahhh jirahhh create --help
```

Or clone and run locally:

```bash
git clone https://github.com/shanemcd/jirahhh.git
cd jirahhh
uv run jirahhh create --help
```

### Traditional pip install

```bash
pip install -e .
```

Then use the CLI directly:
```bash
jirahhh create --help
```

## Configuration

Copy `.jira-config.example.yaml` to `.jira-config.yaml` and configure your Jira instances:

```yaml
staging:
  url: "https://your-jira-instance.example.com"
  token: "your-api-token-here"
  # Optional: proxy for environments that require it
  # proxy: "http://proxy.example.com:3128"

production:
  url: "https://jira.example.com"
  token: "your-production-api-token-here"

# Optional: Define custom field mappings for your Jira instance
custom_fields:
  acceptance_criteria: "customfield_10001"
  epic_name: "customfield_10002"
  parent_link: "customfield_10003"
  epic_link: "customfield_10004"

# Optional: Define security level IDs
security_levels:
  default: "10000"
  confidential: "10001"
```

### Getting Your API Token

Generate a Jira API token from: **Jira > Profile > Personal Access Tokens**

## Quick Start

### Create an issue

```bash
jirahhh create \
  --env staging \
  --project PROJ \
  --type Task \
  --summary "My Task" \
  --description path/to/description.md \
  --acceptance-criteria "- Criteria 1\n- Criteria 2"
```

**Note:** The `--description` parameter auto-detects file types:
- `.md` files are automatically converted from Markdown to Jira format
- `.txt` files are used as-is (expected to be in Jira wiki markup)
- Inline text is treated as Jira wiki markup

### Update an issue

```bash
jirahhh update PROJ-123 \
  --env production \
  --summary "Updated Title"
```

### View an issue

```bash
jirahhh view PROJ-123 \
  --env production
```

View with specific fields:
```bash
jirahhh view PROJ-123 \
  --env staging \
  --fields "summary,status,description"
```

### Search for issues

```bash
jirahhh search "project = PROJ AND status = Open" \
  --env production \
  --max-results 10
```

### Discover available fields

```bash
jirahhh fields \
  --env production \
  --project PROJ \
  --type Epic
```

## License

MIT
