import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "resolve.py"
SPEC = importlib.util.spec_from_file_location("sibling_refs_resolve", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
resolve = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolve)


class TestParseReferences(unittest.TestCase):
    def test_accepts_hash_and_bare_url_forms_in_body_order(self):
        body = """
        sync: angr/cle#795;
        [dependency](https://github.com/angr/archinfo/pull/375),
        https://github.com/angr/pyvex/pull/576/files
        """
        self.assertEqual(
            list(resolve.parse_references(body)),
            [("angr/cle", 795), ("angr/archinfo", 375)],
        )

    def test_ignores_non_numeric_and_unrelated_text(self):
        self.assertEqual(list(resolve.parse_references("sync: angr/cle#head issue #42")), [])


class TestGitSources(unittest.TestCase):
    def test_loads_only_simple_declared_github_git_sources(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pyproject.toml").write_text(
                """
                [tool.uv.sources]
                renamed-package = { git = "https://github.com/angr/cle.git", branch = "master" }
                prefixed-package = { git = "git+https://github.com/angr/archinfo.git", branch = "master" }
                ssh-package = { git = "git@github.com:angr/archinfo.git", branch = "master" }
                conditional = [
                    { git = "https://github.com/angr/pyvex.git", marker = "sys_platform == 'linux'" },
                ]
                nested = { git = "https://github.com/angr/monorepo.git", subdirectory = "packages/nested" }
                indexed = { index = "custom" }
                elsewhere = { git = "https://example.com/owner/repository.git" }
                """,
                encoding="utf-8",
            )

            with mock.patch("sys.stderr"):
                sources = resolve.load_git_sources(project)
            self.assertEqual(
                sources,
                {
                    "angr/cle": [resolve.GitSource("renamed-package", "https://github.com/angr/cle.git")],
                    "angr/archinfo": [
                        resolve.GitSource("prefixed-package", "git+https://github.com/angr/archinfo.git")
                    ],
                },
            )

    def test_rejects_unsafe_github_git_source_urls(self):
        unsafe_urls = {
            "username": "https://token@github.com/angr/cle.git",
            "password": "https://user:secret@github.com/angr/cle.git",
            "params": "https://github.com/angr/cle.git;token=secret",
            "query": "https://github.com/angr/cle.git?token=secret",
            "fragment": "https://github.com/angr/cle.git#token=secret",
            "empty-query": "https://github.com/angr/cle.git?",
            "empty-fragment": "https://github.com/angr/cle.git#",
            "port": "https://github.com:443/angr/cle.git",
            "extra-path": "https://github.com/angr/cle/tree/master",
            "trailing-slash": "https://github.com/angr/cle.git/",
            "space": "https://github.com/angr/cle repo.git",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            source_lines = [
                f'{package} = {{ git = "{url}", branch = "master" }}' for package, url in unsafe_urls.items()
            ]
            (project / "pyproject.toml").write_text(
                "[tool.uv.sources]\n" + "\n".join(source_lines) + "\n",
                encoding="utf-8",
            )

            with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
                sources = resolve.load_git_sources(project)

            self.assertEqual(sources, {})
            self.assertNotIn("secret", stderr.getvalue())
            self.assertNotIn("token@", stderr.getvalue())


class TestResolveOverrides(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "angr/cle": [resolve.GitSource("cle", "https://github.com/angr/cle.git")],
            "angr/archinfo": [resolve.GitSource("arch-info", "https://github.com/angr/archinfo.git")],
        }

    def test_resolves_multiple_open_siblings(self):
        overrides = resolve.resolve_overrides(
            "sync: angr/cle#795\nsync: https://github.com/angr/archinfo/pull/375",
            self.sources,
            lambda _repository, _number: "open",
        )
        self.assertEqual(
            overrides,
            [
                resolve.Override("cle", "cle @ git+https://github.com/angr/cle.git@refs/pull/795/head"),
                resolve.Override(
                    "arch-info", "arch-info @ git+https://github.com/angr/archinfo.git@refs/pull/375/head"
                ),
            ],
        )

    def test_uses_first_open_reference_for_each_repository(self):
        states = {1: "closed", 2: "open", 3: "open"}
        overrides = resolve.resolve_overrides(
            "angr/cle#1 angr/cle#2 angr/cle#3",
            self.sources,
            lambda _repository, number: states[number],
        )
        self.assertEqual(
            overrides,
            [resolve.Override("cle", "cle @ git+https://github.com/angr/cle.git@refs/pull/2/head")],
        )

    def test_deduplicates_package_names(self):
        sources = {
            "angr/cle": [resolve.GitSource("CLE", "https://github.com/angr/cle.git")],
            "angr/other": [resolve.GitSource("cle", "https://github.com/angr/other.git")],
        }
        overrides = resolve.resolve_overrides(
            "angr/cle#1 angr/other#2",
            sources,
            lambda _repository, _number: "open",
        )
        self.assertEqual(
            overrides,
            [resolve.Override("CLE", "CLE @ git+https://github.com/angr/cle.git@refs/pull/1/head")],
        )

    def test_preserves_normal_sources_for_unavailable_closed_and_undeclared_refs(self):
        states = {("angr/cle", 1): None, ("angr/cle", 2): "closed", ("angr/missing", 3): "open"}
        overrides = resolve.resolve_overrides(
            "angr/cle#1 angr/cle#2 angr/missing#3",
            self.sources,
            lambda repository, number: states[(repository, number)],
        )
        self.assertEqual(overrides, [])

    def test_empty_body_does_not_query_github(self):
        lookup = mock.Mock()
        self.assertEqual(resolve.resolve_overrides("", self.sources, lookup), [])
        lookup.assert_not_called()


class TestGithubApiConfiguration(unittest.TestCase):
    def test_local_test_override_never_receives_the_github_token(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            api_response = Path(temporary_directory) / "repos" / "angr" / "cle" / "pulls" / "1"
            api_response.parent.mkdir(parents=True)
            api_response.write_text('{"state": "open"}', encoding="utf-8")
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "SIBLING_REFS_TEST_API_URL": Path(temporary_directory).as_uri(),
                        "GH_TOKEN": "must-not-leave-the-runner",
                    },
                    clear=True,
                ),
                mock.patch.object(
                    resolve.urllib.request,
                    "urlopen",
                    wraps=resolve.urllib.request.urlopen,
                ) as urlopen,
            ):
                api_url, token = resolve.github_api_configuration()
                self.assertIsNone(token)
                self.assertEqual(resolve.pull_request_state(api_url, "angr/cle", 1, token), "open")

            request = urlopen.call_args.args[0]
            self.assertIsNone(request.get_header("Authorization"))

    def test_rejects_unsafe_test_api_overrides(self):
        unsafe_urls = (
            "https://example.invalid/api",
            "not-a-url",
            "file://example.invalid/api",
            "file:///tmp/api?token=secret",
        )
        for unsafe_url in unsafe_urls:
            with self.subTest(unsafe_url=unsafe_url), mock.patch.dict(
                os.environ,
                {"SIBLING_REFS_TEST_API_URL": unsafe_url, "GH_TOKEN": "must-not-leave-the-runner"},
                clear=True,
            ):
                with self.assertRaisesRegex(ValueError, "must be a local file: URL"):
                    resolve.github_api_configuration()

    def test_production_api_retains_github_authentication(self):
        with (
            mock.patch.dict(
                os.environ,
                {"GITHUB_API_URL": "https://api.github.example", "GH_TOKEN": "production-token"},
                clear=True,
            ),
            mock.patch.object(
                resolve.urllib.request,
                "urlopen",
                return_value=io.BytesIO(b'{"state": "open"}'),
            ) as urlopen,
        ):
            api_url, token = resolve.github_api_configuration()
            self.assertEqual(resolve.pull_request_state(api_url, "angr/cle", 1, token), "open")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.example/repos/angr/cle/pulls/1")
        self.assertEqual(request.get_header("Authorization"), "Bearer production-token")


class TestOutput(unittest.TestCase):
    def test_writes_the_paired_uv_settings(self):
        overrides = [
            resolve.Override("cle", "cle @ git+https://github.com/angr/cle.git@refs/pull/795/head"),
            resolve.Override(
                "renamed-package",
                "renamed-package @ git+https://github.com/angr/archinfo.git@refs/pull/375/head",
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = Path(temporary_directory) / "refs.toml"
            resolve.write_config(config, overrides)
            self.assertEqual(
                config.read_text(encoding="utf-8"),
                """no-sources-package = [
  "cle",
  "renamed-package",
]
upgrade-package = [
  "cle @ git+https://github.com/angr/cle.git@refs/pull/795/head",
  "renamed-package @ git+https://github.com/angr/archinfo.git@refs/pull/375/head",
]
""",
            )

    def test_main_leaves_environment_unchanged_without_an_open_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            project = temporary_path / "project"
            project.mkdir()
            (project / "pyproject.toml").write_text("[tool.uv.sources]\n", encoding="utf-8")
            config = temporary_path / "refs.toml"
            github_env = temporary_path / "github-env"
            github_env.touch()
            argv = [
                "resolve.py",
                "--project-directory",
                str(project),
                "--output",
                str(config),
                "--github-env",
                str(github_env),
            ]
            with mock.patch.object(resolve.sys, "argv", argv), mock.patch.dict(os.environ, {"PR_BODY": ""}, clear=True):
                self.assertEqual(resolve.main(), 0)
            self.assertFalse(config.exists())
            self.assertEqual(github_env.read_text(encoding="utf-8"), "")

    def test_main_exports_config_for_an_open_declared_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            project = temporary_path / "project"
            project.mkdir()
            (project / "pyproject.toml").write_text(
                '[tool.uv.sources]\ncle = { git = "https://github.com/angr/cle.git", branch = "master" }\n',
                encoding="utf-8",
            )
            config = temporary_path / "refs.toml"
            github_env = temporary_path / "github-env"
            github_env.touch()
            argv = [
                "resolve.py",
                "--project-directory",
                str(project),
                "--output",
                str(config),
                "--github-env",
                str(github_env),
            ]
            with (
                mock.patch.object(resolve.sys, "argv", argv),
                mock.patch.object(resolve, "pull_request_state", return_value="open"),
                mock.patch.dict(os.environ, {"PR_BODY": "sync: angr/cle#795"}, clear=True),
            ):
                self.assertEqual(resolve.main(), 0)
            self.assertEqual(
                github_env.read_text(encoding="utf-8"),
                f"UV_CONFIG_FILE={config}\n",
            )

    def test_main_rejects_an_unsafe_test_api_override_without_querying_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            project = temporary_path / "project"
            project.mkdir()
            (project / "pyproject.toml").write_text(
                '[tool.uv.sources]\ncle = { git = "https://github.com/angr/cle.git", branch = "master" }\n',
                encoding="utf-8",
            )
            config = temporary_path / "refs.toml"
            github_env = temporary_path / "github-env"
            github_env.touch()
            argv = [
                "resolve.py",
                "--project-directory",
                str(project),
                "--output",
                str(config),
                "--github-env",
                str(github_env),
            ]
            with (
                mock.patch.object(resolve.sys, "argv", argv),
                mock.patch.object(resolve.urllib.request, "urlopen") as urlopen,
                mock.patch("sys.stderr", new_callable=io.StringIO) as stderr,
                mock.patch.dict(
                    os.environ,
                    {
                        "PR_BODY": "sync: angr/cle#795",
                        "SIBLING_REFS_TEST_API_URL": "https://example.invalid/api",
                        "GH_TOKEN": "must-not-leave-the-runner",
                    },
                    clear=True,
                ),
            ):
                self.assertEqual(resolve.main(), 2)

            urlopen.assert_not_called()
            self.assertIn("must be a local file: URL", stderr.getvalue())
            self.assertFalse(config.exists())
            self.assertEqual(github_env.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
