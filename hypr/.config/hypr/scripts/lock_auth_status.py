"""Read pam_u2f's pending-file descriptor in the calling Hyprlock process.

This is display-only. It neither reads credentials nor participates in PAM.
"""

import argparse
import os
from pathlib import Path


def find_locker(pid, proc_root=Path("/proc")):
    """Follow our process ancestry, avoiding unrelated locks and sudo prompts."""
    visited = set()
    for _ in range(32):
        if pid <= 1 or pid in visited:
            return None
        visited.add(pid)
        process = proc_root / str(pid)
        try:
            if process.stat().st_uid != os.getuid():
                return None
            if (process / "comm").read_text().strip() == "hyprlock":
                return pid
            status = (process / "status").read_text()
            parent = next(line for line in status.splitlines() if line.startswith("PPid:"))
            pid = int(parent.split(":", 1)[1])
        except (OSError, ValueError, StopIteration):
            return None
    return None


def touch_pending(pid, pending_file=None, proc_root=Path("/proc")):
    """True: pending fd open; False: no pending fd; None: state unavailable."""
    locker = find_locker(pid, proc_root)
    if locker is None:
        return None

    pending_file = pending_file or Path(f"/var/run/user/{os.getuid()}/pam-u2f-authpending")
    try:
        expected = pending_file.stat()
    except FileNotFoundError:
        return False
    except OSError:
        return None

    try:
        descriptors = list((proc_root / str(locker) / "fd").iterdir())
    except OSError:
        return None

    unreadable = False
    for descriptor in descriptors:
        try:
            opened = descriptor.stat()
        except FileNotFoundError:
            # PAM may close a descriptor between directory listing and stat.
            continue
        except OSError:
            unreadable = True
            continue
        if (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino):
            return True
    return None if unreadable else False


def render(pending):
    label = '<span size="xx-large">󰈷</span>\nTouch your security key'
    if pending is True:
        return label
    # Keep a valid, transparent text resource so Hyprlock clears the old icon.
    # Empty command output can leave the previous resource on screen.
    return f'<span alpha="0">{label}</span>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, default=os.getppid(),
                        help="Hyprlock PID for manual diagnosis; defaults to process ancestry")
    parser.add_argument("--status", action="store_true", help="Print touch, idle, or unavailable")
    args = parser.parse_args()
    pending = touch_pending(args.pid)
    if args.status:
        print("touch" if pending is True else "idle" if pending is False else "unavailable")
    else:
        print(render(pending))


if __name__ == "__main__":
    main()
