"""Read-only system information; no GTK dependency or elevated commands."""

from kumina_common.i18n import translate as tr
from kumina_common.formatting import format_number
from kumina_common.region import read_preferences

import platform
import re
import shutil
from pathlib import Path

from kumina_common.process import CommandError, output


VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"
UNAVAILABLE = tr("Unavailable")


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def version():
    return read_text(VERSION_FILE) or tr("Development (version unavailable)")


def format_bytes(value, preferences=None):
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{format_number(size, preferences, decimals=1)} {unit}"
        size /= 1024


def cpu_model(cpuinfo):
    for line in cpuinfo.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in ("model name", "Hardware") and value.strip():
            return value.strip()
    return UNAVAILABLE


def memory_size(meminfo, preferences=None):
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB\s*$", meminfo, re.MULTILINE)
    if not match:
        return UNAVAILABLE
    return tr("{size} usable", size=format_bytes(int(match[1]) * 1024, preferences))


def parse_graphics(text):
    """Parse lspci -vmm -nn tags, using the numeric display-controller class."""
    devices = []
    for block in re.split(r"\n\s*\n", text.strip()):
        fields = {}
        for line in block.splitlines():
            tag, separator, value = line.partition("\t")
            if separator:
                fields[tag.rstrip(":")] = value.strip()
        device_class = fields.get("Class", "")
        if not re.search(r"\[03[0-9a-fA-F]{2}\]$", device_class):
            continue
        name = " ".join(fields.get(key, "") for key in ("Vendor", "Device")).strip()
        if name:
            devices.append(name)
    return "\n".join(devices)


def graphics():
    if shutil.which("lspci") is None:
        return tr("Unavailable — install pciutils for GPU details")
    try:
        result = output(
            ["lspci", "-D", "-vmm", "-nn"],
            timeout=5,
            check=True,
        )
    except CommandError:
        return tr("Unavailable — could not read PCI devices")
    return parse_graphics(result) or tr("No PCI graphics device reported")


def storage(path, preferences=None):
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return UNAVAILABLE
    return (
        tr("{total} total · {used} used · {free} free",
           total=format_bytes(usage.total, preferences), used=format_bytes(usage.used, preferences),
           free=format_bytes(usage.free, preferences))
    )


def collect():
    preferences = read_preferences()
    try:
        release = platform.freedesktop_os_release()
        distribution = release.get("PRETTY_NAME") or release.get("NAME") or "Linux"
    except OSError:
        distribution = UNAVAILABLE

    rows = [
        (tr("KumiOS version"), version()),
        (tr("Computer name"), platform.node() or UNAVAILABLE),
        (tr("Operating system"), distribution),
        (tr("Kernel"), f"{platform.release()} ({platform.machine()})"),
        (tr("Processor"), cpu_model(read_text("/proc/cpuinfo"))),
        (tr("Graphics"), graphics()),
        (tr("Memory"), memory_size(read_text("/proc/meminfo"), preferences)),
        (tr("System storage (/)"), storage("/", preferences)),
    ]

    # Show home separately only when it is on a different filesystem.
    home = Path.home()
    try:
        separate_home = home.stat().st_dev != Path("/").stat().st_dev
    except OSError:
        separate_home = False
    if separate_home:
        rows.append((tr("Home storage"), storage(home, preferences)))
    return rows


def format_report(rows):
    return "\n".join(
        f"{label}: {value.replace(chr(10), chr(10) + '  ')}"
        for label, value in rows
    )
