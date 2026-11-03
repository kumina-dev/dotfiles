#!/usr/bin/env python3
"""Check KDE's private audio QML API against what the KumiOS Control Center uses.

The Control Center's audio controls rely on plasma-pa's private
`org.kde.plasma.private.volume` module, which KDE may change in any release.
This reads the installed module's qmltypes description (read-only) and verifies
every type, property, method and enum value recorded in
`audio-api-contract.json`. Run it after KDE upgrades. Exit status 0 means
compatible, 1 means incompatible or unreadable.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
CONTRACT = SOURCE / "audio-api-contract.json"
TOKEN = re.compile(r'\s+|//[^\n]*|/\*.*?\*/|("(?:[^"\\]|\\.)*")|([A-Za-z_][\w.]*)|(-?\d+(?:\.\d+)?)|([{}\[\]:,;])', re.S)


def tokens(text):
    position = 0
    while position < len(text):
        match = TOKEN.match(text, position)
        if not match:
            raise ValueError(f"Unreadable qmltypes near offset {position}")
        position = match.end()
        string, word, number, punctuation = match.groups()
        if string is not None:
            yield ("value", json.loads(string))
        elif word is not None:
            yield ("value", {"true": True, "false": False}.get(word, word))
        elif number is not None:
            yield ("value", float(number) if "." in number else int(number))
        elif punctuation is not None:
            yield ("punct", punctuation)


def parse(text):
    """Parse a qmltypes document into nested {"type", "fields", "children"} objects."""
    stream = list(tokens(text))
    index = 0

    def peek():
        return stream[index] if index < len(stream) else (None, None)

    def take():
        nonlocal index
        if index >= len(stream):
            raise ValueError("qmltypes ends unexpectedly (truncated or corrupt file)")
        index += 1
        return stream[index - 1]

    def value():
        kind, token = take()
        if (kind, token) == ("punct", "["):
            items = []
            while peek() != ("punct", "]"):
                items.append(value())
                if peek() == ("punct", ","):
                    take()
            take()
            return items
        if kind != "value":
            raise ValueError(f"Unexpected {token!r} in qmltypes")
        return token

    def block(type_name):
        node = {"type": type_name, "fields": {}, "children": []}
        while True:
            kind, token = take()
            if (kind, token) == ("punct", "}"):
                return node
            if (kind, token) == ("punct", ";"):
                continue
            if kind != "value":
                raise ValueError(f"Unexpected {token!r} in qmltypes")
            if peek() == ("punct", ":"):
                take()
                node["fields"][token] = value()
            elif peek() == ("punct", "{"):
                take()
                node["children"].append(block(token))
            else:
                raise ValueError(f"Unexpected token after {token!r} in qmltypes")

    while index < len(stream):
        kind, token = take()
        if kind == "value" and token == "import":
            while peek()[0] == "value" and index < len(stream) and peek()[1] != "Module":
                take()
            continue
        if kind == "value" and peek() == ("punct", "{"):
            take()
            return block(token)
    raise ValueError("qmltypes has no Module")


class Module:
    def __init__(self, document, module_name):
        self.components = {}
        self.exported = {}
        prefix = module_name + "/"
        for component in (c for c in document["children"] if c["type"] == "Component"):
            fields = component["fields"]
            self.components[fields["name"]] = component
            for export in fields.get("exports", []):
                if export.startswith(prefix):
                    self.exported[export[len(prefix):].split()[0]] = component

    def resolve(self, type_name):
        """Component for a property type, which qmltypes may write without its C++ namespace."""
        if type_name in self.components:
            return self.components[type_name]
        matches = [c for n, c in self.components.items() if n.split("::")[-1] == type_name]
        return matches[0] if len(matches) == 1 else None

    def chain(self, component):
        while component is not None:
            yield component
            component = self.components.get(component["fields"].get("prototype"))

    def members(self, component, kind):
        found = {}
        for link in self.chain(component):
            for child in link["children"]:
                if child["type"] == kind and child["fields"]["name"] not in found:
                    found[child["fields"]["name"]] = child["fields"]
        return found


def check(qmltypes_text, contract):
    """Return a list of human-readable incompatibilities (empty when compatible)."""
    module = Module(parse(qmltypes_text), contract["module"])
    problems = []
    for name, wanted in contract["types"].items():
        component = module.exported.get(name)
        if component is None:
            problems.append(f"type {name} is no longer exported")
            continue
        fields = component["fields"]
        if wanted.get("singleton") and not fields.get("isSingleton"):
            problems.append(f"{name} is no longer a singleton")
        if wanted.get("creatable") and fields.get("isCreatable") is False:
            problems.append(f"{name} can no longer be created from QML")
        properties = module.members(component, "Property")
        methods = module.members(component, "Method")
        enums = module.members(component, "Enum")
        problems += [f"{name}.{p} property removed or renamed" for p in wanted.get("properties", []) if p not in properties]
        problems += [f"{name}.{m}() method removed or renamed" for m in wanted.get("methods", []) if m not in methods]
        for enum, values in wanted.get("enums", {}).items():
            if enum not in enums:
                problems.append(f"{name}.{enum} enum removed or renamed")
                continue
            problems += [f"{name}.{enum}.{v} value removed or renamed" for v in values if v not in enums[enum]["values"]]
    devices = contract["devices"]
    for via in devices["via"]:
        owner, prop = via.split(".")
        component = module.exported.get(owner)
        definition = module.members(component, "Property").get(prop) if component else None
        if definition is None:
            continue  # already reported above
        device = module.resolve(definition.get("type"))
        if device is None:
            problems.append(f"{via} has unknown device type {definition.get('type')!r}")
            continue
        properties = module.members(device, "Property")
        for p in devices["properties"]:
            if p not in properties:
                problems.append(f"{via}.{p} property removed or renamed")
            elif p in devices["writable"] and properties[p].get("isReadonly"):
                problems.append(f"{via}.{p} is no longer writable")
    return problems


def qmltypes_path(module_name):
    qtpaths = shutil.which("qtpaths6") or "/usr/lib/qt6/bin/qtpaths6"
    root = Path(subprocess.run([qtpaths, "--query", "QT_INSTALL_QML"], text=True,
                               capture_output=True, check=True).stdout.strip())
    directory = root / module_name.replace(".", "/")
    qmldir = directory / "qmldir"
    if not qmldir.is_file():
        raise FileNotFoundError(f"KDE audio module {module_name} is not installed ({directory})")
    typeinfo = next((line.split()[1] for line in qmldir.read_text().splitlines()
                     if line.startswith("typeinfo ")), None)
    if not typeinfo:
        raise FileNotFoundError(f"{qmldir} names no typeinfo file")
    return directory / typeinfo


def installed_version(package):
    try:
        output = subprocess.run(["pacman", "-Q", package], text=True, capture_output=True,
                                check=True, timeout=30).stdout.split()
        return output[1].rsplit("-", 1)[0] if len(output) == 2 else None
    except (OSError, subprocess.SubprocessError):
        return None


def report():
    """(compatible, lines) for the installed module; never raises for a missing module."""
    contract = json.loads(CONTRACT.read_text())
    verified = contract["verified_with"]
    version = installed_version(verified["package"])
    lines = []
    try:
        problems = check(qmltypes_path(contract["module"]).read_text(), contract)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        problems = [str(error)]
    label = f"{verified['package']} {version or '(version unknown)'}"
    if problems:
        lines.append(f"KDE audio API INCOMPATIBLE with the Control Center ({label}):")
        lines += ["  - " + problem for problem in problems]
        lines.append("  Audio controls will show a Sound settings fallback; other controls keep working.")
    else:
        lines.append(f"KDE audio API compatible ({label}).")
    if version and version != verified["version"]:
        lines.append(f"  Last verified with {verified['version']}; recheck audio controls after this KDE update "
                     f"and update verified_with in plasma/audio-api-contract.json.")
    return not problems, lines


def main():
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    compatible, lines = report()
    print("\n".join(lines))
    return 0 if compatible else 1


if __name__ == "__main__":
    sys.exit(main())
