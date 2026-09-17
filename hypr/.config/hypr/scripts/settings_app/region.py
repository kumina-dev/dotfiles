"""System time zone via timedated/polkit; formatting stays per user."""
from kumina_common.process import output


def _command(*args, timeout=10):
    return output(("timedatectl", *args), check=True, timeout=timeout)


def current_timezone():
    return _command("show", "--property=Timezone", "--value")


def get_state():
    current = current_timezone()
    zones = sorted(set(_command("list-timezones").splitlines()))
    if current and current not in zones:
        zones.append(current)
        zones.sort()
    return {"timezone": current, "timezones": zones}


def set_timezone(zone):
    # Validate before invoking a system change; never interpret shell text.
    if not zone or zone not in _command("list-timezones").splitlines():
        raise ValueError("Select a time zone from the list.")
    if current_timezone() != zone:
        _command("set-timezone", zone, timeout=120)
    actual = current_timezone()
    if actual != zone:
        raise RuntimeError(f"Time zone was not applied. Current time zone: {actual}")
    return actual
