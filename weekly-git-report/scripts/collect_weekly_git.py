#!/usr/bin/env python3
"""Collect current user's weekly git commits and output concise Markdown.

Usage:
  python3 scripts/collect_weekly_git.py --repo <repo_path>
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass
class CommitInfo:
    sha: str
    author_name: str
    author_email: str
    date: str
    subject: str
    files_changed: int
    insertions: int
    deletions: int
    touched_files: List[str]


def run_git(repo: str, args: Sequence[str], check: bool = True) -> str:
    cmd = ["git", "-C", repo, *args]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git command failed: {' '.join(cmd)}")
    return proc.stdout.strip()


def is_git_repo(repo: str) -> bool:
    try:
        out = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
        return out == "true"
    except RuntimeError:
        return False


def get_git_user(repo: str) -> Tuple[Optional[str], Optional[str]]:
    email = run_git(repo, ["config", "user.email"], check=False).strip() or None
    name = run_git(repo, ["config", "user.name"], check=False).strip() or None
    return email, name


def week_range(now: Optional[dt.datetime] = None) -> Tuple[dt.datetime, dt.datetime]:
    now = now or dt.datetime.now().astimezone()
    week_start = (now - dt.timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return week_start, now


def parse_commit_lines(raw: str) -> List[Tuple[str, str, str, str, str]]:
    entries: List[Tuple[str, str, str, str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 5:
            continue
        entries.append((parts[0], parts[1], parts[2], parts[3], parts[4]))
    return entries


def collect_commit_headers(repo: str, since_iso: str, until_iso: str, author_pattern: str) -> List[Tuple[str, str, str, str, str]]:
    pretty = "%H%x1f%an%x1f%ae%x1f%ad%x1f%s"
    args = [
        "log",
        f"--since={since_iso}",
        f"--until={until_iso}",
        f"--author={author_pattern}",
        "--date=iso-strict",
        f"--pretty=format:{pretty}",
    ]
    out = run_git(repo, args, check=False)
    return parse_commit_lines(out)


def parse_numstat(raw: str) -> Tuple[int, int, List[str]]:
    insertions = 0
    deletions = 0
    files: List[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_str, del_str, path = parts[0], parts[1], parts[2]
        if add_str.isdigit():
            insertions += int(add_str)
        if del_str.isdigit():
            deletions += int(del_str)
        files.append(path)
    return insertions, deletions, sorted(set(files))


def collect_commit_details(repo: str, sha: str) -> Tuple[int, int, List[str]]:
    out = run_git(repo, ["show", "--numstat", "--format=", sha], check=False)
    return parse_numstat(out)


def dedup_headers(rows: Iterable[Tuple[str, str, str, str, str]]) -> List[Tuple[str, str, str, str, str]]:
    seen = set()
    result = []
    for row in rows:
        if row[0] in seen:
            continue
        seen.add(row[0])
        result.append(row)
    return result


def build_commits(repo: str, headers: Iterable[Tuple[str, str, str, str, str]]) -> List[CommitInfo]:
    commits: List[CommitInfo] = []
    for sha, author_name, author_email, date, subject in headers:
        ins, dels, files = collect_commit_details(repo, sha)
        commits.append(
            CommitInfo(
                sha=sha,
                author_name=author_name,
                author_email=author_email,
                date=date,
                subject=subject,
                files_changed=len(files),
                insertions=ins,
                deletions=dels,
                touched_files=files,
            )
        )
    return commits


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def render_markdown(
    repo: str,
    week_start: dt.datetime,
    week_end: dt.datetime,
    user_email: Optional[str],
    user_name: Optional[str],
    commits: Sequence[CommitInfo],
) -> str:
    total_files = sum(c.files_changed for c in commits)
    total_ins = sum(c.insertions for c in commits)
    total_del = sum(c.deletions for c in commits)

    lines = [
        f"# Weekly Git Raw Data ({week_start.date()} ~ {week_end.date()})",
        "",
        f"- Repo: `{repo}`",
        f"- Current user: `{user_name or '-'} <{user_email or '-'}>`",
        f"- Commits: **{len(commits)}**",
        f"- Changed files(total by commit): **{total_files}**",
        f"- Diff stats: **+{total_ins} / -{total_del}**",
        "",
        "## Commit List",
    ]

    if not commits:
        lines.extend([
            "",
            "> No commits found for current user in this week.",
        ])
        return "\n".join(lines)

    lines.extend([
        "",
        "| Hash | Date | Message | Files | +/- |",
        "|---|---|---|---:|---:|",
    ])

    for c in commits:
        short = c.sha[:8]
        date = c.date.replace("T", " ")[:19]
        msg = md_escape(c.subject)
        lines.append(
            f"| `{short}` | {date} | {msg} | {c.files_changed} | +{c.insertions}/-{c.deletions} |"
        )

    lines.extend(["", "## Touched Files (Top 20)", ""])
    all_files = {}
    for c in commits:
        for path in c.touched_files:
            all_files[path] = all_files.get(path, 0) + 1

    for idx, (path, cnt) in enumerate(sorted(all_files.items(), key=lambda kv: (-kv[1], kv[0]))[:20], start=1):
        lines.append(f"{idx}. `{path}` ({cnt} commits)")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect weekly git commits for current user")
    parser.add_argument("--repo", default=".", help="Target git repo path")
    parser.add_argument(
        "--author",
        default="",
        help="Optional explicit author filter (email or name regex). Overrides git config user identity",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of Markdown",
    )
    args = parser.parse_args()

    repo = os.path.abspath(args.repo)
    if not is_git_repo(repo):
        print(f"ERROR: not a git repository: {repo}", file=sys.stderr)
        return 2

    week_start, week_end = week_range()
    since_iso = week_start.isoformat()
    until_iso = week_end.isoformat()

    email, name = get_git_user(repo)

    headers: List[Tuple[str, str, str, str, str]] = []
    if args.author:
        headers.extend(collect_commit_headers(repo, since_iso, until_iso, args.author))
    else:
        if email:
            headers.extend(
                collect_commit_headers(repo, since_iso, until_iso, re.escape(email))
            )
        if name:
            headers.extend(
                collect_commit_headers(repo, since_iso, until_iso, re.escape(name))
            )

    headers = dedup_headers(headers)
    commits = build_commits(repo, headers)

    commits.sort(key=lambda c: c.date, reverse=True)

    if args.json:
        payload = {
            "repo": repo,
            "user": {"name": name, "email": email},
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "commits": [
                {
                    "sha": c.sha,
                    "author_name": c.author_name,
                    "author_email": c.author_email,
                    "date": c.date,
                    "subject": c.subject,
                    "files_changed": c.files_changed,
                    "insertions": c.insertions,
                    "deletions": c.deletions,
                    "touched_files": c.touched_files,
                }
                for c in commits
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(repo, week_start, week_end, email, name, commits))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
