import json
import unittest
from pathlib import Path

from impossible.compiler import (
    HANDLER_BY_SID,
    ProjectCompileError,
    generate_source_bindings,
    validate_project,
)
from impossible.storage import load_project

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "projects" / "flappy-ramon" / "Flappy-Madruga.ieproj"


class FlappyMadrugaImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = validate_project(PROJECT_FILE)

    def test_source_revision_and_project_identity_are_pinned(self):
        self.assertEqual(self.report["project"], "Flappy Madruga")
        self.assertEqual(
            self.report["source_revision"],
            "aab10559cea2d1283eafa2a8792aaf877cbffcf5",
        )
        self.assertEqual(self.report["source_project_version"], "0.6.1.6")

    def test_all_layouts_and_event_sheets_are_present_in_source_order(self):
        self.assertEqual(self.report["layouts"], ["Start", "Continuous", "Chaves"])
        sheets = {item["name"]: item for item in self.report["event_sheets"]}
        self.assertEqual(
            list(sheets),
            ["Start events", "Continuous events", "Common in-game", "Common in-levels", "Chaves"],
        )
        self.assertEqual(sheets["Start events"]["event_count"], 5)
        self.assertEqual(sheets["Continuous events"]["includes"], ["Common in-game"])
        self.assertEqual(sheets["Common in-game"]["event_count"], 25)
        self.assertEqual(sheets["Common in-game"]["groups"],
                         ["Start", "Movement", "Collisions", "Scoring", "Background", "Obstacle"])
        self.assertEqual(sheets["Chaves"]["includes"],
                         ["Common in-game", "Common in-levels"])

    def test_every_source_event_has_one_typed_rust_binding(self):
        self.assertEqual(self.report["source_events"], 32)
        self.assertEqual(self.report["handler_bindings"], 32)
        self.assertEqual(len(HANDLER_BY_SID), 32)
        self.assertEqual(sum(self.report["status_counts"].values()), 32)

    def test_native_project_opens_with_source_provenance(self):
        project = load_project(PROJECT_FILE)
        self.assertEqual(project.name, "Flappy Madruga")
        self.assertEqual(len(project.objects), 10)
        self.assertEqual(len(project.assets), 10)
        self.assertEqual([sheet.name for sheet in project.event_sheets],
                         ["Start events", "Continuous events", "Common in-game",
                          "Common in-levels", "Chaves"])
        common = next(sheet for sheet in project.event_sheets if sheet.name == "Common in-game")
        self.assertEqual(common.groups,
                         ["Start", "Movement", "Collisions", "Scoring", "Background", "Obstacle"])
        self.assertEqual(common.events[0].source_id, "2246972820014324")
        self.assertEqual(common.events[0].group, "Start")
        self.assertEqual(project.metadata["upstream"]["revision"],
                         "aab10559cea2d1283eafa2a8792aaf877cbffcf5")

    def test_codegen_matches_checked_in_compiled_bindings(self):
        generated = generate_source_bindings(PROJECT_FILE)
        content = generated.read_text(encoding="utf-8")
        self.assertIn("pub const SOURCE_EVENT_COUNT: usize = 32;", content)
        self.assertIn("SourceEventHandler::MoveBackgroundAndPipes", content)
        self.assertIn("SourceEventHandler::ChavesLayoutStart", content)
        self.assertIn("SourceGroup::CommonInLevels", content)

    def test_graphics_target_is_explicitly_deferred(self):
        from impossible.compiler import compile_project

        with self.assertRaises(ProjectCompileError):
            compile_project(PROJECT_FILE, target="graphics")


if __name__ == "__main__":
    unittest.main()
