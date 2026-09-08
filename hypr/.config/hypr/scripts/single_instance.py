import fcntl
import os
from pathlib import Path


_lock_handle = None


def acquire(name):
    """
    Acquire a per-user lock for one Kumina utility.

    Returns False when another instance already owns
    the lock. The lock is automatically released when
    the process exits.
    """

    global _lock_handle

    if _lock_handle is not None:
        return True

    safe_name = "".join(
        character
        if (
            character.isalnum()
            or character in "-_"
        )
        else "_"
        for character in str(name)
    )

    if not safe_name:
        raise ValueError(
            "Instance name cannot be empty."
        )

    runtime_dir = os.environ.get(
        "XDG_RUNTIME_DIR"
    )

    if runtime_dir:
        lock_path = (
            Path(runtime_dir)
            / f"kumina-{safe_name}.lock"
        )
    else:
        lock_path = (
            Path("/tmp")
            / (
                f"kumina-{os.getuid()}-"
                f"{safe_name}.lock"
            )
        )

    handle = lock_path.open(
        "a+",
        encoding="utf-8",
    )

    try:
        fcntl.flock(
            handle.fileno(),
            (
                fcntl.LOCK_EX
                | fcntl.LOCK_NB
            ),
        )
    except BlockingIOError:
        handle.close()

        return False

    handle.seek(0)
    handle.truncate()

    handle.write(
        f"{os.getpid()}\n"
    )

    handle.flush()

    _lock_handle = handle

    return True