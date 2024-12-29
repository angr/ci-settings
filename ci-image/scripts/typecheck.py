#!/usr/bin/env python3
import sys
import subprocess
import json
import dataclasses
import os

@dataclasses.dataclass
class FileReport:
    filename: str
    diagnostics: list[tuple[int, int, str, str]]
    errors: int = 0
    warnings: int = 0
    lines: int = 0
    score: float = 0.

def count_lines(filename):
    with open(filename, 'rb') as fp:
        return sum(1 for _ in fp)

def typecheck_files(filenames):
    filenames = [filename for filename in filenames if os.path.exists(filename)]
    if not filenames:
        return {}
    proc = subprocess.run(["pyright", "--outputjson", *filenames], text=False, check=False, stdout=subprocess.PIPE)
    pyright_report = json.loads(proc.stdout)
    my_report = {os.path.realpath(filename): FileReport(filename, diagnostics=[], lines=count_lines(filename)) for filename in filenames}
    for diagnostic in pyright_report["generalDiagnostics"]:
        severity = diagnostic["severity"]
        filename = diagnostic["file"]
        if severity == "error":
            my_report[filename].errors += 1
        elif severity == "warning":
            my_report[filename].warnings += 1
        start = diagnostic["range"]["start"]
        my_report[filename].diagnostics.append((start["line"], start["character"], severity, diagnostic["message"]))

    for report in my_report.values():
        report.score = (report.errors * 10 + report.warnings) / report.lines

    return my_report

def typecheck_diff(rev1, rev2):
    print(f"Comparing {rev1} --> {rev2}")
    print()
    filenames = subprocess.check_output(["git", "diff", "--name-only", f"{rev1}...{rev2}"], text=True).splitlines()
    subprocess.check_call(["git", "checkout", rev1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report1 = typecheck_files(filenames)
    subprocess.check_call(["git", "checkout", rev2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report2 = typecheck_files(filenames)

    status = 0

    for filename in filenames:
        filename = os.path.realpath(filename)
        if filename not in report1 or filename not in report2:
            continue
        e1 = report1[filename]
        e2 = report2[filename]
        if e2.score > e1.score:
            status += 1
            print(f"### {filename} badness increased from {e1.score} to {e2.score}. Please fix:")
            for line, char, severity, text in sorted(e2.diagnostics):
                print(f"{filename}:{line}:{char}: [{severity}] {text}")
        elif e2.score < e1.score:
            print(f"### {filename} badness decreased from {e1.score} to {e2.score}. Nice!")
        else:
            print(f"### {filename} badness remained at {e1.score}. Nice!")

    if status > 0:
        print(f"\n{status} files regressed. Fix them!")
        return 1
    else:
        print("\nYou did it!")
        return 0

if __name__ == '__main__':
    sys.exit(typecheck_diff(sys.argv[1], sys.argv[2]))
