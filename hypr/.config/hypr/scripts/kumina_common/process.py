import subprocess


class CommandError(RuntimeError):
    pass


def _program_name(args):
    try:
        return str(
            args[0]
        )
    except (
        IndexError,
        TypeError,
    ):
        return "Command"


def _error_message(
    result,
    fallback,
):
    return (
        result.stderr.strip()
        or result.stdout.strip()
        or fallback
    )


def run(
    args,
    *,
    timeout=None,
    check=False,
    error_type=CommandError,
    fallback="Command failed.",
):
    try:
        result = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise error_type(
            (
                f"{_program_name(args)} "
                "is not installed."
            )
        ) from error
    except subprocess.TimeoutExpired as error:
        raise error_type(
            "Command timed out."
        ) from error
    except OSError as error:
        raise error_type(
            str(error)
        ) from error

    if (
        check
        and result.returncode != 0
    ):
        raise error_type(
            _error_message(
                result,
                fallback,
            )
        )

    return result


def output(
    args,
    *,
    timeout=None,
    check=False,
    error_type=CommandError,
    fallback="Command failed.",
    default="",
):
    result = run(
        args,
        timeout=timeout,
        check=check,
        error_type=error_type,
        fallback=fallback,
    )

    if result.returncode != 0:
        return default

    return result.stdout.strip()