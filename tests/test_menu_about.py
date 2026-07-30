import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
import warnings


ROOT = Path(__file__).resolve().parents[1]


def parse_module(filename):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse((ROOT / filename).read_text(encoding="utf-8"))


def function_node(module, name):
    return next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def callback_buttons(function):
    return {
        (call.args[0].value, keyword.value.value)
        for call in ast.walk(function)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "InlineKeyboardButton"
        and call.args
        and isinstance(call.args[0], ast.Constant)
        for keyword in call.keywords
        if keyword.arg == "callback_data"
        and isinstance(keyword.value, ast.Constant)
    }


def callback_handler_patterns(module):
    handlers = {}
    for call in ast.walk(module):
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "CallbackQueryHandler"
            and call.args
            and isinstance(call.args[0], ast.Name)
        ):
            patterns = [
                keyword.value.value
                for keyword in call.keywords
                if keyword.arg == "pattern"
                and isinstance(keyword.value, ast.Constant)
            ]
            handlers[call.args[0].id] = patterns
    return handlers


def metadata_values(version=None):
    environment = os.environ.copy()
    if version is None:
        environment.pop("GAME_VERSION", None)
    else:
        environment["GAME_VERSION"] = version
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, game_metadata; "
                "print(json.dumps({"
                "'version': game_metadata.GAME_VERSION, "
                "'about': game_metadata.ABOUT_TEXT"
                "}))"
            ),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class MenuAboutTests(unittest.TestCase):
    def test_main_menu_exposes_plot_and_about_actions(self):
        menu = function_node(parse_module("keyboards.py"), "menu_keyboard")

        self.assertIn(("Plot", "plot"), callback_buttons(menu))
        self.assertIn(("About", "about"), callback_buttons(menu))
        self.assertNotIn(("Info", "info"), callback_buttons(menu))

    def test_plot_callback_handler_is_registered(self):
        handlers = callback_handler_patterns(parse_module("trek.py"))

        self.assertIn("plot", handlers)
        self.assertTrue(
            any(re.fullmatch(pattern, "plot") for pattern in handlers["plot"])
        )

    def test_about_callback_handler_is_registered(self):
        handlers = callback_handler_patterns(parse_module("trek.py"))

        self.assertIn("about", handlers)
        self.assertTrue(
            any(re.fullmatch(pattern, "about") for pattern in handlers["about"])
        )

    def test_about_text_uses_centralized_version_author_and_repository_metadata(self):
        trek = parse_module("trek.py")
        about = function_node(trek, "about")
        metadata = metadata_values("v9.8.7")
        imports = {
            alias.name
            for node in trek.body
            if isinstance(node, ast.ImportFrom) and node.module == "game_metadata"
            for alias in node.names
        }

        self.assertIn("ABOUT_TEXT", imports)
        self.assertTrue(
            any(
                isinstance(node, ast.Name) and node.id == "ABOUT_TEXT"
                for node in ast.walk(about)
            )
        )
        self.assertEqual(metadata["version"], "v9.8.7")
        self.assertIn("Version: v9.8.7", metadata["about"])
        self.assertIn("Author: Simon Borin (@blooomberg)", metadata["about"])
        self.assertIn(
            "GitHub: https://github.com/SimonBorin/trek_bot",
            metadata["about"],
        )

    def test_about_displays_same_v_prefixed_release_tag_from_environment(self):
        metadata = metadata_values("v1.2.3")

        self.assertEqual(metadata["version"], "v1.2.3")
        self.assertIn("Version: v1.2.3", metadata["about"])

    def test_game_metadata_has_no_hardcoded_0_1_0_version(self):
        metadata_source = (ROOT / "game_metadata.py").read_text(encoding="utf-8")

        self.assertNotIn('"0.1.0"', metadata_source)
        self.assertNotIn("'0.1.0'", metadata_source)

    def test_game_metadata_derives_next_repository_version(self):
        self.assertEqual(metadata_values()["version"], "v0.1.3")
