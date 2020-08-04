import os
import shlex
import subprocess

import yaml

from repos import parse_repos, REPOS_CONFIG


def checkout_repo(dir, repo, commit):
    checkout_dir = os.path.join(dir, repo.name)
    clone_str = f"git clone git@github.com:angr/{repo.name}.git {checkout_dir}"
    subprocess.run(shlex.split(clone_str), check=True).check_returncode()
    subprocess.run(
        shlex.split(f"git -C {checkout_dir} checkout -q {commit}"), check=True
    ).check_returncode()


def parse_commits(path):
    with open(path, "r") as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def main():
    repos = parse_repos(REPOS_CONFIG)
    commits = parse_commits("versions.yml")

    os.mkdir("repos")

    for repo in repos:
        checkout_repo("repos", repo, commits[repo.name])


if __name__ == "__main__":
    main()
