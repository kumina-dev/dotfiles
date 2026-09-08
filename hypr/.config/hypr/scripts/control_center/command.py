import subprocess


def run(command):
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
    )


def output(command):
    result = run(command)

    if result.returncode != 0:
        return ""

    return result.stdout.strip()