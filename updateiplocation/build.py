#!/usr/bin/env python

"""Build Splunk app package"""

import tarfile
from configparser import ConfigParser
from os import environ, path
from pathlib import PurePath
from posixpath import join as posixjoin
from re import search
from subprocess import check_call
from sys import executable


def version() -> str:
    """
    Return version number from app.conf or commit hash if in CI
    """

    commit_sha = (
        (
            # gitlab
            environ.get("CI_COMMIT_TAG")
            or environ.get("CI_COMMIT_SHORT_SHA")
            # github
            or (
                environ.get("GITHUB_REF_NAME")
                if environ.get("GITHUB_REF_TYPE") == "tag"
                else None
            )
            or environ.get("GITHUB_SHA", "")[0:8]
        )
        if environ.get("CI") == "true"
        else None
    )
    if commit_sha:
        return commit_sha

    app_conf_path = path.join(
        "default",
        "app.conf",
    )
    app_conf = ConfigParser()
    app_conf.read(app_conf_path)
    launcher = app_conf["launcher"] if "launcher" in app_conf.sections() else {}
    return launcher.get("version", "")


def exclusion(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Exclude dev files and cache, and reset file stats"""

    # exclude certain folders/files
    name = tarinfo.name
    pathname = PurePath(name)
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements",
        name,
    ) or (len(pathname.parts) == 2 and tarinfo.isfile() and pathname.suffix != ".md"):
        return None

    app = pathname.parts[0]

    # reset file stats
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isfile():
        # remove execution permission
        tarinfo.mode = 0o644

        # except for scripts
        # tarinfo uses posix (not nt)
        if name.startswith(posixjoin(app, "bin")) and pathname.suffix == ".py":
            tarinfo.mode = 0o744
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


print("Installing dependencies into './lib/'...")
check_call(
    [
        executable,
        "-m",
        "pip",
        "install",
        "--quiet",
        "splunk-sdk == 1.*",
        "-t",
        "lib",
        "--upgrade",
    ]
)

pkg_file = f"updateiplocation-{version()}.tar.gz"
print(f"Creating {pkg_file}...")
with tarfile.open(pkg_file, "w:gz") as tar:
    tar.add(".", filter=exclusion, arcname="updateiplocation")
