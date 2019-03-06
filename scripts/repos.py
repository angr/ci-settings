from collections import namedtuple

Target = namedtuple('Target', ['owner', 'repo', 'branch', 'package_name', 'deps'])

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

            if '->' in line:
                source, deps = line.split('->')
                source = source.strip()
                deps = deps.strip()
                deps = [dep.strip() for dep in deps.split(',')]
            else:
                source = line
                deps = []

            namespace, repo = source.split('/')
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
                package_name=package_name,
                deps=deps))

    return sources
