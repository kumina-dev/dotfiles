import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hypr/.config/hypr/scripts"))

from settings_app import system_info


PCI_OUTPUT = """Slot:\t0000:00:02.0
Class:\tVGA compatible controller [0300]
Vendor:\tIntel Corporation [8086]
Device:\tIntegrated graphics [1234]
Rev:\t01

Slot:\t0000:03:00.0
Device:\tDiscrete graphics [5678]
Vendor:\tExample vendor [abcd]
Class:\t3D controller [0302]

Slot:\t0000:04:00.0
Class:\tAudio device [0403]
Vendor:\tExample vendor [abcd]
Device:\tAudio [9999]
"""


class SystemInfoTests(unittest.TestCase):
    def test_gpu_parser_handles_multiple_devices_and_reordered_tags(self):
        self.assertEqual(system_info.parse_graphics(PCI_OUTPUT),
                         "Intel Corporation [8086] Integrated graphics [1234]\n"
                         "Example vendor [abcd] Discrete graphics [5678]")

    def test_non_gpu_and_malformed_records_are_ignored(self):
        self.assertEqual(system_info.parse_graphics("Class:\tAudio [0403]\n"), "")
        self.assertEqual(system_info.parse_graphics("Not PCI data"), "")

    def test_ram_is_explicitly_usable_memory(self):
        self.assertEqual(system_info.memory_size("MemTotal:  8388608 kB\nMemFree: 1 kB"),
                         "8.0 GiB usable")
        self.assertEqual(system_info.memory_size("MemTotal: invalid kB"), "Unavailable")

    def test_cpu_uses_first_model_and_supports_hardware_fallback(self):
        self.assertEqual(system_info.cpu_model("processor: 0\nmodel name: Test CPU\n"
                                              "processor: 1\nmodel name: Test CPU"), "Test CPU")
        self.assertEqual(system_info.cpu_model("Hardware: Example SoC"), "Example SoC")
        self.assertEqual(system_info.cpu_model(""), "Unavailable")

    def test_storage_permission_failure_is_not_zero_capacity(self):
        with patch.object(system_info.shutil, "disk_usage", side_effect=PermissionError):
            self.assertEqual(system_info.storage("/"), "Unavailable")

    def test_missing_gpu_tool_does_not_prevent_other_information(self):
        with patch.object(system_info.shutil, "which", return_value=None), \
                patch.object(system_info.platform, "freedesktop_os_release",
                             return_value={"PRETTY_NAME": "Arch Linux"}):
            rows = dict(system_info.collect())
        self.assertIn("pciutils", rows["Graphics"])
        self.assertEqual(rows["Operating system"], "Arch Linux")
        self.assertIn("Kernel", rows)
        self.assertIn("System storage (/)", rows)

    def test_gpu_timeout_is_reported_without_raising(self):
        with patch.object(system_info.shutil, "which", return_value="/usr/bin/lspci"), \
                patch.object(system_info, "output", side_effect=system_info.CommandError("timeout")):
            self.assertIn("Unavailable", system_info.graphics())

    def test_version_is_read_from_installed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "VERSION"
            with patch.object(system_info, "VERSION_FILE", path):
                self.assertEqual(system_info.version(), "Development (version unavailable)")
                path.write_text("1.43.0\n")
                self.assertEqual(system_info.version(), "1.43.0")

    def test_copy_report_preserves_all_gpu_names(self):
        self.assertEqual(system_info.format_report([
            ("KumiOS version", "0.1.0-dev"), ("Graphics", "GPU one\nGPU two"),
        ]), "KumiOS version: 0.1.0-dev\nGraphics: GPU one\n  GPU two")


if __name__ == "__main__":
    unittest.main()
