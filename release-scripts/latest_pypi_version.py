"""Print the most recent version of a package published on PyPI.

Used by the angr release scripts to pin angr to the latest released angr-data
(which is published from its own separate pipeline). Prints an empty string if
the package has never been published or PyPI is unreachable, so callers can
leave the existing pin untouched.
"""

import json
import sys
import urllib.request


def main() -> None:
    if len(sys.argv) != 2:
        print("")
        return
    package = sys.argv[1]
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json", timeout=30) as resp:
            data = json.load(resp)
        print(data["info"]["version"])
    except Exception:  # pylint: disable=broad-except
        print("")


if __name__ == "__main__":
    main()
