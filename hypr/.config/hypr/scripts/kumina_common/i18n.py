"""Translations for KumiOS-owned UI; never change the system locale.

Windows use one language for their lifetime. Streaming components can pass an
explicit language to translate() after reading the saved preference again.
"""
import json
import os
from pathlib import Path
import tempfile

LANGUAGES = {"en": "English", "fi": "Suomi"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def language_path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kumios/language.json"


def read_language(*, strict=False):
    try:
        data = json.loads(language_path().read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("language") not in LANGUAGES:
            raise ValueError("Unsupported interface language.")
        return data["language"]
    except FileNotFoundError:
        return "en"
    except (OSError, ValueError, TypeError) as error:
        if strict:
            raise RuntimeError(f"Could not read interface language: {error}") from error
        return "en"


def save_language(language):
    if not isinstance(language, str) or language not in LANGUAGES:
        raise ValueError("Unsupported interface language.")
    path = language_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({"language": language}, stream)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


LANGUAGE = read_language()
with (Path(__file__).parent / "translations/fi.json").open(encoding="utf-8") as stream:
    FINNISH = json.load(stream)


def translate(message, *, language=None, **values):
    selected = LANGUAGE if language is None else language
    text = FINNISH.get(message, message) if selected == "fi" else message
    return text.format(**values) if values else text
