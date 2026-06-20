#!/usr/bin/env python3
"""
GitHub Localhost Multitool CLI backend.

Read-only MVP wrapper around GitHub CLI `gh`.

Security model:
- Uses subprocess argument lists, not shell=True.
- Uses an allowlist of repositories from config.
- Does not print tokens.
- Does not perform write operations in this MVP.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from datetime import datetime, timezone, timedelta

from config_validation import ConfigError, repo_visibility_warnings, validate_config


DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8765,
    "default_repository": "MerverliPy/calvin-opencode-system",
    "allowed_repositories": ["MerverliPy/calvin-opencode-system"],
    "backend": "gh",
    "allow_write_tools": False,
    "warn_public_repositories": True,
    "strict_private": False,
}


class ToolError(RuntimeError):
    """Controlled user-facing tool error."""


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return Path.cwd()


def load_config(root: Path) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)

    for candidate in (
        root / "tools/github-multitool/config.json",
        root / "tools/github-multitool/config.example.json",
    ):
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            config.update(loaded)
            break

    return validate_config(config)


def print_json(payload: dict[str, Any] | list[Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def gh_available() -> bool:
    return shutil.which("gh") is not None


def require_gh() -> None:
    if not gh_available():
        raise ToolError("GitHub CLI `gh` is not installed or not on PATH.")


def resolve_repo(config: dict[str, Any], requested_repo: str | None) -> str:
    repo = requested_repo or config.get("default_repository")
    allowed = set(config.get("allowed_repositories", []))

    if not repo:
        raise ToolError("No repository provided and no default_repository configured.")

    if allowed and repo not in allowed:
        raise ToolError(f"Repository is not allowlisted: {repo}")

    return repo


def run_gh_json(args: list[str]) -> Any:
    require_gh()

    result = subprocess.run(
        ["gh", *args],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown gh error"
        raise ToolError(stderr)

    stdout = result.stdout.strip()
    if not stdout:
        return {}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Expected JSON from gh, got non-JSON output: {exc}") from exc


def cmd_health(config: dict[str, Any], args: argparse.Namespace) -> int:
    payload = {
        "ok": True,
        "backend": config.get("backend", "gh"),
        "gh_available": gh_available(),
        "host": config.get("host"),
        "localhost_only": config.get("host") in ("127.0.0.1", "localhost"),
        "allow_write_tools": bool(config.get("allow_write_tools", False)),
        "warn_public_repositories": bool(config.get("warn_public_repositories", True)),
        "strict_private": bool(config.get("strict_private", False)),
        "default_repository": config.get("default_repository"),
        "allowed_repositories": config.get("allowed_repositories", []),
    }
    print_json(payload)
    return 0


def cmd_repo_status(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "repo",
        "view",
        repo,
        "--json",
        "nameWithOwner,description,visibility,isPrivate,defaultBranchRef,url",
    ])

    warnings = repo_visibility_warnings(
        payload,
        config,
        strict_private=bool(getattr(args, "strict_private", False)),
    )
    if warnings:
        payload["safety_warnings"] = warnings

    print_json(payload)
    return 0


def cmd_prs_list(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        args.state,
        "--limit",
        str(args.limit),
        "--json",
        "number,title,state,isDraft,author,headRefName,baseRefName,updatedAt,url",
    ])
    print_json(payload)
    return 0


def cmd_pr_view(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "pr",
        "view",
        str(args.number),
        "--repo",
        repo,
        "--json",
        "number,title,state,isDraft,author,headRefName,baseRefName,mergeStateStatus,reviewDecision,url",
    ])
    print_json(payload)
    return 0



def cmd_pr_dashboard(config: dict[str, Any], args: argparse.Namespace) -> int:
    """PR Intelligence Dashboard: summarize open PRs with risk and action data."""
    repo = resolve_repo(config, args.repo)
    raw_prs = run_gh_json([
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--limit",
        str(args.limit),
        "--json",
        "number,title,state,isDraft,author,headRefName,baseRefName,updatedAt,url,mergeStateStatus,reviewDecision,createdAt",
    ])

    if not isinstance(raw_prs, list):
        raw_prs = []

    normalized = []
    for pr in raw_prs:
        entry = _normalize_pr(pr)
        risk_levels, recommended_action = _classify_pr_risk(entry)
        entry["risk_levels"] = risk_levels
        entry["recommended_action"] = recommended_action
        normalized.append(entry)

    summary = _build_dashboard_summary(normalized)

    output = {
        "ok": True,
        "repository": repo,
        "total_count": len(normalized),
        "summary": summary,
        "prs": normalized,
    }
    print_json(output)
    return 0


def _normalize_pr(pr: dict[str, Any]) -> dict[str, Any]:
    """Normalize gh PR output into a stable internal schema."""
    author_info = pr.get("author") or {}
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "is_draft": bool(pr.get("isDraft")),
        "author": author_info.get("login") if isinstance(author_info, dict) else str(author_info),
        "head_branch": pr.get("headRefName"),
        "base_branch": pr.get("baseRefName"),
        "updated_at": pr.get("updatedAt"),
        "created_at": pr.get("createdAt"),
        "url": pr.get("url"),
        "merge_state": pr.get("mergeStateStatus"),
        "review_decision": pr.get("reviewDecision"),
    }


def _classify_pr_risk(pr: dict[str, Any]) -> tuple[list[str], str]:
    """Classify a PR into risk levels and recommend a next action."""
    risk_levels: list[str] = []
    actions: list[str] = []

    # Draft PRs are low readiness
    if pr.get("is_draft"):
        risk_levels.append("draft")
        actions.append("Complete draft before requesting review")

    # Review decision analysis
    review = pr.get("review_decision", "") or ""
    if review == "":
        risk_levels.append("needs_review")
        actions.append("Request or await review")
    elif review == "CHANGES_REQUESTED":
        risk_levels.append("changes_requested")
        actions.append("Address requested changes")
    elif review == "REVIEW_REQUIRED":
        risk_levels.append("needs_review")
        actions.append("Await review completion")

    # Merge state analysis
    merge = pr.get("merge_state", "") or ""
    if merge == "UNKNOWN" or merge == "":
        risk_levels.append("unknown_merge")
        actions.append("Check CI status and merge conflicts")
    elif merge == "DIRTY":
        risk_levels.append("merge_conflict")
        actions.append("Resolve merge conflicts")
    elif merge == "BLOCKED":
        risk_levels.append("blocked")
        actions.append("Unblock merge requirements")

    # Staleness check (not updated in > 7 days)
    updated = pr.get("updated_at", "") or ""
    if updated:
        try:
            updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (now - updated_dt) > timedelta(days=7):
                risk_levels.append("stale")
                actions.append("Follow up or consider closing stale PR")
        except (ValueError, TypeError):
            pass

    # If no risks identified, the PR appears ready
    if not risk_levels:
        risk_levels.append("ready")
        actions.append("Ready to merge")

    recommended_action = "; ".join(actions) if actions else "Review manually"
    return risk_levels, recommended_action


def _build_dashboard_summary(prs: list[dict[str, Any]]) -> dict[str, int]:
    """Build aggregate counts for the dashboard."""
    summary: dict[str, int] = {
        "total": len(prs),
        "draft": 0,
        "needs_review": 0,
        "changes_requested": 0,
        "stale": 0,
        "merge_conflict": 0,
        "blocked": 0,
        "unknown_merge": 0,
        "ready": 0,
    }
    for pr in prs:
        for level in pr.get("risk_levels", []):
            if level in summary:
                summary[level] += 1
    return summary

def cmd_issues_list(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        args.state,
        "--limit",
        str(args.limit),
        "--json",
        "number,title,state,author,labels,updatedAt,url",
    ])
    print_json(payload)
    return 0


def cmd_branches_list(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "api",
        f"repos/{repo}/branches?per_page={args.limit}",
    ])
    simplified = [
        {
            "name": item.get("name"),
            "protected": item.get("protected"),
            "sha": (item.get("commit") or {}).get("sha"),
        }
        for item in payload
    ]
    print_json(simplified)
    return 0


def cmd_runs_list(config: dict[str, Any], args: argparse.Namespace) -> int:
    repo = resolve_repo(config, args.repo)
    payload = run_gh_json([
        "run",
        "list",
        "--repo",
        repo,
        "--limit",
        str(args.limit),
        "--json",
        "databaseId,workflowName,status,conclusion,createdAt,updatedAt,url,headBranch,event",
    ])
    print_json(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="github_multitool.py",
        description="Localhost-safe GitHub multitool CLI backend.",
    )
    parser.add_argument("--repo", help="Repository in owner/name form.")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("health", help="Show local tool health.")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("repo-status", help="Show repository metadata.")
    p.add_argument(
        "--strict-private",
        action="store_true",
        help="Fail if the repository is public.",
    )
    p.set_defaults(func=cmd_repo_status)

    p = sub.add_parser("prs-list", help="List pull requests.")
    p.add_argument("--state", choices=["open", "closed", "all"], default="open")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_prs_list)

    p = sub.add_parser("pr-view", help="View pull request metadata.")
    p.add_argument("number", type=int)
    p.set_defaults(func=cmd_pr_view)

    p = sub.add_parser("pr-dashboard", help="PR intelligence dashboard with risk analysis.")
    p.add_argument("--limit", type=int, default=50, help="Max PRs to analyze (default: 50).")
    p.set_defaults(func=cmd_pr_dashboard)

    p = sub.add_parser("issues-list", help="List issues.")
    p.add_argument("--state", choices=["open", "closed", "all"], default="open")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_issues_list)

    p = sub.add_parser("branches-list", help="List branches.")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_branches_list)

    p = sub.add_parser("runs-list", help="List GitHub Actions workflow runs.")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_runs_list)

    return parser


def main() -> int:
    root = repo_root()
    config = load_config(root)
    parser = build_parser()
    args = parser.parse_args()

    try:
        return args.func(config, args)
    except (ToolError, ConfigError) as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
