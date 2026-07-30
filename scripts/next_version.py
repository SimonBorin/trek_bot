#!/usr/bin/env python3
"""Resolve the current release or calculate the next patch SemVer."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable

SEMVER_PATTERN = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def parse_version(value: str) -> tuple[int, int, int] | None:
    match = SEMVER_PATTERN.fullmatch(value.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def latest_version(tags: Iterable[str]) -> tuple[int, int, int] | None:
    versions = (version for tag in tags if (version := parse_version(tag)) is not None)
    return max(versions, default=None)


def format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def next_version(tags: Iterable[str]) -> str:
    current = latest_version(tags)
    if current is None:
        raise RuntimeError("A stable SemVer tag is required to calculate the next version")
    major, minor, patch = current
    return format_version((major, minor, patch + 1))


def git_tags(*arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", "tag", *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def repository_version() -> str:
    current = latest_version(git_tags("--points-at", "HEAD"))
    if current is not None:
        return format_version(current)
    return next_version(git_tags("--list"))


def main() -> int:
    print(repository_version())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
