#!/usr/bin/env python3

import sys
import os
from github import Github, GithubException
from collections import namedtuple

Target = namedtuple('Target', ['owner', 'repo', 'branch', 'package_name'])
join = os.path.join

# API requests are rate limited... so we try to be thrifty.  API requests are commented.


def load_config(fname):
    sources = []

    with open(fname) as fp:
        for line in fp:
            if '#' in line:
                line = line[:line.index('#')]
            line = line.strip()
            if not line:
                continue
            if line[0] == '!':
                line = line[1:]
                is_package = False
            else:
                is_package = True

            namespace, repo = line.split('/')
            if is_package:
                if ':' in repo:
                    repo, package_name = repo.split(':')
                else:
                    package_name = repo
            else:
                package_name = None
            sources.append(Target(
                owner=namespace,
                repo=repo,
                branch='master',
                package_name=package_name))

    return sources


def main(conf_dir, out_dir, target_repo, ref):
    sources = load_config(join(conf_dir, 'repo-list.txt'))

    if ref.startswith('refs/pull/'):
        targets = sync_reqs_pr(sources, target_repo, int(ref.split('/')[2]))
    elif ref.startswith('refs/heads/'):
        targets = sync_reqs_branch(sources, ref.split('/', 2)[-1])
    else:
        print("I don't know how to process ref %s - must start with 'refs/pull/' or 'refs/heads/'" % ref)
        return 1

    with open(join(conf_dir, 'requirements.txt.template')) as fp:
        reqs_base = fp.read()
    with open(join(conf_dir, 'install.sh.template')) as fp:
        script_base, script_tail = fp.read().split('#{TEMPLATE}\n')

    with open(join(out_dir, 'requirements.txt'), 'w') as fp_reqs:
        with open(join(out_dir, 'install.sh'), 'w') as fp_script:
            fp_reqs.write(reqs_base)
            fp_script.write(script_base)

            for target in targets:
                if target.package_name is not None:
                    fp_reqs.write('-e git+https://github.com/%s/%s.git@%s#egg=%s\n' %
                            (target.owner, target.repo, target.branch, target.package_name))
                else:
                    if target.branch.startswith('refs/'):
                        fp_script.write('git clone https://github.com/%s/%s.git && '
                                        'cd %s && '
                                        'git fetch origin %s && '
                                        'git checkout FETCH_HEAD\n' %
                                (target.owner, target.repo, target.repo, target.branch))
                    else:
                        fp_script.write('git clone -b %s https://github.com/%s/%s.git\n' %
                                (target.branch, target.owner, target.repo))

            fp_script.write(script_tail)

    os.chmod(join(out_dir, 'install.sh'), 0o755)
    return 0

def sync_reqs_branch(sources, branch):
    g = Github()
    for source in sources:
        # save on API calls by not bothering with this nonsense while testing master
        if branch != 'master':
            shortname = '%s/%s' % (source.owner, source.repo)
            r = g.get_repo(shortname, lazy=True)
            try:
                r.get_branch(branch)                            # API: get branch, 1 per target
            except GithubException:
                chosen_branch = 'master'
            else:
                chosen_branch = branch
        else:
            chosen_branch = 'master'

        yield source._replace(branch=chosen_branch)

def sync_reqs_pr(sources, repo_name, pull_number):
    g = Github()
    repo = g.get_repo(repo_name, lazy=True)
    pull = repo.get_pull(pull_number)                       # API: get pull, 1 per build

    # mapping from repo name to a partial Target object
    result_pulls = {}

    # grab the appropriate source object and update it for the current PR
    for source in sources:
        if repo_name == '%s/%s' % (source.owner, source.repo):
            result_pulls[source.repo] = source._replace(
                branch='refs/pull/%d/%s' % (pull_number, 'merge' if pull.mergeable else 'head'))
            break
    else:
        raise ValueError("repo_name %s doesn't match any source spec" % repo_name)

    for word in pull.body.split():
        if '#' not in word:
            continue
        target_repo_name, target_pull_name = word.strip(',;').split('#', 1)

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

        # must actually be a pull request!
        target_pull_number = int(target_pull_name)
        target_repo = g.get_repo(target_repo_name, lazy=True)
        try:
            target_pull = target_repo.get_pull(target_pull_number)  # API: get pull, 1 per link
        except GithubException:
            continue

        # must not have seen this repo before...?
        # pylint: disable=undefined-loop-variable
        if source.repo in result_pulls:
            print("Warning: multiple references to pull requests of %s" % source.repo)
            continue

        result_pulls[source.repo] = source._replace(
            branch='refs/pull/%d/%s' %
                   (target_pull_number,
                    'merge' if target_pull.mergeable else 'head'))

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
