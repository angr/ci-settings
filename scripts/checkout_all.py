import os
import shlex
import subprocess

import yaml

from repos import parse_repos, REPOS_CONFIG


def checkout_repo(dir, repo):
    checkout_dir = os.path.join(dir, repo.name)
    clone_str = f"git clone git@github.com:angr/{repo.name}.git {checkout_dir} --depth=1"
    subprocess.run(shlex.split(clone_str), check=True).check_returncode()


def main():
    repos = parse_repos(REPOS_CONFIG)

    os.mkdir("repos")

    for repo in repos:
        checkout_repo("repos", repo)


if __name__ == "__main__":
    main()
