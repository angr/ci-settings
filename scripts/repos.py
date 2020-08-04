import os

import yaml

REPOS_CONFIG = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "etc", "repos.yml"
)


class Repo:
    name: str
    repo: str
    python: bool = True

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def parse_repos(path):
    with open(path, "r") as f:
        raw = yaml.load(f, Loader=yaml.Loader)
    return [Repo(**r) for r in raw["repos"]]
