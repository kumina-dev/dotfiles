import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hypr/.config/hypr/scripts"))

from control_center import audio


def node(node_id, name, media_class, serial=None):
    return {
        "id": node_id,
        "type": "PipeWire:Interface:Node",
        "info": {"props": {
            "object.serial": serial if serial is not None else node_id + 100,
            "node.name": name,
            "node.description": name.replace("_", " "),
            "media.class": media_class,
        }},
    }


def snapshot():
    return [
        node(41, "Speakers", "Audio/Sink"),
        node(42, "USB_Headphones", "Audio/Sink"),
        node(43, "USB_Microphone", "Audio/Source"),
        node(44, "Music_player", "Stream/Output/Audio"),
        {
            "type": "PipeWire:Interface:Metadata",
            "props": {"metadata.name": "default"},
            "metadata": [
                {"subject": 0, "key": "default.audio.sink",
                 "value": {"name": "USB_Headphones"}},
                {"subject": 0, "key": "default.audio.source",
                 "value": '{"name": "USB_Microphone"}'},
                {"subject": 0, "key": "default.configured.audio.sink",
                 "value": {"name": "Disconnected_headset"}},
            ],
        },
    ]


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.objects = snapshot()
        self.commands = []
        self.volume_errors = {}
        self.volumes = {"41": "Volume: 0.20", "42": "Volume: 0.65",
                        "43": "Volume: 0.40 [MUTED]"}
        self.patcher = patch.object(audio, "_command", side_effect=self.command)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def command(self, *args):
        self.commands.append(args)
        if args[0] == "pw-dump":
            return json.dumps(self.objects)
        if args[1] == "get-volume":
            if args[2] in self.volume_errors:
                raise audio.AudioError(self.volume_errors[args[2]])
            return self.volumes[args[2]]
        return ""

    def test_discovery_uses_actual_defaults_and_excludes_application_streams(self):
        state = audio.get_state()
        self.assertEqual([device.id for device in state["output"]["devices"]], [41, 42])
        self.assertEqual(state["output"]["device"].id, 42)
        self.assertEqual(state["input"]["device"].id, 43)
        self.assertEqual(state["output"]["volume"], 65)
        self.assertTrue(state["input"]["muted"])
        self.assertFalse(any(args[1].startswith("set-") for args in self.commands))

    def test_no_device_is_not_reported_as_zero_volume(self):
        self.objects = []
        for endpoint in audio.get_state().values():
            self.assertIsNone(endpoint["device"])
            self.assertIsNone(endpoint["volume"])
            self.assertEqual(endpoint["devices"], [])

    def test_missing_default_does_not_silently_select_first_device(self):
        self.objects[-1]["metadata"] = []
        state = audio.get_state()
        self.assertIsNone(state["output"]["device"])
        self.assertEqual(len(state["output"]["devices"]), 2)
        self.assertEqual(len(self.commands), 1)

    def test_input_failure_does_not_disable_output(self):
        self.volume_errors["43"] = "Microphone disconnected"
        state = audio.get_state()
        self.assertEqual(state["output"]["volume"], 65)
        self.assertIsNone(state["input"]["volume"])
        self.assertEqual(state["input"]["error"], "Microphone disconnected")

    def test_external_amplification_is_read_without_writing(self):
        self.volumes["42"] = "Volume: 1.35"
        self.assertEqual(audio.get_state()["output"]["volume"], 135)
        self.assertFalse(any(args[1].startswith("set-") for args in self.commands))

    def test_queued_write_keeps_its_device_after_default_changes(self):
        device = audio.get_state()["output"]["device"]
        self.objects[-1]["metadata"][0]["value"] = {"name": "Speakers"}
        audio.set_volume(device, 37)
        self.assertEqual(self.commands[-1],
                         ("wpctl", "set-volume", "--limit", "1.0", "42", "37%"))

    def test_recycled_id_cannot_receive_a_queued_write(self):
        device = audio.get_state()["output"]["device"]
        self.objects[1] = node(42, "USB_Headphones", "Audio/Sink", serial=999)
        self.commands.clear()
        with self.assertRaisesRegex(audio.AudioError, "disconnected"):
            audio.set_mute(device, True)
        self.assertFalse(any(args[0] == "wpctl" for args in self.commands))

    def test_removed_device_cannot_be_selected(self):
        device = audio.get_state()["input"]["device"]
        self.objects = [item for item in self.objects if item.get("id") != device.id]
        with self.assertRaisesRegex(audio.AudioError, "disconnected"):
            audio.set_default(device)

    def test_user_volume_is_limited_and_does_not_unmute(self):
        device = audio.get_state()["input"]["device"]
        self.commands.clear()
        audio.set_volume(device, 140)
        self.assertEqual(self.commands[-1][-1], "100%")
        self.assertFalse(any(args[1] == "set-mute" for args in self.commands))
        audio.set_volume(device, -20)
        self.assertEqual(self.commands[-1][-1], "0%")

    def test_failed_volume_parse_is_explicit(self):
        self.volumes["42"] = "Unexpected output"
        state = audio.get_state()["output"]
        self.assertIsNone(state["volume"])
        self.assertIsNotNone(state["error"])


class CommandTests(unittest.TestCase):
    def test_missing_tools_and_timeouts_have_actionable_errors(self):
        for error, message in ((FileNotFoundError(), "Install pipewire"),
                               (subprocess.TimeoutExpired("pw-dump", 4), "did not respond")):
            with self.subTest(error=error), patch.object(audio.subprocess, "run", side_effect=error):
                with self.assertRaisesRegex(audio.AudioError, message):
                    audio.get_state()

    def test_command_failure_does_not_return_fake_state(self):
        result = subprocess.CompletedProcess([], 2, "", "Connection refused")
        with patch.object(audio.subprocess, "run", return_value=result) as run:
            with self.assertRaisesRegex(audio.AudioError, "Connection refused"):
                audio.get_state()
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertEqual(run.call_args.kwargs["timeout"], 4)
            self.assertEqual(run.call_args.kwargs["env"]["LC_ALL"], "C")

    def test_malformed_snapshot_is_an_error(self):
        for payload in ("not json", "{}"):
            with self.subTest(payload=payload), patch.object(audio, "_command", return_value=payload):
                with self.assertRaises(audio.AudioError):
                    audio.get_state()


if __name__ == "__main__":
    unittest.main()
