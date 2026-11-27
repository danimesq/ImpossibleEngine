import json
import unittest
from pathlib import Path

from impossible.addons import AddonRegistry, AddonRegistryError


class BuiltinAddonRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = AddonRegistry.load()

    def test_catalog_coverage(self):
        counts = self.registry.counts()
        self.assertGreaterEqual(counts["plugins"], 30)
        self.assertGreaterEqual(counts["behaviors"], 20)
        self.assertGreaterEqual(counts["effects"], 30)
        self.assertGreater(counts["conditions"], 80)
        self.assertGreater(counts["actions"], 100)
        self.assertGreater(counts["expressions"], 50)

    def test_namespaced_ids_and_picker_metadata(self):
        self.assertEqual(self.registry.get("plugin.sprite").kind, "plugin")
        self.assertEqual(self.registry.get("behavior.platform").kind, "behavior")
        self.assertEqual(self.registry.get("effect.crt").kind, "effect")
        self.assertEqual(self.registry.get("plugin.sprite").raw["icon"]["kind"], "builtin")
        self.assertTrue(self.registry.get("plugin.sprite").raw["editor"]["picker"]["icon_visible"])

    def test_trigger_ace_metadata(self):
        found = self.registry.find_ace("plugin.sprite.on_animation_finished")
        self.assertIsNotNone(found)
        addon, ace, section = found
        self.assertEqual(section, "conditions")
        self.assertEqual(ace.execution, "trigger")
        self.assertIn("trigger", ace.ui["markers"])
        self.assertTrue(ace.ui["description"])

    def test_action_and_expression_semantics(self):
        sprite = self.registry.get("plugin.sprite")
        self.assertTrue(all(q.execution == "command" for q in sprite.actions))
        self.assertTrue(all(q.execution == "pure" for q in sprite.expressions))

    def test_all_builtins_are_specification_only(self):
        self.assertTrue(all(not q.engine_runtime for q in self.registry.of_kind("plugin")))
        self.assertTrue(all(not q.engine_runtime for q in self.registry.of_kind("behavior")))
        self.assertTrue(all(q.implementation_status == "specification_only" for q in self.registry.of_kind("effect")))

    def test_search_and_category_filters(self):
        self.assertTrue(any(q.id == "behavior.seek" for q in self.registry.search("steering", kind="behavior")))
        self.assertTrue(self.registry.by_category("input", kind="plugin"))
        self.assertFalse(self.registry.search("not-a-real-addon"))

    def test_duplicate_addon_id_rejected(self):
        raw = json.loads(Path(self.registry.source).read_text(encoding="utf-8"))
        raw["addons"].append(raw["addons"][0])
        with self.assertRaises(AddonRegistryError):
            AddonRegistry(raw)

    def test_duplicate_ace_id_rejected(self):
        raw = json.loads(Path(self.registry.source).read_text(encoding="utf-8"))
        entry = raw["addons"][0]
        entry["actions"].append(dict(entry["conditions"][0]))
        with self.assertRaises(AddonRegistryError):
            AddonRegistry(raw)

    def test_undeclared_ace_category_rejected(self):
        raw = json.loads(Path(self.registry.source).read_text(encoding="utf-8"))
        raw["addons"][0]["editor"]["ace_categories"] = []
        with self.assertRaises(AddonRegistryError):
            AddonRegistry(raw)

    def test_runtime_claim_rejected(self):
        raw = json.loads(Path(self.registry.source).read_text(encoding="utf-8"))
        raw["addons"][0]["implementation"]["engine_runtime"] = True
        with self.assertRaises(AddonRegistryError):
            AddonRegistry(raw)


if __name__ == "__main__":
    unittest.main()
