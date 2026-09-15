"""Regressions for native toolbar loss caused by an equal-version XML fragment."""

from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install import ACTION, install_shortcut


class ShortcutConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        self.target = self.home / ".local/share/kxmlgui5/dolphin/dolphinui.rc"
        self.target.parent.mkdir(parents=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_new_fragment_cannot_override_native_document_version(self):
        install_shortcut(self.home, 49)
        root = ET.parse(self.target).getroot()
        self.assertEqual(root.get("version"), "0")
        self.assertLess(int(root.get("version")), 48)  # Oldest supported native UI.
        self.assertIsNone(root.find("ToolBar"))  # KDE retains its own toolbar.
        self.assertEqual(root.find("ActionProperties/Action").get("shortcut"), "Ctrl+Alt+P")

    def test_existing_bad_fragment_is_repaired_and_other_shortcuts_survive(self):
        original = '<gui name="dolphin" version="49"><ActionProperties><Action name="custom" shortcut="Ctrl+Alt+J" /></ActionProperties></gui>'
        self.target.write_text(original)
        install_shortcut(self.home, 49)
        root = ET.parse(self.target).getroot()
        self.assertEqual(root.get("version"), "0")
        self.assertEqual(root.find('ActionProperties/Action[@name="custom"]').get("shortcut"), "Ctrl+Alt+J")
        self.assertEqual(self.target.with_name("dolphinui.rc.pre-aven").read_text(), original)

    def test_complete_native_ui_is_preserved(self):
        toolbar = '<ToolBar name="mainToolBar" noMerge="1"><Action name="go_back"/><Action name="go_forward"/><Action name="view_settings"/><Action name="url_navigators"/><Action name="split_view"/><Action name="toggle_search"/><Action name="hamburger_menu"/></ToolBar>'
        self.target.write_text(f'<gui name="dolphin" version="49"><MenuBar><Menu name="file"><Action name="new_menu"/></Menu></MenuBar>{toolbar}<ActionProperties><Action name="go_back" priority="0"/></ActionProperties></gui>')
        before = ET.parse(self.target).getroot()
        toolbar_before = [(node.tag, dict(node.attrib)) for node in before.find("ToolBar").iter()]
        install_shortcut(self.home, 49)
        after = ET.parse(self.target).getroot()
        self.assertEqual(after.get("version"), "49")
        self.assertEqual([(node.tag, dict(node.attrib)) for node in after.find("ToolBar").iter()], toolbar_before)
        self.assertIsNotNone(after.find('MenuBar/Menu/Action[@name="new_menu"]'))
        self.assertEqual(after.find('ActionProperties/Action[@name="go_back"]').get("priority"), "0")

    def test_reinstallation_does_not_duplicate_action(self):
        install_shortcut(self.home, 49)
        install_shortcut(self.home, 49)
        actions = ET.parse(self.target).findall("ActionProperties/Action")
        self.assertEqual(sum(action.get("name") == ACTION for action in actions), 1)


if __name__ == "__main__":
    unittest.main()
