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

## Prerequisites

- **pandoc**: Required for automatic Markdown to Jira wiki markup conversion
  - Install on macOS: `brew install pandoc`
  - Install on Ubuntu/Debian: `sudo apt-get install pandoc`
  - Install on Fedora: `sudo dnf install pandoc`
  - See [pandoc.org](https://pandoc.org/installing.html) for other platforms

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

### Make generic API calls

For advanced use cases not covered by the built-in commands, use the `api` subcommand to call any Jira REST API endpoint directly:

```bash
# GET request - fetch comments on an issue
jirahhh api GET /rest/api/2/issue/PROJ-123/comment \
  --env production

# POST request - add a comment to an issue
jirahhh api POST /rest/api/2/issue/PROJ-123/comment \
  --env production \
  --data '{"body": "This is a comment added via the API"}'

# PUT request - update a comment
jirahhh api PUT /rest/api/2/issue/PROJ-123/comment/12345 \
  --env production \
  --data '{"body": "Updated comment text"}'

# DELETE request - delete a comment
jirahhh api DELETE /rest/api/2/issue/PROJ-123/comment/12345 \
  --env production
```

Supported HTTP methods: `GET`, `POST`, `PUT`, `DELETE`

## Tips

### Create a shell alias

For frequent use, create an alias in your shell configuration:

```bash
alias jirahhh='uvx --from "git+https://github.com/shanemcd/jirahhh" jirahhh'
```

Then use it directly:

```bash
jirahhh view PROJ-123 --env production
```

### Draft workflow with markdown files

For complex issues, organize your content in markdown files before creating:

```
my-feature/
├── description.md
└── acceptance-criteria.md
```

Then create the issue:

```bash
jirahhh create \
  --env production \
  --project PROJ \
  --type Story \
  --summary "Implement new feature" \
  --description my-feature/description.md \
  --acceptance-criteria my-feature/acceptance-criteria.md
```

### Finding child issues with JQL

When searching for child issues, note that the standard `parent = PROJ-123` syntax only works for native subtasks. For other parent-child relationships (like Stories under Epics), you may need to use the "Parent Link" custom field.

**About Parent Link:** This is a custom field from [Advanced Roadmaps](https://support.atlassian.com/jira-software-cloud/docs/search-for-advanced-roadmaps-custom-fields-in-jql/) (formerly Portfolio for Jira), which is bundled with Jira Cloud Premium and Jira Data Center 8.15+. It enables hierarchies beyond native subtasks.

```bash
# Find subtasks of an issue (native Jira)
jirahhh search "parent = PROJ-123" --env production

# Find issues linked via Parent Link (Advanced Roadmaps)
jirahhh search '"Parent Link" = PROJ-123' --env production
```

Use the `fields` command to discover the correct field names for your Jira instance.

## License

Apache-2.0
