"""
Core Jira client functionality.
"""

import os
from pathlib import Path
from jira import JIRA
import yaml


def get_jira_client(jira_url: str, api_token: str, proxy_url: str = None) -> JIRA:
    """
    Create and return a Jira client instance.

    Args:
        jira_url: The Jira instance URL
        api_token: The Jira API token
        proxy_url: Optional HTTP/HTTPS proxy URL (e.g., 'http://proxy.example.com:3128')
                   Can also be set via HTTPS_PROXY or HTTP_PROXY environment variables

    Returns:
        JIRA client instance
    """
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    elif os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY"):
        env_proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        proxies = {"http": env_proxy, "https": env_proxy}

    jira_options = {"server": jira_url, "verify": True}

    return JIRA(options=jira_options, token_auth=api_token, proxies=proxies)


def load_config(config_path: Path = None) -> dict:
    """
    Load configuration from .jira-config.yaml.

    Args:
        config_path: Optional path to config file. Defaults to .jira-config.yaml in current directory.

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(".jira-config.yaml")

    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


def get_api_token(env: str, config: dict = None) -> str:
    """
    Get API token from environment variable or config file.

    Args:
        env: Environment name (e.g., staging, production)
        config: Optional configuration dictionary

    Returns:
        API token string

    Raises:
        ValueError: If token cannot be found
    """
    api_token = os.getenv("JIRA_API_TOKEN")
    if not api_token and config:
        api_token = config.get(env, {}).get("token")

    if not api_token:
        raise ValueError(
            f"JIRA_API_TOKEN environment variable or {env}.token in .jira-config.yaml must be set"
        )

    return api_token


def get_jira_url(env: str, config: dict = None) -> str:
    """
    Get Jira URL from config file or environment variable.

    Args:
        env: Environment name (e.g., staging, production)
        config: Optional configuration dictionary

    Returns:
        Jira URL string

    Raises:
        ValueError: If URL cannot be found
    """
    jira_url = os.getenv("JIRA_URL")
    if not jira_url and config:
        jira_url = config.get(env, {}).get("url")

    if not jira_url:
        raise ValueError(
            f"JIRA_URL environment variable or {env}.url in .jira-config.yaml must be set"
        )

    return jira_url


def get_proxy_url(env: str, config: dict = None) -> str:
    """
    Get proxy URL from config file (optional).

    Args:
        env: Environment name (e.g., staging, production)
        config: Optional configuration dictionary

    Returns:
        Proxy URL string or None if not configured
    """
    if config:
        return config.get(env, {}).get("proxy")
    return None


def get_custom_fields(config: dict = None) -> dict:
    """
    Get custom field mappings from config file.

    Args:
        config: Optional configuration dictionary

    Returns:
        Dictionary of custom field mappings
    """
    if config and "custom_fields" in config:
        return config["custom_fields"]
    return {}


def get_security_level(level_name: str, config: dict = None) -> str:
    """
    Get security level ID from config file.

    Args:
        level_name: Security level name (e.g., 'default', 'confidential')
        config: Optional configuration dictionary

    Returns:
        Security level ID or None if not configured
    """
    if config and "security_levels" in config:
        return config["security_levels"].get(level_name)
    return None
