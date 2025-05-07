#!/usr/bin/env python3

import os
import sys
import typing
import unittest

from github import Github, GithubException
from github.PullRequest import PullRequest


def parse_directives(text: str) -> typing.List[str]:
    directives = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("ci:"):
            for directive in line[3:].split("#")[0].split(","):
                directive = directive.strip()
                if directive != "" and directive not in directives:
                    directives.append(directive.strip())

    return directives


class TestParseDirectives(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_directives(""), [])

    def test_single(self):
        self.assertEqual(parse_directives("ci: foo"), ["foo"])

    def test_multiple(self):
        self.assertEqual(parse_directives("ci: foo, bar, baz"), ["foo", "bar", "baz"])

    def test_multiple_with_whitespace(self):
        self.assertEqual(parse_directives("ci: foo,  bar, baz"), ["foo", "bar", "baz"])

    def test_multiple_with_whitespace_and_commas(self):
        self.assertEqual(parse_directives("ci: foo, , bar, baz"), ["foo", "bar", "baz"])

    def test_multiple_with_whitespace_and_commas_and_comments(self):
        self.assertEqual(
            parse_directives("ci: foo, , bar, baz # comment"), ["foo", "bar", "baz"]
        )

    def test_multiple_with_whitespace_and_commas_and_comments_and_other_stuff(self):
        self.assertEqual(
            parse_directives(
                "ci: foo, , bar, baz # comment\nci: foo, , bar, baz # comment"
            ),
            ["foo", "bar", "baz"],
        )


def main():
    github = Github(os.getenv("GITHUB_TOKEN"))
    repo = github.get_repo(os.getenv("GITHUB_REPOSITORY"), lazy=True)
    ref = os.getenv("GITHUB_REF")
    if "refs/pull/" not in ref:
        # This is not a pull request
        return

    pull_number = int(ref.split("/")[2])
    pull_request = repo.get_pull(pull_number)
    body = pull_request.body
    if body is None:
        # No body, so no directives
        return

    print(" ".join(parse_directives(body)))


if __name__ == "__main__":
    main()
