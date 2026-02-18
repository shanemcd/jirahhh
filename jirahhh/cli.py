#!/usr/bin/env python3
"""
Main CLI entrypoint for jirahhh with subcommands.
"""

import argparse
import json
import logging
import os
import signal
import sys

# Handle broken pipe gracefully (e.g., when piped to head/grep)
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def configure_logging(verbose: bool = False):
    """Configure logging.

    Args:
        verbose: If True, set level to DEBUG. Otherwise WARNING.
                 Can also be overridden via JIRAHHH_LOG_LEVEL env var.
    """
    env_level = os.environ.get("JIRAHHH_LOG_LEVEL")
    if env_level:
        level = getattr(logging, env_level.upper(), logging.WARNING)
    else:
        level = logging.DEBUG if verbose else logging.WARNING

    # Force unbuffered output so logs appear immediately when run as subprocess
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    handler.stream.reconfigure(line_buffering=True)
    logging.root.addHandler(handler)
    logging.root.setLevel(level)

from .client import (
    get_jira_client,
    load_config,
    get_api_token,
    get_jira_url,
    get_proxy_url,
    get_email,
    get_custom_fields,
    get_security_level,
)
from .convert import read_description, convert_to_jira
from .issues import (
    create_issue,
    update_issue,
    view_issue,
    search_issues,
    get_fields,
    add_comment,
    call_api,
)


def cmd_create(args):
    """Handle the 'create' subcommand."""
    # Get description from various sources
    try:
        description = read_description(
            inline=args.description, file_path=args.description_file
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Convert acceptance criteria if provided
    acceptance_criteria = None
    if args.acceptance_criteria:
        try:
            acceptance_criteria = convert_to_jira(args.acceptance_criteria)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Get custom field IDs and security level from config
    custom_field_ids = get_custom_fields(args.env, config)
    security_level_id = get_security_level("default", env=args.env, config=config)

    # Create the issue
    try:
        result = create_issue(
            jira=jira,
            project_key=args.project,
            summary=args.summary,
            issue_type=args.type,
            description=description,
            acceptance_criteria=acceptance_criteria,
            epic_name=args.epic_name,
            parent=args.parent,
            epic_link=args.epic_link,
            custom_field_ids=custom_field_ids,
            security_level_id=security_level_id,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error creating issue: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args):
    """Handle the 'update' subcommand."""
    # Get description from various sources if any were provided
    description = None
    if args.description or args.description_file:
        try:
            description = read_description(
                inline=args.description, file_path=args.description_file
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Convert acceptance criteria if provided
    acceptance_criteria = None
    if args.acceptance_criteria:
        try:
            acceptance_criteria = convert_to_jira(args.acceptance_criteria)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Get custom field IDs from config
    custom_field_ids = get_custom_fields(args.env, config)

    # Update the issue
    try:
        result = update_issue(
            jira=jira,
            issue_key=args.issue_key,
            summary=args.summary,
            description=description,
            acceptance_criteria=acceptance_criteria,
            custom_field_ids=custom_field_ids,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error updating issue: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_view(args):
    """Handle the 'view' subcommand."""
    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Get custom field IDs from config
    custom_field_ids = get_custom_fields(args.env, config)

    # View the issue
    try:
        result = view_issue(
            jira=jira,
            issue_key=args.issue_key,
            fields=args.fields,
            custom_field_ids=custom_field_ids,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error viewing issue: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args):
    """Handle the 'search' subcommand."""
    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Search for issues
    try:
        result = search_issues(
            jira=jira, jql=args.jql, fields=args.fields, max_results=args.max_results
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error searching issues: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_fields(args):
    """Handle the 'fields' subcommand."""
    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Get fields
    try:
        result = get_fields(jira=jira, project_key=args.project, issue_type=args.type)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error getting fields: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_comment(args):
    """Handle the 'comment' subcommand."""
    # Get comment body from various sources
    try:
        body = read_description(inline=args.body, file_path=args.body_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Add the comment
    try:
        result = add_comment(
            jira=jira,
            issue_key=args.issue_key,
            body=body,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error adding comment: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_api(args):
    """Handle the 'api' subcommand."""
    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)

    # Get API token
    try:
        api_token = get_api_token(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get Jira URL from config (can be overridden by --url)
    try:
        jira_url = args.url if args.url else get_jira_url(args.env, config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get proxy URL from config (can be overridden by --proxy)
    proxy_url = (
        args.proxy
        if hasattr(args, "proxy") and args.proxy
        else get_proxy_url(args.env, config)
    )

    # Get Jira client
    email = get_email(args.env, config)
    jira = get_jira_client(jira_url, api_token, proxy_url, config, email=email)

    # Parse JSON data if provided
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data: {e}", file=sys.stderr)
            sys.exit(1)

    # Handle --body-file: read file, convert if .md, inject into data["body"]
    if hasattr(args, "body_file") and args.body_file:
        try:
            body_content = read_description(file_path=args.body_file)
            if data is None:
                data = {}
            data["body"] = body_content
        except ValueError as e:
            print(f"Error reading body file: {e}", file=sys.stderr)
            sys.exit(1)

    # Make API call
    try:
        result = call_api(
            jira=jira, method=args.method, endpoint=args.endpoint, data=data
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error making API call: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="jirahhh",
        description="Manage Jira issues with proper wiki markup formatting",
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--config",
        help="Path to config file (default: ~/.config/jirahhh/config.yaml or .jira-config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.required = True

    # Create subcommand
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new Jira issue",
        epilog="Description can be provided via --description (inline text or file path) or --description-file",
    )
    create_parser.add_argument(
        "--project", required=True, help="Project key (e.g., PROJ)"
    )
    create_parser.add_argument("--summary", required=True, help="Issue summary/title")
    create_parser.add_argument(
        "--type", required=True, help="Issue type (e.g., Epic, Story, Task, Spike)"
    )
    create_parser.add_argument(
        "--description",
        help="Issue description: inline Jira wiki markup, or path to file (.md auto-converts, .txt as-is)",
    )
    create_parser.add_argument(
        "--description-file",
        help="File containing description in Jira wiki markup (use - for stdin)",
    )
    create_parser.add_argument(
        "--acceptance-criteria", help="Acceptance criteria (inline text or file path)"
    )
    create_parser.add_argument(
        "--epic-name", help="Epic name (required for Epic issue type)"
    )
    create_parser.add_argument("--parent", help="Parent issue key (e.g., PROJ-123)")
    create_parser.add_argument("--epic-link", help="Epic link (e.g., PROJ-456)")
    create_parser.add_argument("--url", help="Jira URL (overrides config file)")
    create_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    create_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    create_parser.set_defaults(func=cmd_create)

    # Update subcommand
    update_parser = subparsers.add_parser(
        "update",
        help="Update an existing Jira issue",
        epilog="Description can be provided via --description (inline text or file path) or --description-file",
    )
    update_parser.add_argument("issue_key", help="Issue key to update (e.g., PROJ-123)")
    update_parser.add_argument("--summary", help="New issue summary/title")
    update_parser.add_argument(
        "--description",
        help="New description: inline Jira wiki markup, or path to file (.md auto-converts, .txt as-is)",
    )
    update_parser.add_argument(
        "--description-file",
        help="File containing description in Jira wiki markup (use - for stdin)",
    )
    update_parser.add_argument(
        "--acceptance-criteria",
        help="New acceptance criteria (inline text or file path)",
    )
    update_parser.add_argument("--url", help="Jira URL (overrides config file)")
    update_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    update_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    update_parser.set_defaults(func=cmd_update)

    # View subcommand
    view_parser = subparsers.add_parser(
        "view", help="View a Jira issue with all details"
    )
    view_parser.add_argument("issue_key", help="Issue key to view (e.g., PROJ-123)")
    view_parser.add_argument(
        "--fields",
        help="Comma-separated list of fields to retrieve (default: all common fields)",
    )
    view_parser.add_argument("--url", help="Jira URL (overrides config file)")
    view_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    view_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    view_parser.set_defaults(func=cmd_view)

    # Search subcommand
    search_parser = subparsers.add_parser(
        "search", help="Search for Jira issues using JQL"
    )
    search_parser.add_argument(
        "jql", help='JQL query string (e.g., "project = PROJ AND status = Open")'
    )
    search_parser.add_argument(
        "--fields",
        help="Comma-separated list of fields to retrieve (default: summary,status,issuetype,assignee)",
    )
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of results to return (default: 50)",
    )
    search_parser.add_argument("--url", help="Jira URL (overrides config file)")
    search_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    search_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    search_parser.set_defaults(func=cmd_search)

    # Fields subcommand
    fields_parser = subparsers.add_parser(
        "fields", help="List available fields for a project/issue type"
    )
    fields_parser.add_argument(
        "--project", help="Project key to filter fields (e.g., PROJ)"
    )
    fields_parser.add_argument(
        "--type", help="Issue type to filter fields (e.g., Epic)"
    )
    fields_parser.add_argument("--url", help="Jira URL (overrides config file)")
    fields_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    fields_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    fields_parser.set_defaults(func=cmd_fields)

    # Comment subcommand
    comment_parser = subparsers.add_parser(
        "comment",
        help="Add a comment to a Jira issue",
        epilog="Comment body can be provided via --body (inline text or file path) or --body-file",
    )
    comment_parser.add_argument(
        "issue_key", help="Issue key to comment on (e.g., PROJ-123)"
    )
    comment_parser.add_argument(
        "--body",
        help="Comment body: inline Jira wiki markup, or path to file (.md auto-converts, .txt as-is)",
    )
    comment_parser.add_argument(
        "--body-file",
        help="File containing comment body in Jira wiki markup (use - for stdin)",
    )
    comment_parser.add_argument("--url", help="Jira URL (overrides config file)")
    comment_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    comment_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    comment_parser.set_defaults(func=cmd_comment)

    # API subcommand
    api_parser = subparsers.add_parser("api", help="Make a generic API call to Jira")
    api_parser.add_argument(
        "method", choices=["GET", "POST", "PUT", "DELETE"], help="HTTP method"
    )
    api_parser.add_argument(
        "endpoint", help="API endpoint path (e.g., /rest/api/2/issue/PROJ-123/comment)"
    )
    api_parser.add_argument("--data", help="JSON data for POST/PUT requests")
    api_parser.add_argument(
        "--body-file",
        help="File containing body content (.md auto-converts to Jira wiki markup). Injects into --data under 'body' key.",
    )
    api_parser.add_argument("--url", help="Jira URL (overrides config file)")
    api_parser.add_argument(
        "--proxy", help="HTTP/HTTPS proxy URL (overrides config file)"
    )
    api_parser.add_argument(
        "--env",
        default=None,
        help="Environment name from config file (overrides default_env in config)",
    )
    api_parser.set_defaults(func=cmd_api)

    args = parser.parse_args()
    configure_logging(verbose=args.verbose)

    # Use --env if provided, otherwise fall back to default_env in config
    if not args.env:
        config = load_config(args.config if hasattr(args, 'config') else None)
        args.env = config.get("default_env")
    if not args.env:
        parser.error("--env is required (or set default_env in your config file)")

    args.func(args)


if __name__ == "__main__":
    main()
