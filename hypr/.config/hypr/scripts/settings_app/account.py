"""Read the current process user's Linux account and session groups."""
from dataclasses import dataclass
import grp
import os
import pwd

from kumina_common.i18n import translate as tr


@dataclass(frozen=True)
class AccountInfo:
    username: str
    full_name: str
    uid: int
    primary_group: str
    session_groups: str
    home: str
    shell: str

    @property
    def display_name(self):
        return self.full_name or self.username

    def rows(self):
        return [
            (tr("Username"), self.username),
            (tr("Full name"), self.full_name or tr("Not set")),
            (tr("User ID"), str(self.uid)),
            (tr("Primary group"), self.primary_group),
            (tr("Session groups"), self.session_groups),
            (tr("Home directory"), self.home or tr("Not set")),
            (tr("Login shell"), self.shell or tr("System default")),
        ]


class AccountError(RuntimeError):
    pass


def group_label(gid):
    try:
        name = grp.getgrgid(gid).gr_name
    except (KeyError, OSError):
        return tr("Unknown group (GID {gid})", gid=gid)
    return f"{name} ({gid})"


def collect():
    # Environment variables like USER and HOME are not authoritative identity.
    uid = os.getuid()
    try:
        entry = pwd.getpwuid(uid)
    except (KeyError, OSError) as error:
        raise AccountError(tr("Could not read the Linux account for user ID {uid}.", uid=uid)) from error

    # Other GECOS fields may contain office/phone data; only use the name field.
    full_name = entry.pw_gecos.split(",", 1)[0].strip()
    try:
        group_ids = set(os.getgroups()) | {os.getgid()}
        groups = ", ".join(group_label(gid) for gid in sorted(group_ids))
    except OSError:
        groups = tr("Unavailable")

    return AccountInfo(
        username=entry.pw_name,
        full_name=full_name,
        uid=uid,
        primary_group=group_label(entry.pw_gid),
        session_groups=groups,
        home=entry.pw_dir,
        shell=entry.pw_shell,
    )


def format_report(info):
    return "\n".join(f"{label}: {value.replace(chr(10), chr(10) + '  ')}" for label, value in info.rows())
