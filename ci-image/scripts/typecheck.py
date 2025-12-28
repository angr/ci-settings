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
    # HACK - a dep of pyright added a spruious print on first use
    stdout = proc.stdout.removeprefix(b"{'x86': False, 'risc': False, 'lts': False}\n")
    pyright_report = json.loads(stdout)
    my_report = {os.path.realpath(filename): FileReport(filename, diagnostics=[], lines=count_lines(filename)) for filename in filenames}
    for diagnostic in pyright_report["generalDiagnostics"]:
        severity = diagnostic["severity"]
        filename = diagnostic["file"]
        if severity == "error":
            my_report[filename].errors += 1
        elif severity == "warning":
            my_report[filename].warnings += 1
        start = diagnostic.get("range", {"start": {"line": 1, "character": 1}})["start"]
        my_report[filename].diagnostics.append((start["line"], start["character"], severity, diagnostic["message"]))

    for report in my_report.values():
        report.score = (report.errors * 10 + report.warnings) / report.lines

    return my_report

def filter_py(names):
    return [name for name in names if name.endswith('.py') or name.endswith('.pyi')]

def typecheck_diff(rev1, rev2):
    print(f"Comparing {rev1} --> {rev2}")
    print()
    filenames = subprocess.check_output(["git", "diff", "--name-only", f"{rev1}...{rev2}"], text=True).splitlines()
    filenames = filter_py(filenames)
    subprocess.check_call(["git", "checkout", rev2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report2 = typecheck_files(filenames)
    subprocess.check_call(["git", "checkout", rev1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report1 = typecheck_files(report2)

    status = 0

    for filename in filenames:
        filename = os.path.realpath(filename)
        if filename not in report2:
            continue
        if filename in report1:
            base_score = report1[filename].score
        else:
            base_score = 0
        e2 = report2[filename]
        if e2.score > base_score:
            status += 1
            print(f"### {filename} badness increased from {base_score} to {e2.score}. Please fix:")
            for line, char, severity, text in sorted(e2.diagnostics):
                print(f"{filename}:{line}:{char}: [{severity}] {text}")
        elif e2.score < base_score:
            print(f"### {filename} badness decreased from {base_score} to {e2.score}. Nice!")
        else:
            print(f"### {filename} badness remained at {base_score}. Nice!")

    if status > 0:
        print(f"\n{status} files regressed. Fix them!")
        return 1
    else:
        print("\nYou did it!")
        return 0

if __name__ == '__main__':
    sys.exit(typecheck_diff(sys.argv[1], sys.argv[2]))
