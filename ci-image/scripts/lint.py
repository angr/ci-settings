#!/usr/bin/env python

import os
import re
import sys
import subprocess

os.environ["PYLINTRC"] = '/root/conf/pylintrc'

MESSAGE_RE = re.compile(r".+:\d+:\d+: [A-Z]\d{4}: ")

def lint_file(filename: str) -> tuple[list[str], int]:
    try:
        pylint_out = subprocess.check_output(["pylint", os.path.abspath(filename)]).decode()
    except subprocess.CalledProcessError as e:
        if e.returncode == 32:
            print(f"LINT FAILURE: pylint failed to run on {filename}")
            return [ "LINT FAILURE: pylint failed to run" ], sys.maxsize
        pylint_out = e.output.decode()

    messages = [ line for line in pylint_out.split('\n') if MESSAGE_RE.match(line) ]
    return messages, len(messages)

def lint_files(tolint: list[str]) -> dict[str, tuple[list[str], int]]:
    return { f: lint_file(f) for f in tolint if os.path.isfile(f) }

def compare_lint() -> bool:
    subprocess.call("git fetch --unshallow".split())
    subprocess.check_call("git fetch origin +refs/heads/master:refs/remotes/origin/master".split())
    cur_branch = subprocess.check_output("git rev-parse --abbrev-ref HEAD".split()).decode().strip()
    if cur_branch == "master":
        compare_ref = 'HEAD^'
    else:
        compare_ref = subprocess.check_output(f"git merge-base origin/master {cur_branch}".split()).decode().strip()

    # get the files to lint
    changed_files = [
        o.split()[-1] for o in
        subprocess.check_output(f"git diff --name-status {compare_ref}".split()).decode().split("\n")[:-1]
    ]
    tolint = [ f for f in changed_files if f.endswith(".py") and os.path.exists(f)]
    print(f"Changed files: {tolint}")

    if len(tolint) > 150:
        print("")
        print("...You know what, I trust you")
        return True

    new_results = lint_files(tolint)
    subprocess.check_call(f"git checkout -q {compare_ref}".split())
    try:
        old_results = lint_files(tolint)
    finally:
        subprocess.check_call(f"git checkout -q {cur_branch}".split())

    repo = os.path.basename(os.getcwd())
    print("")
    print("###")
    print(f"### LINT REPORT FOR {repo}")
    print("###")
    print("")

    regressions: list[tuple[str, int | None, int]] = [ ]
    for v in new_results:
        new_messages, new_count = new_results[v]
        if v not in old_results:
            if new_count != 0:
                print(f"LINT FAILURE: new file {v} has {new_count} messages. Please fix:")
                print("... " + "\n... ".join(new_messages))
                regressions.append((v, None, new_count))
            else:
                print(f"LINT SUCCESS: new file {v} has no messages!")
        else:
            _, old_count = old_results[v]
            if new_count > old_count:
                print(f"LINT FAILURE: {v} messages increased from {old_count} to {new_count}. Please fix:")
                print("... " + "\n... ".join(new_messages))
                regressions.append((v, old_count, new_count))
            elif new_count < old_count:
                print(f"LINT SUCCESS: {v} messages decreased from {old_count} to {new_count}!")
            else:
                print(f"LINT SUCCESS: {v} messages remained at {new_count}")

    print("")
    print("###")
    print(f"### END LINT REPORT FOR {repo}")
    print("###")
    print("")

    return len(regressions) == 0


if __name__ == '__main__':
    sys.exit(0 if compare_lint() else 1)

