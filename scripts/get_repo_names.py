#!/usr/bin/env python3
import sys

from repos import parse_repos, REPOS_CONFIG

repos = parse_repos(REPOS_CONFIG)
if "--python-only" in sys.argv:
    print(" ".join([repo.name for repo in repos if repo.python]))
else:
    print(" ".join([repo.name for repo in repos]))
