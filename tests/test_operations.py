import unittest

from impossible.addons import AddonRegistry
from impossible.model import EventSheet, make_demo_project
from impossible.operations import (
    add_event,
    add_event_action,
    add_event_condition,
    add_project_addon,
    find_event,
    remove_event,
    remove_project_addon,
    set_active_platform,
    set_asset_variant,
    set_event_enabled,
    set_object_override,
)


class SharedEditorOperationsTests(unittest.TestCase):
    def setUp(self):
        self.project = make_demo_project()

    def test_add_event_uses_a_unique_stable_id(self):
        first = add_event(self.project, "First")
        second = add_event(self.project, "Second")
        self.assertEqual(first.id, "event-1")
        self.assertEqual(second.id, "event-2")
        self.assertEqual([item.name for item in self.project.event_sheets[0].events][-2:],
                         ["First", "Second"])

    def test_add_event_creates_default_sheet_when_project_is_empty(self):
        project = make_demo_project()
        project.event_sheets.clear()
        event = add_event(project, "Start")
        self.assertEqual(project.event_sheets[0].id, "sheet-main")
        self.assertEqual(project.event_sheets[0].name, "Gameplay")
        self.assertIs(find_event(project, event.id), event)

    def test_event_conditions_actions_enabled_state_and_removal(self):
        event = add_event(self.project, "Player jumps")
        add_event_condition(self.project, event.id, "On jump")
        add_event_action(self.project, event.id, "Apply vertical impulse")
        set_event_enabled(self.project, event.id, False)
        self.assertEqual(event.conditions, ["On jump"])
        self.assertEqual(event.actions, ["Apply vertical impulse"])
        self.assertFalse(event.enabled)
        removed = remove_event(self.project, event.id)
        self.assertIs(removed, event)
        with self.assertRaises(KeyError):
            find_event(self.project, event.id)

    def test_event_operations_reject_empty_expressions(self):
        event = add_event(self.project, "An event")
        with self.assertRaises(ValueError):
            add_event_condition(self.project, event.id, "  ")
        with self.assertRaises(ValueError):
            add_event_action(self.project, event.id, "")

    def test_platform_asset_and_object_edits(self):
        set_active_platform(self.project, "gba")
        self.assertEqual(self.project.active_platform, "gba")

        set_asset_variant(self.project, "asset-hero-sprite", "gba", "assets/custom/player.png")
        asset = next(item for item in self.project.assets if item.id == "asset-hero-sprite")
        self.assertEqual(asset.variants["gba"], "assets/custom/player.png")
        set_asset_variant(self.project, asset.id, "gba", None)
        self.assertNotIn("gba", asset.variants)

        set_object_override(self.project, "object-hero-3d", "ps1", {"scale": 0.75})
        obj = next(item for item in self.project.objects if item.id == "object-hero-3d")
        self.assertEqual(obj.platform_overrides["ps1"], {"scale": 0.75})
        set_object_override(self.project, obj.id, "ps1", {})
        self.assertNotIn("ps1", obj.platform_overrides)

    def test_invalid_platform_and_resource_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            set_active_platform(self.project, "not-a-platform")
        with self.assertRaises(KeyError):
            set_asset_variant(self.project, "missing", "pc-modern", "missing.png")
        with self.assertRaises(KeyError):
            set_object_override(self.project, "missing", "pc-modern", {})

    def test_add_on_selection_is_idempotent_and_round_trips(self):
        registry = AddonRegistry.load()
        addon = next(item for item in registry._addons.values() if not item.requires)
        added = add_project_addon(self.project, addon.id, registry)
        self.assertEqual(added, [addon.id])
        self.assertEqual(add_project_addon(self.project, addon.id, registry), [])
        self.assertEqual(self.project.used_addons[0]["id"], addon.id)

        serialized = self.project.to_dict()
        self.assertIn("usedAddons", serialized)
        self.assertNotIn("used_addons", serialized)
        restored = type(self.project).from_dict(serialized)
        self.assertEqual(restored.used_addons, self.project.used_addons)

        self.assertTrue(remove_project_addon(restored, addon.id, registry))
        self.assertFalse(remove_project_addon(restored, addon.id, registry))
        self.assertEqual(restored.used_addons, [])


if __name__ == "__main__":
    unittest.main()
