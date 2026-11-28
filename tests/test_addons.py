import json
import tempfile
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

    def test_legacy_plugin_surface_is_catalogued(self):
        expected = {
            "plugin.http", "plugin.advanced-text-input", "plugin.audio",
            "plugin.browser", "plugin.haptics", "plugin.button-control",
            "plugin.websocket", "plugin.time-manager", "plugin.css-styles",
            "plugin.clock", "plugin.function", "plugin.embedded-frame",
            "plugin.keyboard", "plugin.mouse", "plugin.svg-canvas",
            "plugin.sprite", "plugin.text", "plugin.text-input",
            "plugin.tiled-background", "plugin.touch", "plugin.storage",
            "plugin.xml", "plugin.layout-transition", "plugin.progress-bar",
            "plugin.slider", "plugin.video",
        }
        for addon_id in expected:
            self.assertEqual(self.registry.get(addon_id).kind, "plugin")

    def test_legacy_ace_coverage_is_declared(self):
        expected = {
            "plugin.http.on_completed",
            "plugin.http.request_url",
            "plugin.audio.play_at_object",
            "plugin.audio.set_listener_object",
            "plugin.audio.stop_all",
            "plugin.storage.compare_key_text",
            "plugin.xml.string_value_legacy",
            "plugin.function.call_expression",
            "plugin.function.parameter_count",
            "plugin.layout-transition.entrance_transition",
            "plugin.layout-transition.is_transition_ended",
            "plugin.progress-bar.set_progress",
            "plugin.slider.set_value",
            "plugin.text-input.on_text_changed",
            "plugin.embedded-frame.set_url",
            "plugin.svg-canvas.set_svg",
            "plugin.time-manager.get_time_value",
        }
        for ace_id in expected:
            self.assertIsNotNone(self.registry.find_ace(ace_id), ace_id)

    def test_legacy_behavior_and_effect_coverage_is_declared(self):
        self.assertEqual(self.registry.get("behavior.persist").kind, "behavior")
        self.assertIsNotNone(self.registry.find_ace("behavior.solid.is_enabled"))
        self.assertIsNotNone(self.registry.find_ace("behavior.solid.set_enabled"))
        self.assertIsNotNone(self.registry.find_ace("behavior.pin.is_pinned"))
        self.assertIsNotNone(self.registry.find_ace("behavior.platform.set_max_speed"))
        self.assertIsNotNone(self.registry.find_ace("behavior.eight-direction.reverse"))
        self.assertEqual(self.registry.get("effect.swirl").kind, "effect")

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

    def test_behavior_expression_return_types_are_typed(self):
        self.assertEqual(self.registry.find_ace("behavior.platform.grounded")[1].returns, "boolean")
        self.assertEqual(self.registry.find_ace("behavior.seek.desired_velocity")[1].returns, "vector2")
        self.assertEqual(self.registry.find_ace("behavior.grid-movement.cell_x")[1].returns, "integer")

    def test_debug_draw_duration_has_numeric_default(self):
        found = self.registry.find_ace("plugin.debug.draw_shape")
        duration = next(item for item in found[1].parameters if item["name"] == "duration")
        self.assertEqual(duration["type"], "number")
        self.assertFalse(duration["required"])
        self.assertEqual(duration["default"], 0)

    def test_picker_categories_have_human_labels(self):
        self.assertEqual(self.registry.get("plugin.array").raw["editor"]["picker"]["category_label"], "Data and Storage")
        self.assertEqual(self.registry.get("behavior.platform").raw["editor"]["picker"]["category_label"], "Movements")
        self.assertEqual(self.registry.get("effect.normal-map-lighting").raw["editor"]["picker"]["category_label"], "Normal Mapping")

    def test_behavior_and_effect_placement_are_distinct(self):
        self.assertEqual(self.registry.get("behavior.platform").raw["object"]["placement"], "object_properties")
        self.assertEqual(self.registry.get("effect.crt").raw["object"]["placement"], "effects_stack")

    def test_all_builtins_are_specification_only(self):
        self.assertTrue(all(not q.engine_runtime for q in self.registry.of_kind("plugin")))
        self.assertTrue(all(not q.engine_runtime for q in self.registry.of_kind("behavior")))
        self.assertTrue(all(q.implementation_status == "specification_only" for q in self.registry.of_kind("effect")))

    def test_search_and_category_filters(self):
        self.assertTrue(any(q.id == "behavior.seek" for q in self.registry.search("steering", kind="behavior")))
        self.assertTrue(self.registry.by_category("input", kind="plugin"))
        self.assertFalse(self.registry.search("not-a-real-addon"))


    def _external_addon(self, addon_id="plugin.example-vendor-demo"):
        addon = json.loads(json.dumps(self.registry.get("plugin.sprite").raw))
        addon["id"] = addon_id
        addon["name"] = "Vendor Demo"
        addon["description"] = "Third-party metadata fixture."
        addon["author"] = "Example Vendor"
        addon["documentation"] = "README.md"
        addon["provides"] = [addon_id]
        addon["requires"] = []
        for section in ("conditions", "actions", "expressions"):
            for ace in addon[section]:
                suffix = ace["id"].split("plugin.sprite.", 1)[-1]
                ace["id"] = f"{addon_id}.{suffix}"
                ace["ui"]["language_key"] = f"ace.{addon_id}.{suffix}"
        return addon

    def test_c2_timer_and_pathfinding_are_object_behaviors_only(self):
        self.assertEqual(self.registry.get("behavior.timer").kind, "behavior")
        self.assertEqual(self.registry.get("behavior.pathfinding").kind, "behavior")
        self.assertNotIn("plugin.timer", self.registry.ids())
        self.assertNotIn("plugin.pathfinding", self.registry.ids())

    def test_c2_missing_behaviors_are_catalogued(self):
        for addon_id in (
            "behavior.timer", "behavior.pathfinding", "behavior.jump-thru",
            "behavior.no-save", "behavior.shadow-caster",
        ):
            self.assertEqual(self.registry.get(addon_id).kind, "behavior")

    def test_system_and_common_object_are_not_insertable_picker_items(self):
        self.assertFalse(self.registry.get("plugin.system").raw["editor"]["picker"]["visible"])
        self.assertFalse(self.registry.get("plugin.object").raw["editor"]["picker"]["visible"])

    def test_blend_mode_is_common_property_not_visible_shader_effect(self):
        effect = self.registry.get("effect.blend-mode")
        self.assertTrue(effect.raw["isDeprecated"])
        self.assertFalse(effect.raw["editor"]["picker"]["visible"])
        self.assertTrue(any(p["name"] == "blend_mode" for p in self.registry.get("plugin.object").properties))
        self.assertIsNotNone(self.registry.find_ace("plugin.object.set_blend_mode"))

    def test_c2_condition_flags_include_fake_trigger_and_static(self):
        ace = self.registry.find_ace("plugin.sprite.on_animation_finished")[1]
        self.assertIn("fake_trigger", ace.ui["flags"])
        self.assertIn("static", ace.ui["flags"])

    def test_audio_dsp_chain_is_separate_from_visual_effects(self):
        audio = self.registry.get("plugin.audio").raw["audioProcessing"]
        self.assertEqual(audio["scope"], "per_tag_ordered_chain")
        self.assertIn("analyser", audio["operations"])
        self.assertIn("set_effect_wet_dry", audio["controls"])

    def test_loads_third_party_addon_from_drop_in_directory_without_executing_code(self):
        with tempfile.TemporaryDirectory() as temp:
            package_dir = Path(temp) / "example-vendor" / "demo"
            package_dir.mkdir(parents=True)
            marker = package_dir / "executed.txt"
            (package_dir / "runtime.js").write_text(
                "This entrypoint must not be evaluated by the metadata loader.",
                encoding="utf-8",
            )
            manifest = {
                "format": "impossible.addon-package",
                "manifestVersion": 1,
                "addon": self._external_addon(),
                "package": {
                    "entrypoints": {"runtime": "runtime.js"},
                    "permissions": ["audio.output"],
                },
            }
            (package_dir / "addon.json").write_text(json.dumps(manifest), encoding="utf-8")
            registry = AddonRegistry.load(third_party_dir=temp)
            self.assertEqual(registry.get("plugin.example-vendor-demo").name, "Vendor Demo")
            self.assertEqual(registry.origin("plugin.example-vendor-demo"), "third-party:example-vendor/demo")
            self.assertFalse(marker.exists())

    def test_invalid_third_party_package_is_skipped_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            package_dir = Path(temp) / "broken"
            package_dir.mkdir()
            (package_dir / "addon.json").write_text("{ not json", encoding="utf-8")
            registry = AddonRegistry.load(third_party_dir=temp)
            self.assertIsNotNone(registry.get("plugin.sprite"))
            self.assertTrue(any("Skipped" in message for message in registry.diagnostics))

    def test_third_party_entrypoint_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            package_dir = Path(temp) / "vendor" / "bad"
            package_dir.mkdir(parents=True)
            manifest = {
                "format": "impossible.addon-package",
                "manifestVersion": 1,
                "addon": self._external_addon(),
                "package": {"entrypoints": {"runtime": "../../outside.js"}},
            }
            (package_dir / "addon.json").write_text(json.dumps(manifest), encoding="utf-8")
            registry = AddonRegistry.load(third_party_dir=temp)
            self.assertNotIn("plugin.example-vendor-demo", registry.ids())
            self.assertTrue(any("Unsafe entrypoint" in message for message in registry.diagnostics))

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
