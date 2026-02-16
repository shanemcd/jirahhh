"""
Core Jira client functionality.
"""

import logging
import os
import socket
import time
from pathlib import Path
from jira import JIRA
import yaml

logger = logging.getLogger(__name__)

# IPv4-only mode to avoid slow IPv6 connection attempts
# Python tries IPv6 first sequentially, unlike browsers which use Happy Eyeballs
_original_getaddrinfo = socket.getaddrinfo
_ipv4_only_enabled = False


def _ipv4_only_getaddrinfo(*args, **kwargs):
    """Filter getaddrinfo results to IPv4 only."""
    results = _original_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET]


def enable_ipv4_only():
    """Force all socket connections to use IPv4 only.

    Can be enabled via:
    - Environment variable: JIRAHHH_IPV4_ONLY=1
    - Config file: ipv4_only: true (at top level)
    """
    global _ipv4_only_enabled
    if not _ipv4_only_enabled:
        socket.getaddrinfo = _ipv4_only_getaddrinfo
        _ipv4_only_enabled = True
        logger.debug("Forcing IPv4-only connections")


def should_use_ipv4_only(config: dict = None) -> bool:
    """Check if IPv4-only mode should be enabled.

    Checks (in order):
    1. JIRAHHH_IPV4_ONLY environment variable (1/true/yes)
    2. ipv4_only in config file

    Returns:
        True if IPv4-only mode should be enabled
    """
    # Check environment variable first
    env_val = os.environ.get("JIRAHHH_IPV4_ONLY", "").lower()
    if env_val in ("1", "true", "yes"):
        return True
    if env_val in ("0", "false", "no"):
        return False

    # Check config file
    if config and config.get("ipv4_only"):
        return True

    return False


def get_jira_client(
    jira_url: str, api_token: str, proxy_url: str = None, config: dict = None,
    email: str = None,
) -> JIRA:
    """
    Create and return a Jira client instance.

    Args:
        jira_url: The Jira instance URL
        api_token: The Jira API token
        proxy_url: Optional HTTP/HTTPS proxy URL (e.g., 'http://proxy.example.com:3128')
                   Can also be set via HTTPS_PROXY or HTTP_PROXY environment variables
        config: Optional config dict for additional settings like ipv4_only
        email: Optional email for basic auth (required for Jira Cloud)

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

    # Check if IPv4-only mode should be enabled
    if should_use_ipv4_only(config):
        enable_ipv4_only()

    # Use basic auth (email + API token) for Jira Cloud, bearer token for Data Center
    if email:
        auth_kwargs = {"basic_auth": (email, api_token)}
        auth_desc = f"basic auth ({email})"
    else:
        auth_kwargs = {"token_auth": api_token}
        auth_desc = "bearer token"

    logger.debug("Creating JIRA client for %s (proxy: %s, auth: %s)", jira_url, proxy_url or "none", auth_desc)
    start = time.time()
    client = JIRA(options=jira_options, proxies=proxies, **auth_kwargs)
    elapsed = time.time() - start
    logger.debug("JIRA client created in %.2fs", elapsed)
    return client


def load_config(config_path: Path = None) -> dict:
    """
    Load configuration from config file.

    Checks locations in this order:
    1. Explicit config_path if provided
    2. ~/.config/jirahhh/config.yaml
    3. .jira-config.yaml in current directory

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Configuration dictionary
    """
    if config_path is not None:
        # Explicit path provided - use it
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    # Check standard locations
    locations = [
        Path.home() / ".config" / "jirahhh" / "config.yaml",
        Path(".jira-config.yaml"),
    ]

    for location in locations:
        if location.exists():
            with open(location, "r") as f:
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


def get_email(env: str, config: dict = None) -> str:
    """
    Get email for basic auth from environment variable or config file.

    Used for Jira Cloud which requires basic auth (email + API token)
    instead of bearer token auth used by Data Center.

    Args:
        env: Environment name (e.g., cloud, production)
        config: Optional configuration dictionary

    Returns:
        Email string or None if not configured
    """
    email = os.getenv("JIRA_EMAIL")
    if not email and config:
        email = config.get(env, {}).get("email")
    return email


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


def get_custom_fields(env: str, config: dict = None) -> dict:
    """
    Get custom field mappings from config file.

    Checks per-environment custom_fields first, then falls back to
    global custom_fields.

    Args:
        env: Environment name (e.g., cloud, prod)
        config: Optional configuration dictionary

    Returns:
        Dictionary of custom field mappings
    """
    if config:
        # Per-environment custom fields take priority
        env_fields = config.get(env, {}).get("custom_fields")
        if env_fields:
            return env_fields
        # Fall back to global custom fields
        if "custom_fields" in config:
            return config["custom_fields"]
    return {}


def get_security_level(level_name: str, env: str = None, config: dict = None) -> str:
    """
    Get security level ID from config file.

    Checks per-environment security_levels first, then falls back to
    global security_levels.

    Args:
        level_name: Security level name (e.g., 'default', 'confidential')
        env: Optional environment name (e.g., cloud, prod)
        config: Optional configuration dictionary

    Returns:
        Security level ID or None if not configured
    """
    if config:
        # Per-environment security levels take priority
        if env:
            env_level = config.get(env, {}).get("security_levels", {}).get(level_name)
            if env_level:
                return env_level
        # Fall back to global security levels
        if "security_levels" in config:
            return config["security_levels"].get(level_name)
    return None
