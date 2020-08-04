import os

from github import Github
import yaml

from repos import parse_repos, REPOS_CONFIG

GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")


def get_latest_commit(gh, repo):
    gh_repo = gh.get_repo(f"angr/{repo.name}")
    branch = gh_repo.get_branch(gh_repo.default_branch)
    return branch.commit.sha


def main():
    if GH_ACCESS_TOKEN:
        gh = Github(GH_ACCESS_TOKEN)
    else:
        gh = Github()

    repos = parse_repos(REPOS_CONFIG)
    version_dict = {r.name: get_latest_commit(gh, r) for r in repos}

    with open("versions.yml", "w") as f:
        f.write(yaml.dump(version_dict, Dumper=yaml.Dumper))


if __name__ == "__main__":
    main()
