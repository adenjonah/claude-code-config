#!/usr/bin/env python3
"""
PostToolUse hook: after a deploy command, attempt to verify the deployment
reached a healthy state. Soft-warns Claude with the result so it can't
claim "deployed" without showing proof.

Deploy patterns recognised:
  - `vercel deploy` / `vercel --prod` / `vercel deploy --prod`
  - `fly deploy`
  - `eas submit` / `eas build`
  - `gh release create`
  - `npm publish`
  - `pnpm publish`

For Vercel deploys: parses the deployment URL from stdout and curls it,
expecting any 2xx/3xx within 30s. Other targets: prints "no auto-verify
configured for {tool}; Claude should manually verify before claiming done."

Never blocks the deploy itself — only annotates the result with a verify
check that Claude must reference before saying "deployed."

Fails open on any error.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Optional

DEPLOY_PATTERNS = [
    (re.compile(r"\bvercel\b.*\b(deploy|--prod\b|build)\b"), "vercel"),
    (re.compile(r"\bfly\s+deploy\b|\bflyctl\s+deploy\b"), "fly"),
    (re.compile(r"\beas\s+(submit|build)\b"), "eas"),
    (re.compile(r"\bgh\s+release\s+create\b"), "gh-release"),
    (re.compile(r"\b(npm|pnpm)\s+publish\b"), "npm-publish"),
]

VERCEL_URL_RE = re.compile(r"https://[a-z0-9\-]+(?:-[a-z0-9]+)*\.vercel\.app", re.IGNORECASE)
PROD_DOMAIN_RE = re.compile(
    r"(?:Production:|Deployed to:)\s*(https?://\S+)", re.IGNORECASE
)


def _read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _classify(command: str) -> Optional[str]:
    for pattern, tool in DEPLOY_PATTERNS:
        if pattern.search(command):
            return tool
    return None


def _extract_vercel_url(stdout: str, stderr: str) -> Optional[str]:
    blob = (stdout or "") + "\n" + (stderr or "")
    # Prefer "Production:" / "Deployed to:" lines for prod deploys
    m = PROD_DOMAIN_RE.search(blob)
    if m:
        return m.group(1).rstrip(".,)")
    # Otherwise take the last vercel.app URL emitted
    matches = VERCEL_URL_RE.findall(blob)
    if matches:
        return matches[-1]
    return None


def _curl(url: str, timeout: int = 30) -> tuple[int, str]:
    try:
        out = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )
        code = out.stdout.strip() or "?"
        return (out.returncode, code)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return (1, f"curl-failed: {e!s}")


def main() -> None:
    data = _read_input()
    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = (data.get("tool_input", {}).get("command") or "").strip()
    if not command:
        sys.exit(0)

    tool = _classify(command)
    if not tool:
        sys.exit(0)

    tool_response = data.get("tool_response") or {}
    if isinstance(tool_response, str):
        stdout, stderr, exit_code = tool_response, "", 0
    else:
        stdout = tool_response.get("stdout", "") or ""
        stderr = tool_response.get("stderr", "") or ""
        exit_code = tool_response.get("exit_code", 0)

    # If the deploy command itself failed, the hook has nothing to verify —
    # let Claude handle the failure.
    if exit_code not in (0, None):
        sys.exit(0)

    if tool == "vercel":
        url = _extract_vercel_url(stdout, stderr)
        if not url:
            print(
                "⚠ deploy-verifier: vercel deploy command succeeded but no URL parsed "
                "from output. Manually verify with `curl <deployment-url>` before "
                "claiming 'deployed'.",
                file=sys.stderr,
            )
            sys.exit(0)
        rc, code = _curl(url)
        if rc == 0 and code.startswith(("2", "3")):
            print(
                f"✓ deploy-verifier: {url} returned HTTP {code}. Deploy verified live.",
                file=sys.stderr,
            )
        else:
            print(
                f"⚠ deploy-verifier: {url} did NOT respond healthy (HTTP {code}, "
                f"curl exit {rc}). Do NOT claim 'deployed' until you've manually "
                f"checked the URL — could be cold-start delay, DNS, or an actual "
                f"deploy failure.",
                file=sys.stderr,
            )
        sys.exit(0)

    # Other deploy tools: no auto-verify implemented yet.
    print(
        f"⚠ deploy-verifier: no auto-verify configured for `{tool}`. Manually verify "
        f"the deploy reached its target (curl, fly status, eas build:view, etc.) "
        f"before claiming 'deployed'.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
