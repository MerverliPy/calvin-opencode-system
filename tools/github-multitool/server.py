#!/usr/bin/env python3
"""
Localhost-only HTTP server for GitHub Multitool.

Read-only MVP endpoints:
- GET /health
- GET /repo/status
- GET /prs
- GET /issues
- GET /branches
- GET /runs
- GET /pr/<number>
- GET /pr/<number>/readiness

Security model:
- Binds only to localhost / 127.0.0.1.
- Exposes read-only endpoints only.
- Calls the CLI backend through subprocess argument lists.
- Does not print tokens or credentials.
"""

from __future__ import annotations

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from config_validation import ConfigError, validate_config


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/github-multitool/github_multitool.py"
CONFIG_EXAMPLE = ROOT / "tools/github-multitool/config.example.json"
CONFIG_LOCAL = ROOT / "tools/github-multitool/config.json"


def load_config() -> dict:
    config = {
        "host": "127.0.0.1",
        "port": 8765,
        "default_repository": "MerverliPy/calvin-opencode-system",
    }

    for path in (CONFIG_LOCAL, CONFIG_EXAMPLE):
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                config.update(json.load(f))
            break

    return validate_config(config)


def run_cli(args: list[str]) -> tuple[int, dict | list | str]:
    result = subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    output = result.stdout.strip()
    if not output:
        output = result.stderr.strip()

    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError:
        payload = output

    return result.returncode, payload


def first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


class Handler(BaseHTTPRequestHandler):
    server_version = "GitHubMultitool/0.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.client_address[0]} - {fmt % args}", file=sys.stderr)

    def send_json(self, status: int, payload: dict | list | str) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reject(self, status: int, message: str) -> None:
        self.send_json(status, {"ok": False, "error": message})

    def do_POST(self) -> None:
        self.reject(405, "Write endpoints are disabled in the read-only MVP.")

    def do_PUT(self) -> None:
        self.reject(405, "Write endpoints are disabled in the read-only MVP.")

    def do_DELETE(self) -> None:
        self.reject(405, "Write endpoints are disabled in the read-only MVP.")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        repo = first(query, "repo")
        state = first(query, "state", "open")
        limit = first(query, "limit", "20")

        base_args: list[str] = []
        if repo:
            base_args.extend(["--repo", repo])

        if path == "/health":
            code, payload = run_cli([*base_args, "health"])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/repo/status":
            cli_args = [*base_args, "repo-status"]
            strict_private = first(query, "strict_private", "0")
            if str(strict_private).lower() in {"1", "true", "yes"}:
                cli_args.append("--strict-private")
            code, payload = run_cli(cli_args)
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/prs/dashboard":
            code, payload = run_cli([*base_args, "pr-dashboard", "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/prs":
            code, payload = run_cli([*base_args, "prs-list", "--state", state, "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        # PR readiness must be checked before the generic /pr/<number> handler
        if path.startswith("/pr/") and path.endswith("/readiness"):
            parts = path.split("/")
            if len(parts) < 4 or not parts[2].isdigit():
                self.reject(400, "PR number must be numeric.")
                return
            code, payload = run_cli([*base_args, "pr-readiness", parts[2]])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path.startswith("/pr/"):
            number = path.split("/", 2)[2]
            if not number.isdigit():
                self.reject(400, "PR number must be numeric.")
                return
            code, payload = run_cli([*base_args, "pr-view", number])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/issues":
            code, payload = run_cli([*base_args, "issues-list", "--state", state, "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/branches":
            code, payload = run_cli([*base_args, "branches-list", "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/runs":
            code, payload = run_cli([*base_args, "runs-list", "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path == "/runs/failed":
            code, payload = run_cli([*base_args, "runs-failed", "--limit", limit])
            self.send_json(200 if code == 0 else 500, payload)
            return

        if path.startswith("/run/") and path.endswith("/explain"):
            parts = path.split("/")
            if len(parts) < 4 or not parts[2].isdigit():
                self.reject(400, "Run ID must be numeric.")
                return
            run_id = parts[2]
            log_lines = first(query, "log_lines", "80")
            code, payload = run_cli([*base_args, "run-explain", run_id, "--log-lines", log_lines])
            self.send_json(200 if code == 0 else 500, payload)
            return

        self.reject(404, f"Unknown endpoint: {path}")


def main() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    host = str(config.get("host", "127.0.0.1"))
    port = int(config.get("port", 8765))

    if host not in {"127.0.0.1", "localhost"}:
        print("Refusing to bind non-localhost host:", host, file=sys.stderr)
        return 2

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GitHub Multitool listening on http://{host}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GitHub Multitool.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
