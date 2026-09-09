"""Read-only system information; no GTK dependency or elevated commands."""

import platform
import re
import shutil
from pathlib import Path

from kumina_common.process import CommandError, output


VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"
UNAVAILABLE = "Unavailable"


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def version():
    return read_text(VERSION_FILE) or "Development (version unavailable)"


def format_bytes(value):
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024


def cpu_model(cpuinfo):
    for line in cpuinfo.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in ("model name", "Hardware") and value.strip():
            return value.strip()
    return UNAVAILABLE


def memory_size(meminfo):
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB\s*$", meminfo, re.MULTILINE)
    if not match:
        return UNAVAILABLE
    return f"{format_bytes(int(match[1]) * 1024)} usable"


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
        return "Unavailable — install pciutils for GPU details"
    try:
        result = output(
            ["lspci", "-D", "-vmm", "-nn"],
            timeout=5,
            check=True,
        )
    except CommandError:
        return "Unavailable — could not read PCI devices"
    return parse_graphics(result) or "No PCI graphics device reported"


def storage(path):
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return UNAVAILABLE
    return (
        f"{format_bytes(usage.total)} total · "
        f"{format_bytes(usage.used)} used · "
        f"{format_bytes(usage.free)} free"
    )


def collect():
    try:
        release = platform.freedesktop_os_release()
        distribution = release.get("PRETTY_NAME") or release.get("NAME") or "Linux"
    except OSError:
        distribution = UNAVAILABLE

    rows = [
        ("KumiOS version", version()),
        ("Computer name", platform.node() or UNAVAILABLE),
        ("Operating system", distribution),
        ("Kernel", f"{platform.release()} ({platform.machine()})"),
        ("Processor", cpu_model(read_text("/proc/cpuinfo"))),
        ("Graphics", graphics()),
        ("Memory", memory_size(read_text("/proc/meminfo"))),
        ("System storage (/)", storage("/")),
    ]

    # Show home separately only when it is on a different filesystem.
    home = Path.home()
    try:
        separate_home = home.stat().st_dev != Path("/").stat().st_dev
    except OSError:
        separate_home = False
    if separate_home:
        rows.append(("Home storage", storage(home)))
    return rows


def format_report(rows):
    return "\n".join(
        f"{label}: {value.replace(chr(10), chr(10) + '  ')}"
        for label, value in rows
    )
