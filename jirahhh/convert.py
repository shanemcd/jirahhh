"""
Functions for converting between formats.
"""

import sys
import os
import pypandoc
from typing import Optional


def convert_to_jira(text: str, file_path: Optional[str] = None) -> str:
    """
    Convert text to Jira format, detecting if conversion is needed based on file extension.

    Args:
        text: The text content (either inline or from file)
        file_path: Optional path to the file (used to detect extension)

    Returns:
        Text in Jira wiki markup format

    Raises:
        ValueError: If file extension is not supported
    """
    # If file_path is provided and exists, check extension
    if file_path and file_path != "-" and os.path.isfile(file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".md":
            # Convert from markdown to Jira
            return pypandoc.convert_file(file_path, "jira", format="gfm")
        elif ext == ".txt" or ext == "":
            # Assume it's already in Jira format
            return text
        else:
            raise ValueError(
                f"Unsupported file format: {ext}. Only .md and .txt are supported."
            )

    # If text looks like a file path that exists, check it
    if text and os.path.isfile(text):
        ext = os.path.splitext(text)[1].lower()

        if ext == ".md":
            # Convert from markdown to Jira
            return pypandoc.convert_file(text, "jira", format="gfm")
        elif ext == ".txt" or ext == "":
            # Read and return as-is
            with open(text, "r") as f:
                return f.read()
        else:
            raise ValueError(
                f"Unsupported file format: {ext}. Only .md and .txt are supported."
            )

    # Otherwise, treat as inline text in Jira format
    return text


def read_description(
    inline: Optional[str] = None, file_path: Optional[str] = None
) -> str:
    """
    Read description from various sources.

    Args:
        inline: Inline description text in Jira wiki markup, or a path to a file
        file_path: Path to file with Jira wiki markup (use '-' for stdin)

    Returns:
        Description string in Jira wiki markup

    Raises:
        ValueError: If no description source is provided or unsupported format
    """
    if file_path:
        if file_path == "-":
            return sys.stdin.read()
        else:
            # Use smart detection
            with open(file_path, "r") as f:
                content = f.read()
            return convert_to_jira(content, file_path)
    elif inline:
        # Check if inline is actually a file path
        return convert_to_jira(inline)
    else:
        raise ValueError("Must provide description via inline or file_path")
