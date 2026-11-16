#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_URL = "https://github.com/angr/sibling-ref-fixture.git"
PULL_NUMBER = 7


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def create_fixture_repository(path: Path) -> tuple[str, str]:
    path.mkdir(parents=True)
    run(["git", "init", "--initial-branch=master"], cwd=path)
    run(["git", "config", "user.name", "ci-settings test"], cwd=path)
    run(["git", "config", "user.email", "ci-settings@example.invalid"], cwd=path)
    write(
        path / "pyproject.toml",
        """[project]
name = "sibling-ref-fixture"
version = "0.0.0"

[build-system]
requires = ["setuptools==80.9.0"]
build-backend = "setuptools.build_meta"
""",
    )
    module = path / "sibling_ref_fixture" / "__init__.py"
    write(module, 'SELECTED_REF = "master"\n')
    run(["git", "add", "pyproject.toml", "sibling_ref_fixture/__init__.py"], cwd=path)
    run(["git", "commit", "-m", "master fixture"], cwd=path)
    master_commit = run(["git", "rev-parse", "HEAD"], cwd=path)

    write(module, 'SELECTED_REF = "pull"\n')
    run(["git", "add", "sibling_ref_fixture/__init__.py"], cwd=path)
    run(["git", "commit", "-m", "pull request fixture"], cwd=path)
    pull_commit = run(["git", "rev-parse", "HEAD"], cwd=path)
    run(["git", "update-ref", f"refs/pull/{PULL_NUMBER}/head", pull_commit], cwd=path)
    run(["git", "reset", "--hard", master_commit], cwd=path)
    return master_commit, pull_commit


def create_project(path: Path) -> None:
    path.mkdir(parents=True)
    write(
        path / "pyproject.toml",
        f"""[project]
name = "sibling-ref-consumer"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = ["sibling-ref-fixture"]

[dependency-groups]
dev = ["typing-extensions==4.15.0"]

[tool.uv]
default-groups = []

[tool.uv.sources]
sibling-ref-fixture = {{ git = "{REPOSITORY_URL}", branch = "master" }}
""",
    )


def append_github_env(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as github_env:
        for name, value in values.items():
            github_env.write(f"{name}={value}\n")


def integration_environment(root: Path, project: Path, api_root: Path, git_config: Path) -> dict[str, str]:
    return {
        "SIBLING_REFS_TEST_ROOT": str(root),
        "SIBLING_REFS_TEST_PROJECT": str(project),
        "SIBLING_REFS_TEST_API_URL": api_root.as_uri(),
        "GIT_CONFIG_GLOBAL": str(git_config),
        "UV_CACHE_DIR": str(root / "uv-cache"),
    }


def prepare(root: Path, github_env: Path | None) -> None:
    if root.exists():
        raise FileExistsError(f"Refusing to replace existing integration directory: {root}")
    root.mkdir(parents=True)
    fixture_repository = root / "sibling-repository"
    master_commit, pull_commit = create_fixture_repository(fixture_repository)
    project = root / "project"
    create_project(project)

    api_root = root / "github-api"
    write(
        api_root / "repos" / "angr" / "sibling-ref-fixture" / "pulls" / str(PULL_NUMBER),
        json.dumps({"state": "open"}),
    )
    git_config = root / "gitconfig"
    run(["git", "config", "--file", str(git_config), "protocol.file.allow", "always"])
    run(
        [
            "git",
            "config",
            "--file",
            str(git_config),
            f"url.{fixture_repository.as_uri()}.insteadOf",
            REPOSITORY_URL,
        ]
    )
    environment_values = integration_environment(root, project, api_root, git_config)
    environment = os.environ.copy()
    environment.update(environment_values)
    run(["uv", "lock", "--python", sys.executable], cwd=project, env=environment)
    seeded_lock = (project / "uv.lock").read_text(encoding="utf-8")
    if master_commit not in seeded_lock:
        raise AssertionError(f"Seeded uv.lock does not contain master commit {master_commit}")
    if pull_commit in seeded_lock:
        raise AssertionError(f"Seeded uv.lock unexpectedly contains pull commit {pull_commit}")
    state = {
        "master_commit": master_commit,
        "pull_commit": pull_commit,
        "pull_number": PULL_NUMBER,
        "project": str(project),
        "api_url": api_root.as_uri(),
        "git_config": str(git_config),
        "seeded_lock_sha256": hashlib.sha256(seeded_lock.encode()).hexdigest(),
    }
    write(root / "state.json", json.dumps(state))
    if github_env is not None:
        append_github_env(github_env, environment_values)


def verify(root: Path, scenario: str) -> None:
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    project = Path(state["project"])
    lock_path = project / "uv.lock"
    if not lock_path.is_file():
        raise AssertionError("The prepared project no longer has its seeded uv.lock")
    seeded_lock = lock_path.read_text(encoding="utf-8")
    if hashlib.sha256(seeded_lock.encode()).hexdigest() != state["seeded_lock_sha256"]:
        raise AssertionError("uv.lock changed before the selected-ref lock step")
    if state["master_commit"] not in seeded_lock:
        raise AssertionError("The prepared uv.lock no longer contains the master commit")
    if state["pull_commit"] in seeded_lock:
        raise AssertionError("The prepared uv.lock already contains the pull commit")

    run(["uv", "lock", "--python", sys.executable], cwd=project)
    run(["uv", "sync", "--locked", "--python", sys.executable], cwd=project)

    expected_name = "pull" if scenario == "selected" else "master"
    expected_commit = state[f"{expected_name}_commit"]
    lock = lock_path.read_text(encoding="utf-8")
    if expected_commit not in lock:
        raise AssertionError(f"uv.lock does not contain expected {expected_name} commit {expected_commit}")
    if scenario == "selected":
        if lock == seeded_lock:
            raise AssertionError("The selected-ref lock step did not update the seeded uv.lock")
        if state["master_commit"] in lock:
            raise AssertionError("The selected-ref uv.lock still contains the master commit")
    elif lock != seeded_lock:
        raise AssertionError("The normal lock step changed the seeded master uv.lock")
    config_file = os.environ.get("UV_CONFIG_FILE")
    if scenario == "selected":
        if config_file is None:
            raise AssertionError("The selected-ref action did not export UV_CONFIG_FILE")
        config = Path(config_file).read_text(encoding="utf-8")
        if f"@refs/pull/{state['pull_number']}/head" not in config:
            raise AssertionError("The selected-ref config does not name the pull request ref")
    elif config_file is not None:
        raise AssertionError("The no-reference action unexpectedly exported a config file")

    python = project / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    selected_ref = run([str(python), "-c", "import sibling_ref_fixture; print(sibling_ref_fixture.SELECTED_REF)"])
    if selected_ref != expected_name:
        raise AssertionError(f"Expected {expected_name} fixture, got {selected_ref}")
    marker = run(
        [
            str(python),
            "-c",
            "import importlib.util; print(importlib.util.find_spec('typing_extensions') is not None)",
        ]
    )
    if marker != "False":
        raise AssertionError("The project's default-groups = [] setting was not preserved")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--root", type=Path, required=True)
    prepare_parser.add_argument("--github-env", type=Path)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--scenario", choices=("selected", "normal"), required=True)
    args = parser.parse_args()

    if args.command == "prepare":
        prepare(args.root, args.github_env)
    else:
        verify(args.root, args.scenario)
    return 0


if __name__ == "__main__":
    sys.exit(main())
