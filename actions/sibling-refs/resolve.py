#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tomllib
from typing import Callable, Iterator, NamedTuple
import urllib.error
import urllib.parse
import urllib.request


GITHUB_API_URL = "https://api.github.com"


class GitSource(NamedTuple):
    package: str
    url: str


class Override(NamedTuple):
    package: str
    requirement: str


def parse_references(body: str) -> Iterator[tuple[str, int]]:
    """Yield GitHub repository and pull request pairs in body order."""
    for word in body.replace("(", " ").replace(")", " ").split():
        word = word.strip(",;")
        if "#" in word:
            target_repo_name, target_pull_name = word.split("#", 1)
        elif "github.com" in word and "pull/" in word:
            parts = word.split("/")[-4:]
            if len(parts) != 4:
                continue
            owner, name, pull_component, target_pull_name = parts
            if pull_component != "pull":
                continue
            target_repo_name = f"{owner}/{name}"
        else:
            continue

        if target_repo_name.count("/") == 1 and target_pull_name.isdigit():
            yield target_repo_name.lower(), int(target_pull_name)


def github_repository(url: str) -> str | None:
    """Return owner/repository for a GitHub git URL."""
    if url.startswith("git+"):
        url = url[4:]

    match = re.fullmatch(
        r"https?://github\.com/(?P<owner>[A-Za-z0-9-]+)/(?P<repository>[A-Za-z0-9_.-]+)",
        url,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    owner = match.group("owner")
    repository = match.group("repository")
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not owner or not repository:
        return None
    return f"{owner}/{repository}".lower()


def load_git_sources(project_directory: Path) -> dict[str, list[GitSource]]:
    with (project_directory / "pyproject.toml").open("rb") as pyproject:
        data = tomllib.load(pyproject)

    source_table = data.get("tool", {}).get("uv", {}).get("sources", {})
    result: dict[str, list[GitSource]] = {}
    for package, value in source_table.items():
        if isinstance(value, list):
            print(f"Skipping {package}: conditional source lists are not supported", file=sys.stderr)
            continue
        if not isinstance(value, dict) or not isinstance(value.get("git"), str):
            continue
        unsupported_keys = set(value) - {"git", "branch", "tag", "rev"}
        if unsupported_keys:
            keys = ", ".join(sorted(unsupported_keys))
            print(f"Skipping {package}: unsupported git source settings: {keys}", file=sys.stderr)
            continue

        url = value["git"]
        if not url.startswith(("https://", "http://", "git+https://", "git+http://")):
            print(f"Skipping {package}: only HTTP(S) git source URLs are supported", file=sys.stderr)
            continue
        repository = github_repository(url)
        if repository is None:
            print(f"Skipping {package}: git source is not a simple GitHub repository URL", file=sys.stderr)
            continue
        result.setdefault(repository, []).append(GitSource(package, url))
    return result


def pull_request_state(api_url: str, repository: str, number: int, token: str | None) -> str | None:
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/repos/{repository}/pulls/{number}",
        headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, ValueError) as error:
        print(f"Could not resolve {repository}#{number}: {error}", file=sys.stderr)
        return None
    state = data.get("state")
    return state if isinstance(state, str) else None


def github_api_configuration() -> tuple[str, str | None]:
    test_api_url = os.environ.get("SIBLING_REFS_TEST_API_URL")
    if test_api_url is not None:
        parsed = urllib.parse.urlparse(test_api_url)
        if (
            parsed.scheme.lower() != "file"
            or parsed.netloc.lower() not in ("", "localhost")
            or not parsed.path
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("SIBLING_REFS_TEST_API_URL must be a local file: URL")
        return test_api_url, None

    return os.environ.get("GITHUB_API_URL") or GITHUB_API_URL, os.environ.get("GH_TOKEN")


def resolve_overrides(
    body: str,
    sources: dict[str, list[GitSource]],
    state_lookup: Callable[[str, int], str | None],
) -> list[Override]:
    overrides: list[Override] = []
    resolved_repositories: set[str] = set()
    resolved_packages: set[str] = set()
    for repository, number in parse_references(body):
        if repository in resolved_repositories or repository not in sources:
            continue

        state = state_lookup(repository, number)
        if state != "open":
            print(f"{repository}#{number} is {state or 'unavailable'}, so it is not used")
            continue

        ref = f"refs/pull/{number}/head"
        for source in sources[repository]:
            normalized_package = source.package.lower()
            if normalized_package in resolved_packages:
                continue
            url = source.url if source.url.startswith("git+") else f"git+{source.url}"
            overrides.append(Override(source.package, f"{source.package} @ {url}@{ref}"))
            resolved_packages.add(normalized_package)
        resolved_repositories.add(repository)
    return overrides


def write_config(path: Path, overrides: list[Override]) -> None:
    lines = ["no-sources-package = ["]
    lines.extend(f"  {json.dumps(override.package)}," for override in overrides)
    lines.append("]")
    lines.append("upgrade-package = [")
    lines.extend(f"  {json.dumps(override.requirement)}," for override in overrides)
    lines.extend(("]", ""))
    path.write_text("\n".join(lines), encoding="utf-8")


def append_github_env(path: Path, config_path: Path) -> None:
    with path.open("a", encoding="utf-8") as github_env:
        github_env.write(f"UV_CONFIG_FILE={config_path}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-env", type=Path, required=True)
    args = parser.parse_args()

    sources = load_git_sources(args.project_directory)
    try:
        api_url, token = github_api_configuration()
    except ValueError as error:
        print(f"Invalid test API override: {error}", file=sys.stderr)
        return 2
    overrides = resolve_overrides(
        os.environ.get("PR_BODY", ""),
        sources,
        lambda repository, number: pull_request_state(api_url, repository, number, token),
    )
    if not overrides:
        print("No open sibling pull requests were selected; uv will use the project's normal sources")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_config(args.output, overrides)
    append_github_env(args.github_env, args.output)
    for override in overrides:
        print(f"Using {override.requirement}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
