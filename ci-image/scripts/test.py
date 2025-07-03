#!/usr/bin/env python3

import os
import subprocess
import sys

from repos import Target, load_config


GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "angr/angr")
REPO = GITHUB_REPOSITORY.split("/")[-1]
NUM_WORKERS = os.environ.get("NUM_WORKERS", 1)
# Adjust WORKER to be 1-indexed for pytest-split
WORKER = int(os.environ.get("WORKER", 0)) + 1
NIGHTLY = os.environ.get("NIGHTLY", "false").lower() == "true"
INCLUDE_SELF = os.environ.get("INCLUDE_SELF", "true").lower() == "true"


def test_project(project: str) -> bool:
    command = (
        f"pytest -v -nauto --splits {NUM_WORKERS} --group {WORKER} "
        f"--rootdir=./src/{project}/tests ./src/{project}/tests"
    )

    if not NIGHTLY:
        command += ' -m "not slow"'

    print(f"Running test command:\n{command}", flush=True)
    rc = subprocess.run(command, shell=True).returncode
    if rc not in (0, 5):
        print(f"Tests failed for {project} with return code {rc}", flush=True)
        return False
    else:
        print(f"Tests passed for {project}", flush=True)
        return True


def build_reverse_deps(targets: list[Target]) -> dict[str, set[str]]:
    reverse_deps: dict[str, set[str]] = {}
    for t in targets:
        for dep in t.deps:
            reverse_deps.setdefault(dep, set()).add(t.repo)
    return reverse_deps


def collect_all_dependents(repo: str, reverse_deps: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    stack = [repo]
    while stack:
        current = stack.pop()
        for dep in reverse_deps.get(current, []):
            if dep not in result:
                result.add(dep)
                stack.append(dep)
    return result


def main():
    targets: list[Target] = load_config("/root/conf/repo-list.txt")

    reverse_deps = build_reverse_deps(targets)
    repo_dependents = collect_all_dependents(REPO, reverse_deps)
    if INCLUDE_SELF:
        repo_dependents.add(REPO)

    fail_count = 0
    for repo in sorted(repo_dependents):
        fail_count += int(not test_project(repo))

    sys.exit(fail_count)


if __name__ == "__main__":
    main()
