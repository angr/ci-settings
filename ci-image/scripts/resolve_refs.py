#!/usr/bin/env python3

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
from typing import Iterable, Iterator, Optional, Sequence, Tuple

sys.path.append(os.path.dirname(os.path.basename(__file__)))
from repos import Target, load_config

join = os.path.join

# API requests are rate limited... so we try to be thrifty.  API requests are commented.


def _get_pr(repo_name: str, pull_number: int) -> Tuple[Optional[str], Optional[str]]:
    """Return (state, body) for the given PR, or (None, None) if the PR doesn't exist."""
    req = urllib.request.Request(
        'https://api.github.com/repos/%s/pulls/%d' % (repo_name, pull_number),
        headers={'Accept': 'application/vnd.github+json'})
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        return data.get('state'), data.get('body')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise


def _branch_exists(owner: str, repo: str, branch: str) -> bool:
    """Return True if `branch` exists on the remote, using git ls-remote (no API quota)."""
    r = subprocess.run(
        ['git', 'ls-remote', '--exit-code', '--heads',
         'https://github.com/%s/%s.git' % (owner, repo),
         'refs/heads/' + branch],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def main(conf_dir: str, out_dir: str, target_repo: str, ref: str) -> int:
    sources = load_config(join(conf_dir, 'repo-list.txt'))

    if target_repo.endswith('.git'):
        target_repo = target_repo[:-4]
    if target_repo.count('/') > 1:
        target_repo = '/'.join(target_repo.split('/')[-2:])

    if ref.startswith('refs/pull/'):
        targets = sync_reqs_pr(sources, target_repo, int(ref.split('/')[2]))
        snapshot_branch = "%s_%s" % (target_repo, int(ref.split('/')[2]))
    elif ref.startswith('refs/heads/'):
        targets = sync_reqs_branch(sources, ref.split('/', 2)[-1])
        snapshot_branch = ref.split('/', 2)[-1]
    else:
        print("I don't know how to process ref %s - must start with 'refs/pull/' or 'refs/heads/'" % ref)
        return 1

    with open(join(conf_dir, 'install.sh.template')) as fp:
        script_body = fp.read()
    script_base, script_tail = script_body.split('#{TEMPLATE}\n')

    with open(join(out_dir, 'install.sh'), 'w') as fp_script:
        fp_script.write(script_base)

        for target in targets:
            # clone the target repo first
            if target.repo == "dec-snapshots":
                fp_script.write('git clone https://github.com/%s/%s.git --depth 1 --branch master\n' %
                        (target.owner, target.repo))
            elif target.branch.startswith('refs/'):
                fp_script.write('git init %s && '
                                'pushd %s && '
                                'git remote add origin https://github.com/%s/%s.git && '
                                'git fetch --depth 1 origin %s && '
                                'git checkout FETCH_HEAD && '
                                'git submodule update --init --recursive --depth 1 && '
                                'popd\n' %
                        (target.repo, target.repo, target.owner, target.repo, target.branch))
            else:
                fp_script.write('git clone --depth 1 --recursive --shallow-submodules -b %s https://github.com/%s/%s.git\n' %
                        (target.branch, target.owner, target.repo))

        fp_script.write('CONF=' + conf_dir + '\n')

        fp_script.write(script_tail)

    with open(join(out_dir, 'snapshot_branch.txt'), 'w') as fp:
        fp.write(snapshot_branch)

    os.chmod(join(out_dir, 'install.sh'), 0o755)
    return 0

def sync_reqs_branch(sources: Iterable[Target], branch: str) -> Iterator[Target]:
    for source in sources:
        # save on API calls by not bothering with this nonsense while testing master
        if branch != 'master' and _branch_exists(source.owner, source.repo, branch):
            chosen_branch = branch
        else:
            chosen_branch = 'master'

        yield source._replace(branch=chosen_branch)

def sync_reqs_pr(sources: Sequence[Target], repo_name: str, pull_number: int) -> Iterator[Target]:
    _, body = _get_pr(repo_name, pull_number)               # API: get pull, 1 per build

    # mapping from repo name to a partial Target object
    result_pulls = {}

    # grab the appropriate source object and update it for the current PR
    for source in sources:
        if repo_name == '%s/%s' % (source.owner, source.repo):
            result_pulls[source.repo] = source._replace(
                branch='refs/pull/%d/head' % pull_number)
            break
    else:
        raise ValueError("repo_name %s doesn't match any source spec" % repo_name)

    # Check if the pull request has a body
    if body is not None:

        for word in body.replace('(', ' ').replace(')', ' ').split():
            if '#' in word:
                target_repo_name, target_pull_name = word.strip(',;').split('#', 1)
            elif "github.com" in word and "pull/" in word:
                t = word.strip(',;').split("/")[-4:]
                if len(t) != 4:
                    continue
                owner, name, p, target_pull_name = t
                target_repo_name = '%s/%s' % (owner, name)
                if p != 'pull':
                    continue
            else:
                continue

            # some sanity checks
            # pull request number must be... a number
            if not target_pull_name.isdigit():
                continue

            # pull request must be to one of the repos we're testing
            for source in sources:
                if target_repo_name == '%s/%s' % (source.owner, source.repo):
                    break
            else:
                continue

            # must not have seen this repo before...?
            target_pull_number = int(target_pull_name)
            # pylint: disable=undefined-loop-variable
            if source.repo in result_pulls:
                print("Warning: multiple references to pull requests of %s" % source.repo)
                continue

            # pull request shouldn't be merged/closed
            target_state, _ = _get_pr(target_repo_name, target_pull_number)  # API: get pull, 1 per link
            if target_state is None:
                continue
            if target_state != 'open':
                print("Warning: PR %s#%d is not open, skipping" % (target_repo_name, target_pull_number))
                continue

            result_pulls[source.repo] = source._replace(
                branch='refs/pull/%d/head' % target_pull_number)

    for source in sources:
        if source.repo in result_pulls:
            yield result_pulls[source.repo]
        else:
            yield source._replace(branch='master')


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
    except IndexError:
        print('usage: resolve-refs.py conf_dir out_dir target_repo ref')
        print('ref is either refs/heads/<branch> or refs/pull/<pr>')
