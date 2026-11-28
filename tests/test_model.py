import unittest

from impossible.model import Project, make_demo_project


class PlatformVariantTests(unittest.TestCase):
    def setUp(self):
        self.project = make_demo_project()

    def test_3d_mesh_has_pc_ps1_and_n64_variants(self):
        mesh = next(asset for asset in self.project.assets if asset.id == "asset-hero-mesh")
        self.assertEqual(mesh.source_for("pc-modern"), "assets/hero/hero-high.glb")
        self.assertEqual(mesh.source_for("ps1"), "assets/hero/hero-ps1.obj")
        self.assertEqual(mesh.source_for("n64"), "assets/hero/hero-n64.obj")

    def test_2d_sprite_has_mobile_gba_and_gbc_variants(self):
        sprite = next(asset for asset in self.project.assets if asset.id == "asset-hero-sprite")
        self.assertEqual(sprite.source_for("mobile-modern"), "assets/hero/hero-mobile.png")
        self.assertEqual(sprite.source_for("gba"), "assets/hero/hero-gba.png")
        self.assertEqual(sprite.source_for("gbc"), "assets/hero/hero-gbc.png")

    def test_browser_wasm_is_a_first_class_profile(self):
        from impossible.model import PROFILE_BY_ID
        web = PROFILE_BY_ID["web-wasm"]
        self.assertEqual(web.dimension, "2D + 3D")
        self.assertEqual(web.renderer, "Canvas 2D / WebGL 2")

    def test_missing_variant_falls_back_to_base_source(self):
        sprite = next(asset for asset in self.project.assets if asset.id == "asset-hero-sprite")
        self.assertEqual(sprite.source_for("ps1"), sprite.source)

    def test_object_variant_merges_over_base_properties(self):
        hero = next(obj for obj in self.project.objects if obj.id == "object-hero-3d")
        properties = hero.properties_for("ps1")
        self.assertEqual(properties["scale"], 0.92)
        self.assertFalse(properties["shadow"])
        self.assertEqual(properties["collision"], "box")

    def test_project_round_trip(self):
        restored = Project.from_dict(self.project.to_dict())
        self.assertEqual(restored.name, self.project.name)
        self.assertEqual(len(restored.event_sheets[0].events), 3)

    def test_unknown_project_fields_survive_round_trip(self):
        original = {
            "name": "Forward-compatible Project",
            "format": "impossible-engine-project",
            "projectFormatVersion": 1,
            "futureEditorMetadata": {"keep": True, "revision": 7},
            "usedAddons": [{"type": "plugin", "id": "plugin.sprite"}],
        }
        restored = Project.from_dict(original)
        serialized = restored.to_dict()
        self.assertEqual(serialized["format"], original["format"])
        self.assertEqual(serialized["projectFormatVersion"], 1)
        self.assertEqual(serialized["futureEditorMetadata"], {"keep": True, "revision": 7})
        self.assertEqual(serialized["usedAddons"], original["usedAddons"])
        self.assertNotIn("extra_fields", serialized)


    def test_native_project_format_version_is_validated(self):
        with self.assertRaisesRegex(ValueError, "Unsupported native project format version"):
            Project.from_dict({
                "format": "impossible-engine-project",
                "projectFormatVersion": 99,
                "name": "Future Project",
                "usedAddons": [],
            })

    def test_used_addons_must_be_an_array_of_objects(self):
        with self.assertRaisesRegex(ValueError, "usedAddons must be an array"):
            Project.from_dict({"name": "Invalid", "usedAddons": ["plugin.sprite"]})

if __name__ == "__main__":
    unittest.main()
