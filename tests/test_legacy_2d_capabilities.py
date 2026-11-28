import unittest

from impossible.addons import AddonRegistry


class Generic2DCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = AddonRegistry.load()

    def test_arcade_car_movement_is_separate_from_vehicle_dynamics(self):
        car = self.registry.get("behavior.car-movement")
        vehicle = self.registry.get("behavior.vehicle")
        self.assertEqual(car.kind, "behavior")
        self.assertEqual(vehicle.kind, "behavior")
        self.assertNotEqual(car.id, vehicle.id)
        self.assertEqual(car.raw["object"]["placement"], "object_properties")
        self.assertTrue({"max_speed", "acceleration", "deceleration", "steer_speed",
                         "drift_recover", "friction", "set_angle", "default_controls",
                         "turn_while_stopped", "enabled"} <=
                        {item["name"] for item in car.properties})
        expected = {
            "behavior.car-movement.compare_speed",
            "behavior.car-movement.is_enabled",
            "behavior.car-movement.is_moving",
            "behavior.car-movement.simulate_control",
            "behavior.car-movement.set_speed",
            "behavior.car-movement.set_enabled",
            "behavior.car-movement.stop",
            "behavior.car-movement.vector_x",
            "behavior.car-movement.vector_y",
            "behavior.car-movement.moving_angle",
        }
        for ace_id in expected:
            self.assertIsNotNone(self.registry.find_ace(ace_id), ace_id)

    def test_viewport_anchor_and_bounds_contracts(self):
        anchor = self.registry.get("behavior.anchor")
        bounds = self.registry.get("behavior.bound-to-layout")
        self.assertIsNotNone(self.registry.find_ace("behavior.anchor.is_enabled"))
        self.assertIsNotNone(self.registry.find_ace("behavior.anchor.set_enabled"))
        self.assertIn("left_edge", {p["name"] for p in anchor.properties})
        self.assertIn("bottom_edge", {p["name"] for p in anchor.properties})
        bound_by = next(p for p in bounds.properties if p["name"] == "bound_by")
        self.assertEqual(bound_by["options"], ["edge", "origin"])

    def test_text_to_speech_exposes_voice_selection(self):
        tts = self.registry.get("plugin.text-to-speech")
        speak = next(a for a in tts.actions if a.id == "plugin.text-to-speech.speak")
        self.assertIn("voice_uri", {p["name"] for p in speak.parameters})
        self.assertIn("volume", {p["name"] for p in speak.parameters})
        self.assertIsNotNone(self.registry.find_ace("plugin.text-to-speech.voice_uri_at"))

    def test_user_media_exposes_recognition_and_sensing(self):
        media = self.registry.get("plugin.user-media")
        expected = {
            "plugin.user-media.start_speech_recognition",
            "plugin.user-media.stop_speech_recognition",
            "plugin.user-media.on_speech_result",
            "plugin.user-media.on_speech_recognition_error",
            "plugin.user-media.speech_transcript",
            "plugin.user-media.speech_confidence",
            "plugin.user-media.ambient_light_lux",
        }
        for ace_id in expected:
            self.assertIsNotNone(self.registry.find_ace(ace_id), ace_id)
        category_ids = {item["id"] for item in media.raw["editor"]["ace_categories"]}
        self.assertIn("speech", category_ids)
        self.assertIn("sensing", category_ids)

    def test_banner_ads_have_explicit_placement_controls(self):
        ads = self.registry.get("plugin.advertising")
        expected = {
            "plugin.advertising.on_banner_loaded",
            "plugin.advertising.on_banner_failed",
            "plugin.advertising.show_banner",
            "plugin.advertising.hide_banner",
            "plugin.advertising.set_banner_position",
        }
        for ace_id in expected:
            self.assertIsNotNone(self.registry.find_ace(ace_id), ace_id)

    def test_tiled_background_has_async_uri_loading(self):
        tiled = self.registry.get("plugin.tiled-background")
        load = next(a for a in tiled.actions if a.id == "plugin.tiled-background.load_image_from_url")
        uri = next(p for p in load.parameters if p["name"] == "uri")
        self.assertEqual(uri["type"], "uri")
        self.assertIsNotNone(self.registry.find_ace("plugin.tiled-background.on_image_url_loaded"))
        self.assertIsNotNone(self.registry.find_ace("plugin.tiled-background.image_width"))

    def test_game_services_are_provider_neutral_and_async(self):
        services = self.registry.get("plugin.game-services")
        expected = {
            "plugin.game-services.on_sign_in_succeeded",
            "plugin.game-services.on_sign_in_failed",
            "plugin.game-services.request_achievements",
            "plugin.game-services.unlock_achievement",
            "plugin.game-services.increment_achievement",
            "plugin.game-services.request_leaderboard",
            "plugin.game-services.submit_score",
            "plugin.game-services.leaderboard_rank_at",
            "plugin.game-services.player_display_name",
        }
        for ace_id in expected:
            self.assertIsNotNone(self.registry.find_ace(ace_id), ace_id)
        self.assertIn("host.game_services", services.raw["implementation"]["host_adapter_required"])

    def test_new_contracts_remain_specification_only(self):
        addon_ids = (
            "behavior.car-movement", "plugin.game-services", "plugin.text-to-speech",
            "plugin.user-media", "plugin.advertising", "plugin.tiled-background",
        )
        for addon_id in addon_ids:
            addon = self.registry.get(addon_id)
            self.assertEqual(addon.implementation_status, "specification_only")
            self.assertFalse(addon.engine_runtime)


if __name__ == "__main__":
    unittest.main()
