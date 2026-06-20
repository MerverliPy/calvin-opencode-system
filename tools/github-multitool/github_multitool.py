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
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

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





# ---------------------------------------------------------------------------
# Write tool safety gates (Feature 5: Safe PR Creator)
# ---------------------------------------------------------------------------


def _check_allow_write_tools(config: dict[str, Any]) -> None:
    """Raise ToolError if write tools are disabled in config."""
    if not config.get("allow_write_tools", False):
        raise ToolError(
            "Write tools are disabled. "
            "Set allow_write_tools=true in config to enable gated write commands."
        )


def _git_working_tree_clean() -> bool:
    """Return True if git working tree is clean (no uncommitted changes)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == ""


def _git_current_branch() -> str:
    """Return the current git branch name."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ToolError(
            "Failed to determine current branch: "
            + (result.stderr.strip() or "not in a git repository")
        )
    return result.stdout.strip()


def _branch_ahead_count(base: str, head: str) -> int:
    """Return number of commits *head* is ahead of *base*.

    Prefers origin/<base> when available, falls back to local <base>.
    """
    for base_ref in (f"origin/{base}", base):
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{base_ref}..{head}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            try:
                return int(result.stdout.strip())
            except ValueError:
                continue
    raise ToolError(
        f"Failed to count commits ahead: could not compare {base}..{head}"
    )


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


# ---------------------------------------------------------------------------
# PR Readiness Score helpers
# ---------------------------------------------------------------------------

HIGH_RISK_DIRS = [
    ".github/workflows/",
    "tools/github-multitool/",
    "scripts/",
    ".opencode/",
]

HIGH_RISK_FILES = {
    "package-lock.json",
    "pyproject.toml",
    "requirements.txt",
    "dockerfile",
    "docker-compose.yml",
}

HIGH_RISK_KEYWORDS = [
    "secret", "token", "credential", "auth",
    "deploy", "release", "workflow",
]

STALE_DAYS = 14



# ---------------------------------------------------------------------------
# Log redaction and failure classification helpers
# ---------------------------------------------------------------------------

SENSITIVE_LOG_PATTERNS = [
    "gh_token",
    "github_token",
    "token",
    "secret",
    "credential",
    "password",
    "cookie",
    "authorization",
    "bearer",
]


def _redact_log(log_text: str) -> str:
    """Redact sensitive-looking log lines before printing or storing."""
    lines = log_text.split("\n")
    redacted: list[str] = []
    for line in lines:
        lower = line.lower()
        if any(p in lower for p in SENSITIVE_LOG_PATTERNS):
            redacted.append("[REDACTED: line matched sensitive pattern]")
        else:
            redacted.append(line)
    return "\n".join(redacted)


def _classify_failure(log_text: str) -> dict[str, str]:
    """Lightweight pattern matching to classify a workflow failure from log text.

    Returns a dict with keys: class, recommended_command, next_step.
    """
    lower = log_text.lower()

    # Shell syntax errors (check first — most specific patterns)
    shell_patterns = [
        "syntax error", "unexpected token", "command not found",
        "bad substitution",
    ]
    if any(p in lower for p in shell_patterns):
        return {
            "class": "shell syntax",
            "recommended_command": "bash -n <script>",
            "next_step": "Run bash -n on the failing script to catch syntax errors locally.",
        }

    # Test failures
    test_patterns = [
        "assertionerror", " assertionerror", "pytest", "npm test",
        "test failed", "test failure",
    ]
    # also match FAILED in all-caps (common pytest output) but not the word "failed" alone
    has_failed_caps = any("FAILED" in part for part in log_text.split("\n") if "FAILED" in part)
    if any(p in lower for p in test_patterns) or has_failed_caps:
        return {
            "class": "test failure",
            "recommended_command": "tools/github-multitool/smoke-test.sh",
            "next_step": "Run the matching local verification command and inspect the first failing test.",
        }

    # Dependency install failures
    dep_patterns = [
        "npm err!", "pip install", "no matching distribution found",
        "could not resolve", "dependency",
    ]
    if any(p in lower for p in dep_patterns):
        return {
            "class": "dependency install",
            "recommended_command": "pip install -r requirements.txt  # or npm install",
            "next_step": "Check that dependency versions are available and compatible with the runner environment.",
        }

    # Permission / token failures
    perm_patterns = [
        "permission denied", "resource not accessible by integration",
        "bad credentials", "gh_token", "github_token", " 403 ", " 401 ",
    ]
    if any(p in lower for p in perm_patterns):
        return {
            "class": "permission/token",
            "recommended_command": "gh auth status",
            "next_step": "Verify GITHUB_TOKEN permissions and repository secrets configuration.",
        }

    # Workflow configuration errors
    wf_patterns = [
        "invalid workflow file", "the workflow is not valid",
        ".github/workflows", "mapping values are not allowed",
    ]
    if any(p in lower for p in wf_patterns):
        return {
            "class": "workflow configuration",
            "recommended_command": "yamllint .github/workflows/  # or python3 -c 'import yaml; yaml.safe_load(open(\"...\"))'",
            "next_step": "Validate the workflow YAML file syntax and structure.",
        }

    # Unknown
    return {
        "class": "unknown",
        "recommended_command": "tools/github-multitool/smoke-test.sh",
        "next_step": "Inspect failed job logs with run-explain.",
    }


def _fetch_failed_run_log(repo: str, run_id: int, max_lines: int = 200) -> str:
    """Fetch a limited log excerpt from a failed run's failed steps.

    Uses gh run view --log-failed and returns at most *max_lines*.
    Returns an empty string if the log is unavailable.
    """
    try:
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--repo", repo, "--log-failed"],
            text=True,
            capture_output=True,
            check=False,
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        return "(log fetch timed out)"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            return f"(log unavailable: {stderr})"
        return ""

    raw = result.stdout.strip()
    if not raw:
        return ""

    lines = raw.split("\n")
    if len(lines) > max_lines:
        excerpt = "\n".join(lines[:max_lines])
        excerpt += f"\n... (truncated, {len(lines) - max_lines} more lines)"
    else:
        excerpt = raw

    return _redact_log(excerpt)

def _is_high_risk_file(filepath: str) -> bool:
    """Return True if *filepath* matches high-risk directory, file, or keyword."""
    path_lower = filepath.lower()

    for d in HIGH_RISK_DIRS:
        if path_lower.startswith(d):
            return True

    filename = path_lower.split("/")[-1]
    if filename in HIGH_RISK_FILES:
        return True

    for kw in HIGH_RISK_KEYWORDS:
        if kw in path_lower:
            return True

    return False


def _fetch_pr_metadata(repo: str, number: int) -> dict[str, Any]:
    """Fetch PR metadata via gh pr view --json."""
    return run_gh_json([
        "pr", "view", str(number),
        "--repo", repo,
        "--json",
        "number,title,state,isDraft,author,headRefName,baseRefName,"
        "mergeStateStatus,reviewDecision,url,updatedAt,createdAt",
    ])


def _fetch_changed_files(repo: str, number: int) -> list[str]:
    """Fetch changed file paths for a PR via gh pr view --json files."""
    try:
        result = run_gh_json([
            "pr", "view", str(number),
            "--repo", repo,
            "--json", "files",
        ])
    except ToolError:
        return []

    files = result.get("files") if isinstance(result, dict) else result
    if not isinstance(files, list):
        return []
    return [f.get("path", "") for f in files if isinstance(f, dict)]


def _fetch_pr_checks(repo: str, number: int) -> list[dict[str, Any]]:
    """Fetch PR check statuses via gh pr checks --json."""
    try:
        result = run_gh_json([
            "pr", "checks", str(number),
            "--repo", repo,
            "--json", "name,status,conclusion",
        ])
    except ToolError:
        return []
    return result if isinstance(result, list) else []


def _score_pr_readiness(
    pr_data: dict[str, Any],
    files: list[str],
    checks_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute a numeric readiness score (0-100) and risk level."""

    score: int = 100
    blockers: list[str] = []
    warnings: list[str] = []
    reasons: list[dict[str, Any]] = []

    number = pr_data.get("number")

    # ── Merge state ───────────────────────────────────────────────
    mss = (pr_data.get("mergeStateStatus") or "").upper()
    if mss == "CLEAN":
        reasons.append({"signal": "merge_state_clean", "effect": 0,
                        "detail": "Merge state is clean"})
    elif mss == "DIRTY":
        score -= 30
        blockers.append("Merge conflicts detected")
        reasons.append({"signal": "merge_state_dirty", "effect": -30,
                        "detail": "Merge state is dirty (conflicts)"})
    elif mss == "BLOCKED":
        score -= 30
        blockers.append("Merge is blocked")
        reasons.append({"signal": "merge_state_blocked", "effect": -30,
                        "detail": "Merge is blocked"})
    elif mss in ("UNKNOWN", ""):
        score -= 10
        warnings.append("Merge state is unknown")
        reasons.append({"signal": "merge_state_unknown", "effect": -10,
                        "detail": "Merge state is unknown"})
    else:
        score -= 10
        warnings.append(f"Unexpected merge state: {mss}")
        reasons.append({"signal": "merge_state_unexpected", "effect": -10,
                        "detail": f"Unexpected merge state: {mss}"})

    # ── Draft ─────────────────────────────────────────────────────
    if pr_data.get("isDraft"):
        score -= 30
        blockers.append("PR is a draft")
        reasons.append({"signal": "draft", "effect": -30,
                        "detail": "Draft PRs are not ready for review"})
    else:
        reasons.append({"signal": "not_draft", "effect": 0,
                        "detail": "PR is not a draft"})

    # ── Stale ─────────────────────────────────────────────────────
    updated_at = pr_data.get("updatedAt", "")
    if updated_at:
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - updated_dt).days
            if age_days > STALE_DAYS:
                score -= 10
                warnings.append(f"PR is stale ({age_days} days since last update)")
                reasons.append({"signal": "stale_pr", "effect": -10,
                                "detail": f"PR has not been updated in {age_days} days"})
        except (ValueError, TypeError):
            pass

    # ── Review decision ───────────────────────────────────────────
    rd = (pr_data.get("reviewDecision") or "").upper()
    if rd == "APPROVED":
        reasons.append({"signal": "review_approved", "effect": 0,
                        "detail": "Review has been approved"})
    elif rd == "CHANGES_REQUESTED":
        score -= 15
        blockers.append("Changes requested in review")
        reasons.append({"signal": "review_changes_requested", "effect": -15,
                        "detail": "Review requested changes"})
    elif rd in ("REVIEW_REQUIRED", ""):
        score -= 5
        warnings.append("Review decision unavailable")
        reasons.append({"signal": "review_unavailable", "effect": -5,
                        "detail": "Review decision is not available"})
    else:
        score -= 5
        warnings.append(f"Unknown review decision: {rd}")
        reasons.append({"signal": "review_unknown", "effect": -5,
                        "detail": f"Unknown review decision: {rd}"})

    # ── Base branch ───────────────────────────────────────────────
    base_ref = pr_data.get("baseRefName", "")
    if base_ref == "main":
        reasons.append({"signal": "base_is_main", "effect": 0,
                        "detail": "Base branch is main"})
    else:
        score -= 5
        warnings.append(f"Base branch is '{base_ref}', not main")
        reasons.append({"signal": "base_not_main", "effect": -5,
                        "detail": f"Base branch is '{base_ref}', not main"})

    # ── Checks ────────────────────────────────────────────────────
    if checks_data:
        failed = [c for c in checks_data if c.get("conclusion") == "FAILURE"]
        pending = [c for c in checks_data
                   if c.get("status") in ("IN_PROGRESS", "QUEUED")]

        if failed:
            score -= max(20, len(failed) * 5)  # significant penalty
            blockers.append(f"{len(failed)} check(s) failed")
            reasons.append({"signal": "checks_failed",
                            "effect": -max(20, len(failed) * 5),
                            "detail": f"{len(failed)} checks failed",
                            "failed_checks": [c.get("name") for c in failed]})
        elif pending:
            score -= 5
            warnings.append(f"{len(pending)} check(s) still running")
            reasons.append({"signal": "checks_pending", "effect": -5,
                            "detail": f"{len(pending)} checks pending"})
        else:
            reasons.append({"signal": "checks_passed", "effect": 0,
                            "detail": "All checks passed or neutral"})
    else:
        score -= 5
        warnings.append("Check status unavailable")
        reasons.append({"signal": "checks_unavailable", "effect": -5,
                        "detail": "Check status could not be fetched"})

    # ── High-risk files ───────────────────────────────────────────
    if files:
        risky = [f for f in files if _is_high_risk_file(f)]
        if risky:
            # cap combined file-risk deduction at 30
            risk_deduction = min(30, len(risky) * 10)
            score -= risk_deduction
            if risk_deduction >= 20:
                blockers.append(f"{len(risky)} high-risk file(s) changed")
            else:
                warnings.append(f"{len(risky)} high-risk file(s) changed")
            reasons.append({
                "signal": "high_risk_files",
                "effect": -risk_deduction,
                "detail": f"{len(risky)} high-risk files changed",
                "files": risky,
            })
        else:
            reasons.append({"signal": "no_risky_files", "effect": 0,
                            "detail": "No high-risk files changed"})
    else:
        warnings.append("Changed files unavailable")
        reasons.append({"signal": "files_unavailable", "effect": 0,
                        "detail": "Changed files could not be fetched"})

    # ── Clamp & risk level ────────────────────────────────────────
    score = max(0, min(100, score))

    if score >= 85:
        risk = "low"
    elif score >= 60:
        risk = "medium"
    elif score >= 30:
        risk = "high"
    else:
        risk = "blocked"

    # ── Recommended next action ───────────────────────────────────
    if blockers:
        recommended = "Address blockers before proceeding."
    elif warnings:
        recommended = "Run local verification and request review."
    elif score >= 85:
        recommended = "PR appears ready to merge."
    else:
        recommended = "Review and address warnings before proceeding."

    return {
        "number": number,
        "score": score,
        "risk": risk,
        "blockers": blockers,
        "warnings": warnings,
        "scoring_reasons": reasons,
        "changed_files": files,
        "recommended_next_action": recommended,
    }




def _parse_diff_stats(diff_text: str) -> dict[str, int]:
    """Parse gh pr diff output to count files, additions, deletions."""
    files = 0
    additions = 0
    deletions = 0
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            files += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {"files": files, "additions": additions, "deletions": deletions}


def _fetch_pr_diff(repo: str, number: int) -> str:
    """Fetch a compact diff for a PR via gh pr diff (read-only)."""
    result = subprocess.run(
        ["gh", "pr", "diff", str(number), "--repo", repo, "--color", "never"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _sanitize_for_appendix(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive fields from metadata for appendix inclusion."""
    safe = dict(data)
    sensitive_patterns = {"token", "password", "secret", "credential", "cookie", "key", "auth"}
    for key in list(safe.keys()):
        key_lower = key.lower()
        for pattern in sensitive_patterns:
            if pattern in key_lower:
                safe[key] = "***REDACTED***"
    return safe


def _build_review_pack_md(
    pr_data: dict[str, Any],
    readiness: dict[str, Any],
    files: list[str],
    diff_text: str,
    number: int,
    padded: str,
    repo: str,
) -> str:
    """Build the Markdown review pack content."""
    lines: list[str] = []

    author_data = pr_data.get("author") or {}
    author = author_data.get("login", "unknown") if isinstance(author_data, dict) else str(author_data)

    diff_stats = _parse_diff_stats(diff_text) if diff_text else {"files": 0, "additions": 0, "deletions": 0}

    # ── Header ──
    lines.append(f"# PR {number} Review Pack")
    lines.append("")

    # ── Summary ──
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Title**: {pr_data.get('title', 'N/A')}")
    lines.append(f"- **Author**: {author}")
    lines.append(f"- **Branch**: `{pr_data.get('headRefName', 'N/A')}` → `{pr_data.get('baseRefName', 'N/A')}`")
    lines.append(f"- **Base Branch**: `{pr_data.get('baseRefName', 'N/A')}`")
    lines.append(f"- **URL**: {pr_data.get('url', 'N/A')}")
    lines.append(f"- **State**: {pr_data.get('state', 'N/A')}")
    lines.append(f"- **Draft**: {pr_data.get('isDraft', False)}")
    lines.append(f"- **Updated**: {pr_data.get('updatedAt', 'N/A')}")
    lines.append("")

    # ── Readiness ──
    lines.append("## Readiness")
    lines.append("")
    lines.append(f"- **Score**: {readiness['score']}/100")
    lines.append(f"- **Risk**: {readiness['risk']}")
    blockers = readiness.get("blockers", [])
    if blockers:
        lines.append(f"- **Blockers**: {len(blockers)}")
        for b in blockers:
            lines.append(f"  - {b}")
    else:
        lines.append("- **Blockers**: none")
    warnings = readiness.get("warnings", [])
    if warnings:
        lines.append(f"- **Warnings**: {len(warnings)}")
        for w in warnings:
            lines.append(f"  - {w}")
    else:
        lines.append("- **Warnings**: none")
    lines.append(f"- **Recommended Next Action**: {readiness.get('recommended_next_action', 'N/A')}")
    lines.append("")

    # ── Changed Files ──
    lines.append("## Changed Files")
    lines.append("")
    if files:
        for fp in files:
            flag = "  ⚠️ HIGH RISK" if _is_high_risk_file(fp) else ""
            lines.append(f"- `{fp}`{flag}")
    else:
        lines.append("_No changed files available._")
    lines.append("")

    # ── Diff Summary ──
    lines.append("## Diff Summary")
    lines.append("")
    if diff_text:
        lines.append(f"- **Files changed**: {diff_stats['files']}")
        lines.append(f"- **Additions**: {diff_stats['additions']}")
        lines.append(f"- **Deletions**: {diff_stats['deletions']}")
        lines.append("")
        lines.append("```diff")
        diff_lines = diff_text.split("\n")
        max_diff = 150
        if len(diff_lines) <= max_diff:
            lines.append(diff_text)
        else:
            lines.append("\n".join(diff_lines[:max_diff]))
            lines.append(f"")
            lines.append(f"... ({len(diff_lines) - max_diff} more lines truncated)")
        lines.append("```")
    else:
        lines.append("_Diff not available._")
    lines.append("")

    # ── Risk Assessment ──
    lines.append("## Risk Assessment")
    lines.append("")
    high_risk_files = [fp for fp in files if _is_high_risk_file(fp)]
    if readiness["risk"] == "low":
        lines.append("This PR appears low-risk. No significant blockers or high-risk file changes detected.")
    elif readiness["risk"] == "medium":
        lines.append("This PR has moderate risk. Review the warnings below and verify changed files before merging.")
    elif readiness["risk"] == "high":
        lines.append("**⚠️ This PR has high risk.** Review carefully before merging.")
    else:
        lines.append("**🚫 This PR is blocked.** Address blockers before any review or merge attempt.")
    lines.append("")

    if high_risk_files:
        lines.append("### High-Risk Files Changed")
        lines.append("")
        lines.append("The following files match high-risk patterns and deserve extra scrutiny:")
        lines.append("")
        for f in high_risk_files:
            lines.append(f"- `{f}`")
        lines.append("")

    # Specific risk notes based on signals
    scoring = readiness.get("scoring_reasons", [])
    negative_signals = [s for s in scoring if s.get("effect", 0) < 0]
    if negative_signals:
        lines.append("### Risk Signals")
        lines.append("")
        for s in negative_signals:
            lines.append(f"- **{s.get('signal', 'unknown')}** (effect: {s.get('effect', 0)}): {s.get('detail', '')}")
        lines.append("")

    lines.append("")

    # ── Verification Commands ──
    lines.append("## Verification Commands")
    lines.append("")
    lines.append("Run the following commands to verify the repository state:")
    lines.append("")
    lines.append("```bash")
    lines.append("tools/github-multitool/smoke-test.sh")
    lines.append("./scripts/verify-opencode-os.sh")
    lines.append("git status --short --branch")
    lines.append("```")
    lines.append("")

    # ── Rollback Notes ──
    lines.append("## Rollback Notes")
    lines.append("")
    head_branch = pr_data.get("headRefName", "feature-branch")
    base_branch = pr_data.get("baseRefName", "main")
    lines.append("To abandon this branch locally before merge:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"git checkout {base_branch}")
    lines.append(f"git branch -D {head_branch}")
    lines.append("```")
    lines.append("")
    lines.append("If the PR has already been merged and needs reversion:")
    lines.append("")
    lines.append("```bash")
    lines.append("git revert <merge-commit-hash>")
    lines.append("```")
    lines.append("")

    # ── ChatGPT / opencode Review Prompt ──
    lines.append("## ChatGPT / opencode Review Prompt")
    lines.append("")
    lines.append("Copy and paste the following prompt into ChatGPT, opencode, or another review tool:")
    lines.append("")
    lines.append("```")
    lines.append(f"Please review PR #{number} ({pr_data.get('title', 'N/A')}) in the {repo} repository.")
    lines.append("")
    lines.append("Review checklist:")
    lines.append("1. **Correctness** — Does the logic accomplish the intended goal without bugs or unintended side effects?")
    lines.append("2. **Safety** — Are there security risks, token leaks, injection vectors, or unsafe command patterns?")
    lines.append("3. **Regression risk** — Could this change break existing features, workflows, or smoke tests?")
    lines.append("4. **Missing verification** — What tests, assertions, or manual checks should be added?")
    lines.append("5. **Suggested improvements** — What could be simpler, cleaner, or more maintainable?")
    lines.append("")
    lines.append("The diff summary and changed files are included in this review pack.")
    lines.append("Focus on the risk assessment signals first.")
    lines.append("```")
    lines.append("")

    # ── Raw Metadata Appendix ──
    lines.append("## Raw Metadata Appendix")
    lines.append("")
    lines.append("```json")
    appendix = {
        "pr_metadata": _sanitize_for_appendix(pr_data),
        "readiness": {
            "score": readiness["score"],
            "risk": readiness["risk"],
            "blockers": readiness.get("blockers", []),
            "warnings": readiness.get("warnings", []),
            "recommended_next_action": readiness.get("recommended_next_action"),
        },
        "changed_files": files,
        "diff_stats": diff_stats,
        "high_risk_files": high_risk_files,
    }
    lines.append(json.dumps(appendix, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    return "\n".join(lines) + "\n"


# ── CLI command: pr-review-pack ─────────────────────────────────────────────


def cmd_pr_review_pack(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Generate a local Markdown review package for a PR."""
    require_gh()
    repo = resolve_repo(config, args.repo)
    number: int = args.number

    # Fetch PR metadata (required)
    try:
        pr_data = _fetch_pr_metadata(repo, number)
    except ToolError as exc:
        print_json({"ok": False, "error": f"Failed to fetch PR metadata: {exc}"})
        return 2

    # Fetch changed files (best-effort)
    try:
        files = _fetch_changed_files(repo, number)
    except ToolError as exc:
        files = []

    # Fetch checks (best-effort)
    try:
        checks = _fetch_pr_checks(repo, number)
    except ToolError as exc:
        checks = []

    # Compute readiness score
    readiness = _score_pr_readiness(pr_data, files, checks)

    # Fetch compact diff (read-only, best-effort)
    diff_text = _fetch_pr_diff(repo, number)

    # Generate output path
    output_dir = repo_root() / "dist" / "github-review-packs"
    output_dir.mkdir(parents=True, exist_ok=True)
    padded = f"{number:03d}"
    output_path = output_dir / f"pr-{padded}-review-pack.md"

    # Build and write Markdown review pack
    md_content = _build_review_pack_md(pr_data, readiness, files, diff_text, number, padded, repo)
    output_path.write_text(md_content, encoding="utf-8")

    # Print JSON result
    result = {
        "ok": True,
        "pr_number": number,
        "output_path": str(output_path),
        "repository": repo,
        "readiness_score": readiness["score"],
        "risk": readiness["risk"],
        "changed_file_count": len(files),
    }
    print_json(result)
    return 0

# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


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


def cmd_pr_readiness(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Compute a PR readiness score from metadata, checks, and changed files."""
    require_gh()
    repo = resolve_repo(config, args.repo)
    number: int = args.number
    fetch_errors: list[str] = []

    # Fetch PR metadata (required)
    try:
        pr_data = _fetch_pr_metadata(repo, number)
    except ToolError as exc:
        print_json({"ok": False, "error": f"Failed to fetch PR metadata: {exc}"})
        return 2

    # Fetch changed files (best-effort)
    try:
        files = _fetch_changed_files(repo, number)
    except ToolError as exc:
        files = []
        fetch_errors.append(f"Changed files unavailable: {exc}")

    # Fetch checks (best-effort)
    try:
        checks = _fetch_pr_checks(repo, number)
    except ToolError as exc:
        checks = []
        fetch_errors.append(f"Checks unavailable: {exc}")

    result = _score_pr_readiness(pr_data, files, checks)
    if fetch_errors:
        result["fetch_errors"] = fetch_errors
    result["ok"] = True
    print_json(result)
    return 0


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




# ---------------------------------------------------------------------------
# Feature 4: GitHub Actions Failure Explainer
# ---------------------------------------------------------------------------

def cmd_runs_failed(config: dict[str, Any], args: argparse.Namespace) -> int:
    """List failed GitHub Actions workflow runs with failure classification."""
    require_gh()
    repo = resolve_repo(config, args.repo)

    try:
        runs = run_gh_json([
            "run", "list",
            "--repo", repo,
            "--status", "failure",
            "--limit", str(args.limit),
            "--json",
            "databaseId,workflowName,status,conclusion,createdAt,updatedAt,url,headBranch,event",
        ])
    except ToolError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2

    if not isinstance(runs, list):
        runs = []

    failed_runs: list[dict[str, Any]] = []
    for run in runs:
        run_id = run.get("databaseId")
        if not run_id:
            continue

        # Best-effort classification: fetch a small log excerpt
        log_excerpt = _fetch_failed_run_log(repo, run_id, max_lines=150)
        classification = _classify_failure(log_excerpt)

        entry: dict[str, Any] = {
            "database_id": run_id,
            "workflow_name": run.get("workflowName", ""),
            "status": run.get("status", ""),
            "conclusion": run.get("conclusion", ""),
            "branch": run.get("headBranch", ""),
            "event": run.get("event", ""),
            "url": run.get("url", ""),
            "created_at": run.get("createdAt", ""),
            "updated_at": run.get("updatedAt", ""),
            "probable_failure_class": classification["class"],
            "recommended_local_command": classification["recommended_command"],
            "next_debugging_step": classification["next_step"],
        }
        failed_runs.append(entry)

    output = {
        "ok": True,
        "repository": repo,
        "failed_runs": failed_runs,
        "total_count": len(failed_runs),
    }
    print_json(output)
    return 0


def cmd_run_explain(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Explain a failed GitHub Actions workflow run with log excerpts."""
    require_gh()
    repo = resolve_repo(config, args.repo)
    run_id: int = args.run_id
    log_lines: int = getattr(args, "log_lines", 80)

    # Fetch run metadata
    try:
        run_data = run_gh_json([
            "run", "view", str(run_id),
            "--repo", repo,
            "--json",
            "databaseId,workflowName,status,conclusion,createdAt,updatedAt,url,headBranch,event",
        ])
    except ToolError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2

    if not isinstance(run_data, dict):
        run_data = {}

    # Fetch log excerpt
    log_excerpt = _fetch_failed_run_log(repo, run_id, max_lines=log_lines)

    # Count actual lines returned (before truncation marker)
    actual_lines = log_excerpt.count("\n") + 1 if log_excerpt else 0

    # Classify
    classification = _classify_failure(log_excerpt)

    output = {
        "ok": True,
        "repository": repo,
        "run_id": run_id,
        "workflow_name": run_data.get("workflowName", ""),
        "status": run_data.get("status", ""),
        "conclusion": run_data.get("conclusion", ""),
        "branch": run_data.get("headBranch", ""),
        "event": run_data.get("event", ""),
        "url": run_data.get("url", ""),
        "created_at": run_data.get("createdAt", ""),
        "updated_at": run_data.get("updatedAt", ""),
        "probable_failure_class": classification["class"],
        "recommended_local_command": classification["recommended_command"],
        "next_debugging_step": classification["next_step"],
        "log_excerpt": log_excerpt,
        "log_lines_returned": actual_lines,
    }
    print_json(output)
    return 0


# ---------------------------------------------------------------------------
# Feature 5: Safe PR Creator
# ---------------------------------------------------------------------------


def cmd_pr_create(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Create a pull request with heavy safety gates.

    All of the following must pass before a PR is created:

    1. allow_write_tools is true in config.
    2. --confirm is present.
    3. Current branch is not main or master.
    4. Working tree is clean.
    5. Branch has commits ahead of base.
    6. PR title is non-empty.
    7. Body file exists.
    8. Repository is allowlisted.
    9. Repository visibility guard does not block.
    """
    # Gate 1: --confirm flag present
    if not getattr(args, "confirm", False):
        print_json({"ok": False, "error": "Refusing to create PR without --confirm."})
        return 1

    # Gate 2: Write tools enabled
    if not config.get("allow_write_tools", False):
        print_json({
            "ok": False,
            "error": (
                "Write tools are disabled. "
                "Set allow_write_tools=true in config to enable gated write commands."
            ),
        })
        return 1

    # Gate 3: PR title is non-empty
    title = (getattr(args, "title", "") or "").strip()
    if not title:
        print_json({"ok": False, "error": "PR title must be non-empty."})
        return 1

    # Gate 4: Body file exists
    body_file = getattr(args, "body_file", "")
    if not body_file:
        print_json({"ok": False, "error": "Refusing to create PR without --body-file."})
        return 1

    body_path = Path(body_file)
    if not body_path.exists():
        print_json({
            "ok": False,
            "error": f"Refusing to create PR: body file does not exist: {body_file}",
        })
        return 1

    # Gate 5: Repository is allowlisted (resolve_repo enforces allowlist)
    repo = resolve_repo(config, args.repo)

    # Determine base branch
    base = getattr(args, "base", "main") or "main"

    # Determine head branch: resolve "current" to actual branch name
    head_raw = getattr(args, "head", "")
    if not head_raw:
        print_json({"ok": False, "error": "Refusing to create PR without --head."})
        return 1

    if head_raw == "current":
        head = _git_current_branch()
    else:
        head = head_raw

    # Get current branch for safety checks
    current_branch = _git_current_branch()

    # Gate 6: Current branch is not main or master
    if current_branch in ("main", "master"):
        print_json({"ok": False, "error": "Refusing to create PR from main branch."})
        return 1

    # Gate 7: Working tree is clean
    if not _git_working_tree_clean():
        print_json({
            "ok": False,
            "error": (
                "Refusing to create PR: working tree is not clean. "
                "Commit or stash changes first."
            ),
        })
        return 1

    # Gate 8: Branch has commits ahead of base
    ahead = _branch_ahead_count(base, head)
    if ahead == 0:
        print_json({
            "ok": False,
            "error": (
                f"Refusing to create PR: head branch '{head}' "
                f"has 0 commits ahead of base '{base}'."
            ),
        })
        return 1

    # Gate 9: Repository visibility guard
    # (handled implicitly by resolve_repo and config validation)

    # ── Safe PR preview (stderr) ──────────────────────────────────
    preview_lines = [
        "--- PR Preview ---",
        f"Repository:     {repo}",
        f"Title:          {title}",
        f"Base:           {base}",
        f"Head:           {head}",
        f"Body file:      {body_path}",
        f"Commits ahead:  {ahead}",
        f"Current branch: {current_branch}",
        "--- Creating PR ---",
    ]
    print("\n".join(preview_lines), file=sys.stderr)

    # ── Execute gh pr create ──────────────────────────────────────
    result = subprocess.run(
        [
            "gh", "pr", "create",
            "--repo", repo,
            "--title", title,
            "--body-file", str(body_path),
            "--base", base,
            "--head", head,
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        print_json({
            "ok": False,
            "error": result.stderr.strip() or "gh pr create failed",
        })
        return 2

    url = result.stdout.strip()

    output = {
        "ok": True,
        "repository": repo,
        "title": title,
        "base": base,
        "head": head,
        "url": url,
        "write_action": "pr_create",
    }
    print_json(output)
    return 0


# ---------------------------------------------------------------------------
# Feature 6: PR Body Generator
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Sanitize branch name for use as a filename.

    Replaces unsafe characters with hyphens, collapses multiple hyphens,
    and strips leading/trailing hyphens and dots.
    """
    safe = re.sub(r'[^a-zA-Z0-9._-]', '-', name)
    safe = re.sub(r'-{2,}', '-', safe)
    safe = safe.strip('.-')
    return safe if safe else "unnamed-branch"


def _resolve_base_branch() -> str:
    """Find the base branch to compare against.

    Tries origin/main first, falls back to main.
    Returns the branch name used.
    """
    for candidate in ("origin/main", "main"):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return candidate
    raise ToolError(
        "Cannot find origin/main or main as base branch. "
        "Create one or fetch from remote."
    )


def _collect_commit_subjects(base: str) -> list[str]:
    """Collect commit subject lines from base..HEAD."""
    result = subprocess.run(
        ["git", "log", "--oneline", f"{base}..HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line for line in result.stdout.strip().split("\n") if line]


def _collect_changed_files(base: str) -> list[str]:
    """Collect changed file paths with status markers from base..HEAD."""
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{base}..HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line for line in result.stdout.strip().split("\n") if line]


def _collect_diff_stat(base: str) -> str:
    """Collect compact diff stat from base..HEAD."""
    result = subprocess.run(
        ["git", "diff", "--stat", f"{base}..HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _extract_path_from_status(status_line: str) -> str:
    """Extract the file path from a git diff --name-status line.

    Lines have the format: M\tpath/to/file or A\tpath/to/file
    For renames, the format is: R100\told\tnew
    Returns the last tab-separated component (the destination path).
    """
    parts = status_line.split("\t")
    return parts[-1] if parts else status_line


def _detect_verification() -> tuple[bool, str]:
    """Detect whether smoke test / verifier were recently run.

    Returns (verification_detected, message).
    Does not invent successful verification — only reports what can be proven.
    """
    smoke_files = [
        "/tmp/github-multitool-cli-health.json",
        "/tmp/github-multitool-cli-pr-readiness.json",
    ]
    found = 0
    for fp in smoke_files:
        p = Path(fp)
        if p.exists():
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                age = datetime.now(timezone.utc) - mtime
                if age < timedelta(hours=24):
                    found += 1
            except OSError:
                pass

    if found > 0:
        return (
            True,
            f"Smoke test evidence detected ({found} output file(s) modified within 24 hours).",
        )
    return (
        False,
        "Not automatically verified by this generator. Run the commands below before opening the PR.",
    )


def _generate_summary(
    commit_subjects: list[str],
    changed_files: list[str],
    branch: str,
) -> str:
    """Generate a brief summary of the branch purpose."""
    num_commits = len(commit_subjects)
    num_files = len(changed_files)

    if num_commits == 0:
        return (
            f"Branch `{branch}` has no commits ahead of base. "
            f"{num_files} file(s) differ from base."
        )

    # Use first commit subject (without short hash) as a lead
    first = commit_subjects[0]
    first_subject = first.split(" ", 1)[1] if " " in first else first

    # Identify affected directories
    affected_dirs: set[str] = set()
    for cf in changed_files:
        path = _extract_path_from_status(cf)
        top = path.split("/")[0] if "/" in path else "(root)"
        affected_dirs.add(top)

    dirs_str = ", ".join(sorted(affected_dirs)[:5])
    if len(affected_dirs) > 5:
        dirs_str += f", ... (+{len(affected_dirs) - 5} more)"

    lines = [
        f"Branch `{branch}` contains {num_commits} commit(s) affecting "
        f"{num_files} file(s) across {dirs_str}.",
        "",
    ]
    if num_commits == 1:
        lines.append(f"**Change**: {first_subject}")
    else:
        lines.append(f"**First commit**: {first_subject}")
        lines.append(f"_({num_commits - 1} additional commit(s) — see Changes section below)_")

    return "\n".join(lines)


def _build_pr_body_md(
    branch: str,
    base: str,
    commit_subjects: list[str],
    changed_files: list[str],
    diff_stat: str,
    verification_detected: bool,
    verification_message: str,
) -> str:
    """Build the PR body Markdown content."""
    lines: list[str] = []

    # ── Header ──
    lines.append(f"# PR Body: {branch}")
    lines.append("")

    # ── Summary ──
    lines.append("## Summary")
    lines.append("")
    lines.append(_generate_summary(commit_subjects, changed_files, branch))
    lines.append("")

    # ── Changes ──
    lines.append("## Changes")
    lines.append("")

    if commit_subjects:
        lines.append("### Commits")
        lines.append("")
        for cs in commit_subjects:
            lines.append(f"- {cs}")
        lines.append("")

    if changed_files:
        lines.append("### Changed Files")
        lines.append("")
        for cf in changed_files:
            lines.append(f"- `{cf}`")
        lines.append("")

    if diff_stat:
        lines.append("### Diff Stat")
        lines.append("")
        lines.append("```")
        lines.append(diff_stat)
        lines.append("```")
        lines.append("")

    # ── Verification ──
    lines.append("## Verification")
    lines.append("")
    lines.append("Run the following commands before opening the PR:")
    lines.append("")
    lines.append("```bash")
    lines.append("tools/github-multitool/smoke-test.sh")
    lines.append("./scripts/verify-opencode-os.sh")
    lines.append("git status --short --branch")
    lines.append("```")
    lines.append("")
    lines.append(verification_message)
    lines.append("")

    # ── Risk ──
    lines.append("## Risk")
    lines.append("")

    # Identify high-risk files from changed files
    high_risk: list[str] = []
    for cf in changed_files:
        path = _extract_path_from_status(cf)
        if _is_high_risk_file(path):
            high_risk.append(path)

    if high_risk:
        lines.append(f"**⚠️ {len(high_risk)} high-risk file(s) detected.**")
        lines.append("")
        lines.append("The following files match high-risk patterns:")
        lines.append("")
        for f in high_risk:
            lines.append(f"- `{f}`")
        lines.append("")
        lines.append("Pay extra attention to:")
        lines.append("- Configuration and workflow impacts")
        lines.append("- Security-sensitive paths")
        lines.append("- Infrastructure changes")
    else:
        lines.append("No high-risk files detected in this change set.")
        lines.append("")
        lines.append("Standard review practices apply.")

    lines.append("")

    # ── Rollback ──
    lines.append("## Rollback")
    lines.append("")
    base_clean = base.replace("origin/", "")
    lines.append("To abandon this branch before merge:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"git checkout {base_clean}")
    lines.append(f"git branch -D {branch}")
    lines.append("```")
    lines.append("")
    lines.append("If already merged and needs reversion:")
    lines.append("")
    lines.append("```bash")
    lines.append("git revert <merge-commit-hash>")
    lines.append("```")
    lines.append("")

    # ── Reviewer Notes ──
    lines.append("## Reviewer Notes")
    lines.append("")
    lines.append(f"- **Branch**: `{branch}` → `{base}`")
    lines.append(f"- **Commits**: {len(commit_subjects)}")
    lines.append(f"- **Files changed**: {len(changed_files)}")
    lines.append("")
    if high_risk:
        lines.append("### Files Requiring Extra Scrutiny")
        lines.append("")
        for f in high_risk:
            lines.append(f"- `{f}`")
        lines.append("")
    lines.append("Review checklist:")
    lines.append("")
    lines.append("1. **Correctness** — Does the logic accomplish the intended goal?")
    lines.append("2. **Safety** — Are there security risks, token leaks, or unsafe patterns?")
    lines.append("3. **Regression** — Could this break existing features or smoke tests?")
    lines.append("4. **Completeness** — Are tests, documentation, and verification adequate?")
    lines.append("")

    return "\n".join(lines) + "\n"


def cmd_pr_body(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Generate a local PR body Markdown file from commits, changed files,
    and available verification context.

    Output is written to dist/github-pr-bodies/.
    """
    root = repo_root()

    # Determine current branch
    current_branch = _git_current_branch()

    # Refuse if on main or master
    if current_branch in ("main", "master"):
        print_json({
            "ok": False,
            "error": (
                f"Refusing to generate PR body on '{current_branch}' branch. "
                "Switch to a feature branch first."
            ),
        })
        return 1

    # Determine base branch (origin/main fallback main)
    base = _resolve_base_branch()

    # Collect data from git
    commit_subjects = _collect_commit_subjects(base)
    changed_files = _collect_changed_files(base)
    diff_stat = _collect_diff_stat(base)

    # Detect verification status
    verification_detected, verification_message = _detect_verification()

    # Build markdown content
    md_content = _build_pr_body_md(
        branch=current_branch,
        base=base,
        commit_subjects=commit_subjects,
        changed_files=changed_files,
        diff_stat=diff_stat,
        verification_detected=verification_detected,
        verification_message=verification_message,
    )

    # Create output directory
    output_dir = root / "dist" / "github-pr-bodies"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename from branch name
    safe_branch = _sanitize_filename(current_branch)
    output_path = output_dir / f"pr-body-{safe_branch}.md"

    # Write file
    output_path.write_text(md_content, encoding="utf-8")

    # Print JSON result
    result = {
        "ok": True,
        "output_path": str(output_path),
        "branch": current_branch,
        "base": base,
        "commit_count": len(commit_subjects),
        "changed_file_count": len(changed_files),
        "verification_detected": verification_detected,
    }
    print_json(result)
    return 0
# ---------------------------------------------------------------------------
# Feature 7: Branch Cleanup Advisor helpers and command
# ---------------------------------------------------------------------------

def _git_list_local_branches() -> list[str]:
    """List local branch names via git branch --format."""
    result = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ToolError(
            "Failed to list local branches: "
            + (result.stderr.strip() or "unknown error")
        )
    return [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]


def _git_list_remote_branches() -> list[str]:
    """List remote tracking branches (origin/* only, excluding HEAD)."""
    result = subprocess.run(
        ["git", "branch", "-r", "--format=%(refname:short)"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    all_remote = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
    return [
        b for b in all_remote
        if b.startswith("origin/") and "->" not in b and not b.endswith("/HEAD")
    ]


def _git_get_merged_branches(target: str, *, remote: bool = False) -> set[str]:
    """Return branches merged into *target*.

    When *remote* is True, uses ``git branch -r --merged``.
    Returns an empty set on failure.
    """
    if remote:
        cmd = ["git", "branch", "-r", "--merged", target, "--format=%(refname:short)"]
    else:
        cmd = ["git", "branch", "--merged", target, "--format=%(refname:short)"]
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return set()
    branches = {b.strip() for b in result.stdout.strip().split("\n") if b.strip()}
    if remote:
        branches = {
            b for b in branches
            if b.startswith("origin/") and "->" not in b and not b.endswith("/HEAD")
        }
    return branches


def _get_default_branch(repo: str) -> str:
    """Determine the default branch for *repo*.

    Tries ``gh repo view --json defaultBranchRef`` first,
    then falls back to ``git symbolic-ref refs/remotes/origin/HEAD``,
    and finally returns ``"main"``.
    """
    try:
        data = run_gh_json(["repo", "view", repo, "--json", "defaultBranchRef"])
        ref = data.get("defaultBranchRef") or {}
        if isinstance(ref, dict):
            name = ref.get("name")
            if name:
                return name
    except ToolError:
        pass

    # Local fallback
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ref = result.stdout.strip()
        return ref.split("/")[-1] if "/" in ref else ref

    return "main"


def _get_open_pr_branches(repo: str) -> set[str]:
    """Return the set of headRefName values for open PRs in *repo*."""
    try:
        prs = run_gh_json([
            "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", "200",
            "--json", "headRefName",
        ])
    except ToolError:
        return set()
    if not isinstance(prs, list):
        return set()
    return {pr.get("headRefName", "") for pr in prs if isinstance(pr, dict)}


def cmd_branches_cleanup_plan(config: dict[str, Any], args: argparse.Namespace) -> int:
    """Branch Cleanup Advisor: identify local and remote branches safe to delete.

    This command is strictly read-only.  It never deletes anything.
    """
    require_gh()
    repo = resolve_repo(config, args.repo)

    # ── Gather data ─────────────────────────────────────────────────
    default_branch = _get_default_branch(repo)
    current_branch = _git_current_branch()

    try:
        local_branches = _git_list_local_branches()
    except ToolError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2

    remote_branches = _git_list_remote_branches()

    # Determine which branches are merged into default (local + remote)
    merged_local = _git_get_merged_branches(default_branch, remote=False)
    if not merged_local:
        # Fallback: try origin/<default> as merge target
        merged_local = _git_get_merged_branches(f"origin/{default_branch}", remote=False)

    merged_remote = _git_get_merged_branches(f"origin/{default_branch}", remote=True)

    # Open PR branches
    open_pr_branches = _get_open_pr_branches(repo)

    # ── Classify ────────────────────────────────────────────────────
    protected = {"main", "master", default_branch}

    do_not_delete: list[dict[str, str]] = []
    safe_local: list[dict[str, str]] = []
    safe_remote: list[dict[str, str]] = []
    manual_review: list[dict[str, str]] = []

    # --- Local branches ---
    for branch in local_branches:
        if branch in protected:
            do_not_delete.append({
                "branch": branch,
                "reason": "Default branch.",
            })
            continue

        if branch == current_branch:
            do_not_delete.append({
                "branch": branch,
                "reason": "Current checked-out branch.",
            })
            continue

        if branch in open_pr_branches:
            do_not_delete.append({
                "branch": branch,
                "reason": "Has an open pull request.",
            })
            continue

        if branch in merged_local:
            safe_local.append({
                "branch": branch,
                "reason": f"Merged into {default_branch} and has no open PR.",
                "suggested_command": f"git branch -d {branch}",
            })
        else:
            manual_review.append({
                "branch": branch,
                "reason": f"Not merged into {default_branch} and has no open PR.",
            })

    # --- Remote branches (origin/*) ---
    merged_remote_raw: set[str] = {b.replace("origin/", "", 1) for b in merged_remote}

    for remote_branch in remote_branches:
        raw_name = remote_branch.replace("origin/", "", 1)

        if raw_name in protected:
            do_not_delete.append({
                "branch": remote_branch,
                "reason": "Default branch (remote tracking).",
            })
            continue

        if raw_name == current_branch:
            do_not_delete.append({
                "branch": remote_branch,
                "reason": "Remote tracking for current checked-out branch.",
            })
            continue

        if raw_name in open_pr_branches:
            do_not_delete.append({
                "branch": remote_branch,
                "reason": "Has an open pull request.",
            })
            continue

        if raw_name in merged_remote_raw:
            safe_remote.append({
                "branch": remote_branch,
                "reason": f"Remote branch appears merged into {default_branch} and has no open PR.",
                "suggested_command": f"git push origin --delete {raw_name}",
            })
        elif merged_remote:
            # We have a merged list, and this branch is not in it
            manual_review.append({
                "branch": remote_branch,
                "reason": f"Remote branch not merged into {default_branch}.",
            })
        else:
            manual_review.append({
                "branch": remote_branch,
                "reason": "Remote merge state could not be determined (origin tracking may be stale).",
            })

    # ── Build output ────────────────────────────────────────────────
    output: dict[str, Any] = {
        "ok": True,
        "repository": repo,
        "default_branch": default_branch,
        "current_branch": current_branch,
        "safe_to_delete_local": safe_local,
        "safe_to_delete_remote": safe_remote,
        "needs_manual_review": manual_review,
        "do_not_delete": do_not_delete,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    print_json(output)
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

    p = sub.add_parser("pr-readiness", help="Compute a PR readiness score.")
    p.add_argument("number", type=int)
    p.set_defaults(func=cmd_pr_readiness)

    p = sub.add_parser("pr-review-pack", help="Generate a local Markdown review pack for a PR.")
    p.add_argument("number", type=int)
    p.set_defaults(func=cmd_pr_review_pack)

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

    p = sub.add_parser("runs-failed", help="List failed GitHub Actions workflow runs with failure classification.")
    p.add_argument("--limit", type=int, default=10, help="Max failed runs to return (default: 10).")
    p.set_defaults(func=cmd_runs_failed)

    p = sub.add_parser("run-explain", help="Explain a failed GitHub Actions workflow run.")
    p.add_argument("run_id", type=int, help="The run database ID to explain.")
    p.add_argument("--log-lines", type=int, default=80, help="Max log lines to return (default: 80).")
    p.set_defaults(func=cmd_run_explain)


    p = sub.add_parser("pr-create", help="Create a pull request (gated write tool).")
    p.add_argument("--title", required=True, help="PR title.")
    p.add_argument("--body-file", required=True, help="Path to PR body Markdown file.")
    p.add_argument("--base", default="main", help="Base branch for the PR (default: main).")
    p.add_argument(
        "--head",
        default="current",
        help='Head branch for the PR. Use "current" to resolve the current branch (default: current).',
    )
    p.add_argument(
        "--confirm",
        action="store_true",
        help="Required confirmation flag. The command refuses without this flag.",
    )
    p.set_defaults(func=cmd_pr_create)

    p = sub.add_parser("pr-body", help="Generate a local PR body Markdown file from commits and changed files.")

    p.set_defaults(func=cmd_pr_body)
    p = sub.add_parser("branches-cleanup-plan", help="Branch Cleanup Advisor: identify branches safe to delete (advisory only).")
    p.set_defaults(func=cmd_branches_cleanup_plan)




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
