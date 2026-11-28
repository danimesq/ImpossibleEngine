import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from impossible.addons import AddonRegistry
from impossible.cli import main
from impossible.storage import load_project


class HeadlessCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.project_path = str(Path(self.tempdir.name) / "headless.ieproj")

    def run_cli(self, *arguments):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = main(list(arguments))
        return result, output.getvalue(), errors.getvalue()

    def test_cli_import_does_not_import_gtk(self):
        self.assertNotIn("gi", sys.modules)

    def test_create_and_edit_project_without_gui(self):
        code, output, errors = self.run_cli(
            "project", "create", "--path", self.project_path,
            "--name", "Headless Project", "--format", "json",
        )
        self.assertEqual(code, 0, errors)
        self.assertTrue(json.loads(output)["created"])

        code, output, errors = self.run_cli(
            "events", "add", "--project", self.project_path,
            "--name", "Player jumps", "--format", "json",
        )
        self.assertEqual(code, 0, errors)
        event_id = json.loads(output)["event"]["id"]

        code, output, errors = self.run_cli(
            "events", "condition", "add", "--project", self.project_path,
            "--event-id", event_id, "--text", "On jump", "--format", "json",
        )
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output)["conditions"], ["On jump"])

        code, output, errors = self.run_cli(
            "events", "action", "add", "--project", self.project_path,
            "--event-id", event_id, "--text", "Apply impulse", "--format", "json",
        )
        self.assertEqual(code, 0, errors)
        project = load_project(self.project_path)
        event = project.event_sheets[0].events[0]
        self.assertEqual(event.actions, ["Apply impulse"])

    def test_addon_list_emits_machine_readable_catalogue(self):
        code, output, errors = self.run_cli(
            "addons", "list", "--kind", "behavior", "--format", "json",
        )
        self.assertEqual(code, 0, errors)
        result = json.loads(output)
        self.assertGreater(result["count"], 0)
        self.assertTrue(all(item["kind"] == "behavior" for item in result["addons"]))

    def test_addon_add_and_remove_records_project_dependency(self):
        registry = AddonRegistry.load()
        addon = next(item for item in registry._addons.values() if not item.requires)
        self.run_cli(
            "project", "create", "--path", self.project_path,
            "--name", "Add-on Test", "--format", "json",
        )
        code, output, errors = self.run_cli(
            "addons", "add", addon.id, "--project", self.project_path,
        )
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output)["added"], [addon.id])
        self.assertEqual(load_project(self.project_path).used_addons[0]["id"], addon.id)

        code, output, errors = self.run_cli(
            "addons", "remove", addon.id, "--project", self.project_path,
        )
        self.assertEqual(code, 0, errors)
        self.assertTrue(json.loads(output)["removed"])
        self.assertEqual(load_project(self.project_path).used_addons, [])


if __name__ == "__main__":
    unittest.main()
