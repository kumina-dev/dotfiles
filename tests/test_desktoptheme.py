"""The KumiOS Plasma style must follow the active color scheme (KUM-20).

A fixed palette would ignore light/dark mode and the wallpaper accent, so the
theme ships no `colors` file and its panel SVG draws with Plasma's color-scheme
stylesheet class instead of hardcoded fills.
"""

import json
import pathlib
import unittest
import xml.etree.ElementTree as ET

THEME = pathlib.Path(__file__).resolve().parents[1] / "plasma" / "desktoptheme" / "KumiOS"
PANEL = THEME / "widgets" / "panel-background.svg"
SVG = "{http://www.w3.org/2000/svg}"

# Element ids Plasma's frame renderer looks up for the generic, top-bar (north),
# dock (south) and floating panel backgrounds.
FRAME_PARTS = ("center", "top", "bottom", "left", "right",
               "topleft", "topright", "bottomleft", "bottomright")
REQUIRED_IDS = (
    set(FRAME_PARTS)
    | {f"north-{part}" for part in FRAME_PARTS}
    | {f"south-{part}" for part in FRAME_PARTS}
    | {"floating-center"}
    | {f"{prefix}hint-{side}-margin" for prefix in ("", "floating-")
       for side in ("top", "bottom", "left", "right")}
)


class DesktopThemeTest(unittest.TestCase):
    def setUp(self):
        self.root = ET.parse(PANEL).getroot()
        self.elements = {el.get("id"): el for el in self.root.iter() if el.get("id")}

    def test_theme_has_no_fixed_palette(self):
        self.assertFalse((THEME / "colors").exists(),
                         "a colors file overrides the system color scheme and accent")

    def test_panel_uses_color_scheme_stylesheet(self):
        style = self.elements.get("current-color-scheme")
        self.assertIsNotNone(style, "Plasma substitutes colors into this stylesheet")
        self.assertEqual(style.tag, f"{SVG}style")
        self.assertIn(".ColorScheme-Background", style.text)

    def test_visible_parts_draw_with_scheme_background(self):
        visible = [el for el in self.elements.values()
                   if el.tag in (f"{SVG}rect", f"{SVG}path") and el.get("opacity") != "0"]
        self.assertTrue(visible)
        for el in visible:
            with self.subTest(id=el.get("id")):
                self.assertIsNone(el.get("fill"), "fixed fill ignores the color scheme")
                self.assertEqual(el.get("class"), "ColorScheme-Background")
                self.assertEqual(el.get("style"), "fill:currentColor")
                self.assertIsNotNone(el.get("fill-opacity"), "panel translucency kept")

    def test_required_frame_elements_present(self):
        self.assertEqual(REQUIRED_IDS - self.elements.keys(), set())

    def test_metadata_version(self):
        metadata = json.loads((THEME / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], "KumiOS")
        self.assertEqual(metadata["KPlugin"]["Version"], "0.3.0")


if __name__ == "__main__":
    unittest.main()
