"""Structural tests for the data-driven GTK ribbon specification."""
import unittest

from impossible.ui.ribbon_spec import BACKSTAGE_ITEMS, QUICK_ACCESS, TABS


class RibbonSpecTests(unittest.TestCase):
    def test_tabs_have_unique_ids_and_groups(self):
        ids = [tab["id"] for tab in TABS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("home", ids)
        self.assertIn("view", ids)
        self.assertIn("events", ids)
        for tab in TABS:
            self.assertTrue(tab["groups"], tab["id"])

    def test_every_ribbon_button_has_an_action_and_icon(self):
        for tab in TABS:
            for group in tab["groups"]:
                for item in group["buttons"]:
                    self.assertTrue(item["label_key"])
                    self.assertTrue(item["icon"])
                    self.assertTrue(item["action"])

    def test_backstage_and_quick_access_are_wired(self):
        self.assertTrue(any(item.get("action") == "open_project" for item in BACKSTAGE_ITEMS))
        self.assertTrue(any(item.get("action") == "save_project" for item in QUICK_ACCESS))


if __name__ == "__main__":
    unittest.main()
