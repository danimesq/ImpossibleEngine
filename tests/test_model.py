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


if __name__ == "__main__":
    unittest.main()
