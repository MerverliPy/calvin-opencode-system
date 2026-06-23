#!/usr/bin/env python3
"""
Config validation helpers for GitHub Localhost Multitool.
"""

from __future__ import annotations

import re
from typing import Any


REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOCALHOST_VALUES = {"127.0.0.1", "localhost"}


class ConfigError(ValueError):
    """Controlled config validation error."""


def validate_repo_name(repo: str, field_name: str) -> None:
    if not isinstance(repo, str) or not REPO_RE.match(repo):
        raise ConfigError(f"{field_name} must be in owner/name form: {repo!r}")


def require_bool(config: dict[str, Any], key: str, default: bool) -> None:
    value = config.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be true or false.")
    config[key] = value


def require_string_list(config: dict[str, Any], key: str) -> None:
    value = config.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{key} must be a list of strings.")
    config[key] = value


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    validated = dict(config)

    host = validated.get("host", "127.0.0.1")
    if host not in LOCALHOST_VALUES:
        raise ConfigError(f"Refusing non-localhost host: {host!r}")
    validated["host"] = host

    try:
        port = int(validated.get("port", 8765))
    except (TypeError, ValueError) as exc:
        raise ConfigError("port must be an integer.") from exc

    if not (1 <= port <= 65535):
        raise ConfigError("port must be between 1 and 65535.")
    validated["port"] = port

    backend = validated.get("backend", "gh")
    if backend != "gh":
        raise ConfigError("Only backend 'gh' is supported in the MVP.")
    validated["backend"] = backend

    default_repo = validated.get("default_repository")
    if default_repo:
        validate_repo_name(default_repo, "default_repository")

    require_string_list(validated, "allowed_repositories")
    for repo in validated["allowed_repositories"]:
        validate_repo_name(repo, "allowed_repositories item")

    if default_repo and validated["allowed_repositories"]:
        if default_repo not in validated["allowed_repositories"]:
            raise ConfigError("default_repository must be included in allowed_repositories.")

    require_bool(validated, "allow_write_tools", False)
    require_bool(validated, "warn_public_repositories", True)
    require_bool(validated, "strict_private", False)
    require_bool(validated, "block_writes_on_public_repo", True)
    require_bool(validated, "allow_public_repo_write_override", False)

    require_string_list(validated, "require_confirmation_for")
    require_string_list(validated, "forbidden_actions")

    return validated


def repo_visibility_warnings(
    repo_status: dict[str, Any],
    config: dict[str, Any],
    strict_private: bool = False,
) -> list[str]:
    warnings: list[str] = []

    is_private = repo_status.get("isPrivate")
    visibility = repo_status.get("visibility")

    public = is_private is False or visibility == "PUBLIC"

    if public:
        message = (
            "Repository is public. If this repo stores private workflow, agent, "
            "configuration, or audit material, change the GitHub repository visibility to private."
        )

        if config.get("warn_public_repositories", True):
            warnings.append(message)

        if strict_private or config.get("strict_private", False):
            raise ConfigError("Strict private mode failed: repository is public.")

    return warnings
