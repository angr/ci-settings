#!/usr/bin/env python

import os
import sys
import subprocess

PYLINT_RC = '/root/conf/pylintrc'

def has_pylint_config() -> bool:
    try:
        with open("pyproject.toml") as f:
            return "[tool.pylint" in f.read()
    except FileNotFoundError:
        return False

def lint_file(filename: str) -> tuple[list[str], float]:
    try:
        cmd = ["pylint"]
        if not has_pylint_config():
            cmd.append(f"--rcfile={PYLINT_RC}")
        cmd.append(os.path.abspath(filename))
        pylint_out = subprocess.check_output(cmd).decode()
    except subprocess.CalledProcessError as e:
        if e.returncode == 32:
            print(f"LINT FAILURE: pylint failed to run on {filename}")
            pylint_out = "-1337/10"
        else:
            pylint_out = e.output.decode()

    if "\n0 statements analysed." in pylint_out:
        return [ ], 10.00

    if "Report" not in pylint_out:
        return [ "LINT FAILURE: syntax error in file?" ], 0

    out_lines = pylint_out.split('\n')
    errors = out_lines[1:out_lines.index('Report')-2]
    score = float(out_lines[-3].split("/")[0].split(" ")[-1])
    return errors, score

def lint_files(tolint: list[str]) -> dict[str, tuple[list[str], float]]:
    return { f: lint_file(f) for f in tolint if os.path.isfile(f) }

def compare_lint() -> bool:
    subprocess.call("git fetch --unshallow".split())
    subprocess.call("git fetch origin master".split())
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

    regressions: list[tuple[str, float | None, float]] = [ ]
    for v in new_results:
        new_errors, new_score = new_results[v]
        if v not in old_results:
            if new_score != 10.00:
                print(f"LINT FAILURE: new file {v} lints at {new_score:.2f}/10.00. Errors:")
                print("... " + "\n... ".join(new_errors))
                regressions.append((v, None, new_score))
            else:
                print(f"LINT SUCCESS: new file {v} is a perfect 10.00!")
        else:
            _, old_score = old_results[v]
            if new_score < old_score:
                print(f"LINT FAILURE: {v} regressed to {new_score:.2f}/{old_score:.2f}")
                print("... " + "\n... ".join(new_errors))
                regressions.append((v, old_score, new_score))
            elif new_score > old_score:
                print(f"LINT SUCCESS: {v} has improved to {new_score:.2f} (from {old_score:.2f})! ")
            else:
                print(f"LINT SUCCESS: {v} has remained at {new_score:.2f} ")

    print("")
    print("###")
    print(f"### END LINT REPORT FOR {repo}")
    print("###")
    print("")

    return len(regressions) == 0


if __name__ == '__main__':
    sys.exit(0 if compare_lint() else 1)

