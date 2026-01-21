"""
Functions for creating and updating Jira issues.
"""

import logging
from typing import Optional
from jira import JIRA

logger = logging.getLogger(__name__)


def create_issue(
    jira: JIRA,
    project_key: str,
    summary: str,
    issue_type: str,
    description: str,
    acceptance_criteria: Optional[str] = None,
    epic_name: Optional[str] = None,
    parent: Optional[str] = None,
    epic_link: Optional[str] = None,
    custom_field_ids: Optional[dict] = None,
    security_level_id: Optional[str] = None,
    additional_fields: Optional[dict] = None,
) -> dict:
    """
    Create a Jira issue with the given parameters.

    Args:
        jira: JIRA client instance
        project_key: Project key (e.g., PROJ)
        summary: Issue summary/title
        issue_type: Issue type (e.g., Epic, Story, Task, Spike)
        description: Issue description in Jira wiki markup
        acceptance_criteria: Optional acceptance criteria
        epic_name: Optional epic name (required for Epic issue type)
        parent: Optional parent issue key (e.g., PROJ-123)
        epic_link: Optional epic link (e.g., PROJ-456)
        custom_field_ids: Optional dict mapping field names to custom field IDs
                         Expected keys: acceptance_criteria, epic_name, parent_link, epic_link
        security_level_id: Optional security level ID to set on the issue
        additional_fields: Optional additional custom fields

    Returns:
        Dictionary with id, key, and self URL of created issue
    """
    # Default custom field IDs (can be overridden via custom_field_ids param or config)
    field_ids = custom_field_ids or {}

    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
        "description": description,
    }

    # Add security level if configured
    if security_level_id:
        fields["security"] = {"id": security_level_id}

    # Add custom fields using configured IDs
    if acceptance_criteria and "acceptance_criteria" in field_ids:
        fields[field_ids["acceptance_criteria"]] = acceptance_criteria
    if epic_name and "epic_name" in field_ids:
        fields[field_ids["epic_name"]] = epic_name
    if parent and "parent_link" in field_ids:
        fields[field_ids["parent_link"]] = parent
    if epic_link and "epic_link" in field_ids:
        fields[field_ids["epic_link"]] = epic_link

    # Add any additional fields (can override anything)
    if additional_fields:
        fields.update(additional_fields)

    # Create the issue
    new_issue = jira.create_issue(fields=fields)

    return {"id": new_issue.id, "key": new_issue.key, "self": new_issue.self}


def update_issue(
    jira: JIRA,
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    acceptance_criteria: Optional[str] = None,
    custom_field_ids: Optional[dict] = None,
    additional_fields: Optional[dict] = None,
) -> dict:
    """
    Update an existing Jira issue.

    Args:
        jira: JIRA client instance
        issue_key: Issue key to update (e.g., PROJ-123)
        summary: Optional new summary
        description: Optional new description in Jira wiki markup
        acceptance_criteria: Optional new acceptance criteria
        custom_field_ids: Optional dict mapping field names to custom field IDs
        additional_fields: Optional additional fields to update

    Returns:
        Dictionary with updated issue information
    """
    issue = jira.issue(issue_key)
    field_ids = custom_field_ids or {}
    fields = {}

    if summary is not None:
        fields["summary"] = summary
    if description is not None:
        fields["description"] = description
    if acceptance_criteria is not None and "acceptance_criteria" in field_ids:
        fields[field_ids["acceptance_criteria"]] = acceptance_criteria

    if additional_fields:
        fields.update(additional_fields)

    if fields:
        issue.update(fields=fields)

    return {"id": issue.id, "key": issue.key, "self": issue.self}


def view_issue(
    jira: JIRA,
    issue_key: str,
    fields: Optional[str] = None,
    custom_field_ids: Optional[dict] = None,
) -> dict:
    """
    View a Jira issue with all its details.

    Args:
        jira: JIRA client instance
        issue_key: Issue key to view (e.g., PROJ-123)
        fields: Optional comma-separated list of fields to retrieve (default: common fields)
        custom_field_ids: Optional dict mapping field names to custom field IDs for pretty-printing

    Returns:
        Dictionary with issue information
    """
    # Get the issue
    issue = jira.issue(issue_key, fields=fields if fields else "*all")
    field_ids = custom_field_ids or {}

    # Extract common fields
    result = {
        "key": issue.key,
        "id": issue.id,
        "self": issue.self,
        "summary": getattr(issue.fields, "summary", None),
        "status": issue.fields.status.name if hasattr(issue.fields, "status") else None,
        "type": (
            issue.fields.issuetype.name if hasattr(issue.fields, "issuetype") else None
        ),
        "description": getattr(issue.fields, "description", "") or "",
    }

    # Add assignee if present
    if hasattr(issue.fields, "assignee") and issue.fields.assignee:
        result["assignee"] = issue.fields.assignee.displayName

    # Add reporter if present
    if hasattr(issue.fields, "reporter") and issue.fields.reporter:
        result["reporter"] = issue.fields.reporter.displayName

    # Add priority if present
    if hasattr(issue.fields, "priority") and issue.fields.priority:
        result["priority"] = issue.fields.priority.name

    # Add security level if present
    if hasattr(issue.fields, "security") and issue.fields.security:
        result["security"] = {
            "id": issue.fields.security.id,
            "name": issue.fields.security.name,
        }

    # Add custom fields if field IDs are provided
    if "acceptance_criteria" in field_ids and hasattr(
        issue.fields, field_ids["acceptance_criteria"]
    ):
        acceptance_criteria = getattr(
            issue.fields, field_ids["acceptance_criteria"], None
        )
        if acceptance_criteria:
            result["acceptance_criteria"] = acceptance_criteria

    if "epic_name" in field_ids and hasattr(issue.fields, field_ids["epic_name"]):
        epic_name = getattr(issue.fields, field_ids["epic_name"], None)
        if epic_name:
            result["epic_name"] = epic_name

    if "parent_link" in field_ids and hasattr(issue.fields, field_ids["parent_link"]):
        parent = getattr(issue.fields, field_ids["parent_link"], None)
        if parent:
            result["parent"] = parent

    if "epic_link" in field_ids and hasattr(issue.fields, field_ids["epic_link"]):
        epic_link = getattr(issue.fields, field_ids["epic_link"], None)
        if epic_link:
            result["epic_link"] = epic_link

    # Add labels if present
    if hasattr(issue.fields, "labels") and issue.fields.labels:
        result["labels"] = issue.fields.labels

    # Add components if present
    if hasattr(issue.fields, "components") and issue.fields.components:
        result["components"] = [c.name for c in issue.fields.components]

    return result


def search_issues(
    jira: JIRA, jql: str, fields: Optional[str] = None, max_results: int = 50
) -> dict:
    """
    Search for Jira issues using JQL.

    Args:
        jira: JIRA client instance
        jql: JQL query string
        fields: Optional comma-separated list of fields to retrieve (default: common fields)
        max_results: Maximum number of results to return (default: 50)

    Returns:
        Dictionary with search results
    """
    # Execute JQL search
    issues = jira.search_issues(
        jql_str=jql,
        maxResults=max_results,
        fields=fields if fields else "summary,status,issuetype,assignee",
    )

    results = []
    for issue in issues:
        item = {
            "key": issue.key,
            "summary": issue.fields.summary,
        }

        # Add optional fields if present
        if hasattr(issue.fields, "status") and issue.fields.status:
            item["status"] = issue.fields.status.name
        if hasattr(issue.fields, "issuetype") and issue.fields.issuetype:
            item["type"] = issue.fields.issuetype.name
        if hasattr(issue.fields, "assignee") and issue.fields.assignee:
            item["assignee"] = issue.fields.assignee.displayName
        if hasattr(issue.fields, "priority") and issue.fields.priority:
            item["priority"] = issue.fields.priority.name

        results.append(item)

    return {"total": len(results), "issues": results}


def get_fields(
    jira: JIRA, project_key: Optional[str] = None, issue_type: Optional[str] = None
) -> dict:
    """
    Get available fields, optionally filtered by project and issue type.

    Args:
        jira: JIRA client instance
        project_key: Optional project key to filter fields
        issue_type: Optional issue type to filter fields

    Returns:
        Dictionary with field information
    """
    # Get all fields
    all_fields = jira.fields()

    # If project and issue type specified, get createmeta to see which fields are required/available
    available_fields = None
    if project_key:
        try:
            # Get create metadata for the project
            meta = jira.createmeta(
                projectKeys=project_key,
                issuetypeNames=issue_type,
                expand="projects.issuetypes.fields",
            )

            if meta and "projects" in meta and len(meta["projects"]) > 0:
                project = meta["projects"][0]
                if "issuetypes" in project and len(project["issuetypes"]) > 0:
                    issuetype = project["issuetypes"][0]
                    available_fields = issuetype.get("fields", {})
        except Exception:
            # If createmeta fails, just return all fields
            pass

    # Format field information
    fields = []
    for field in all_fields:
        field_info = {
            "id": field["id"],
            "name": field["name"],
            "custom": field.get("custom", False),
            "schema": field.get("schema", {}),
        }

        # Add required/allowed info if we have it
        if available_fields and field["id"] in available_fields:
            field_meta = available_fields[field["id"]]
            field_info["required"] = field_meta.get("required", False)
            field_info["operations"] = field_meta.get("operations", [])

        fields.append(field_info)

    return {"total": len(fields), "fields": fields}


def call_api(
    jira: JIRA, method: str, endpoint: str, data: Optional[dict] = None
) -> dict:
    """
    Make a generic API call to Jira.

    Args:
        jira: JIRA client instance
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path (e.g., /rest/api/2/issue/PROJ-123/comment)
        data: Optional JSON data for POST/PUT requests

    Returns:
        API response as dictionary
    """
    method = method.upper()

    # Ensure endpoint starts with /
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    url = jira._options["server"] + endpoint
    logger.debug("Making %s request to %s", method, url)

    # Make the API call using the JIRA client's session
    if method == "GET":
        response = jira._session.get(url)
    elif method == "POST":
        response = jira._session.post(url, json=data)
    elif method == "PUT":
        response = jira._session.put(url, json=data)
    elif method == "DELETE":
        response = jira._session.delete(url)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    logger.debug("Response status: %d", response.status_code)

    # Raise for HTTP errors
    response.raise_for_status()

    # Return JSON response if available, otherwise return status info
    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text}
