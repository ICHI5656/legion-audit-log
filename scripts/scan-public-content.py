#!/usr/bin/env python3
"""Fail-closed scanner for content intended for the public audit repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 1_000_000


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str


def _secret_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    token_prefix = "(?:" + "|".join(
        (
            "gh" + "[pousr]",
            "github_pat",
            "glpat",
            "xox" + "[aboprs]",
            "sk" + "-(?:live|test|proj)",
        )
    ) + ")"
    jwt_prefix = "ey" + "J"
    private_header = "-" * 5 + "BEGIN " + "(?:RSA |EC |OPENSSH )?PRIVATE KEY" + "-" * 5
    connection_schemes = "(?:" + "|".join(
        ("postgres(?:ql)?", "mysql", "mongodb(?:\\+srv)?", "redis")
    ) + ")"

    return (
        ("private-key", re.compile(private_header, re.IGNORECASE)),
        (
            "token-prefix",
            re.compile(rf"\b{token_prefix}_[A-Za-z0-9_-]{{12,}}\b", re.IGNORECASE),
        ),
        (
            "jwt",
            re.compile(rf"\b{jwt_prefix}[A-Za-z0-9_-]{{10,}}\.[A-Za-z0-9_-]{{10,}}"),
        ),
        (
            "credential-assignment",
            re.compile(
                r"""(?ix)
                \b(api[_-]?key|access[_-]?token|auth[_-]?token|password|
                passwd|passphrase|client[_-]?secret|service[_-]?role[_-]?key)
                \b\s*[:=]\s*["']?[A-Za-z0-9+/=_-]{12,}
                """
            ),
        ),
        (
            "authorization-header",
            re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+\S+"),
        ),
        (
            "connection-string",
            re.compile(rf"(?i)\b{connection_schemes}://\S+"),
        ),
        (
            "email-address",
            re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        ),
    )


IPV4_CANDIDATE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")


def _is_ipv4(value: str) -> bool:
    return all(0 <= int(part) <= 255 for part in value.split("."))


def _git_paths(mode: str, root: Path) -> list[Path]:
    if mode == "all":
        command = ("git", "ls-files", "-z")
    else:
        command = (
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        )
    result = subprocess.run(
        command,
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [
        root / raw.decode("utf-8")
        for raw in result.stdout.split(b"\0")
        if raw
    ]


def _scan_file(path: Path, root: Path) -> list[Finding]:
    relative = path.relative_to(root)
    try:
        payload = path.read_bytes()
    except OSError:
        return [Finding(relative, 0, "unreadable-file")]
    if len(payload) > MAX_FILE_BYTES:
        return [Finding(relative, 0, "file-size-limit")]
    if b"\0" in payload:
        return [Finding(relative, 0, "binary-content")]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return [Finding(relative, 0, "non-utf8-content")]

    findings: list[Finding] = []
    patterns = _secret_patterns()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in patterns:
            if pattern.search(line):
                findings.append(Finding(relative, line_number, rule))
        for match in IPV4_CANDIDATE.finditer(line):
            if _is_ipv4(match.group(0)):
                findings.append(Finding(relative, line_number, "ipv4-address"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="scan all tracked files")
    group.add_argument(
        "--staged",
        action="store_true",
        help="scan added or modified files staged for commit",
    )
    args = parser.parse_args()

    root_result = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    root = Path(root_result.stdout.strip()).resolve()
    mode = "all" if args.all else "staged"
    paths = _git_paths(mode, root)
    if not paths:
        print(f"PASS: no {mode} files to scan")
        return 0

    findings = [
        finding
        for path in paths
        for finding in _scan_file(path, root)
    ]
    if findings:
        print("BLOCKED: public-content scan found prohibited or unsafe content")
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.rule}")
        return 1

    print(f"PASS: scanned {len(paths)} {mode} text files; no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
