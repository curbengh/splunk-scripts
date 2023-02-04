#!/usr/bin/env python

"""Build Splunk app package"""

import tarfile
from configparser import ConfigParser
from os import environ, path
from re import search, sub
from subprocess import check_call
from sys import executable


def version():
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


def exclusion(tarinfo):
    """Exclude dev files and cache, and reset file stats"""

    # exclude certain folders/files
    pathname = tarinfo.name
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements|build\.py|maxmind-license\.py|tar\.gz",
        pathname,
    ):
        return None

    # rename parent folder as "updateiplocation"
    tarinfo.name = sub(r"^.", "updateiplocation", pathname)

    # reset file stats
    # based on https://splunkbase.splunk.com/app/833
    tarinfo.uid = 1001
    tarinfo.gid = 123
    tarinfo.uname = tarinfo.gname = ""

    return tarinfo


print("Installing dependencies into './lib/'...")
check_call(
    [
        executable,
        "-m",
        "pip",
        "install",
        "--quiet",
        "-r",
        path.join("..", "requirements.txt"),
        "-t",
        "lib",
        "--upgrade",
    ]
)

pkg_file = f"updateiplocation-{version()}.tar.gz"
print(f"Creating {pkg_file}...")
with tarfile.open(pkg_file, "w:gz") as tar:
    tar.add(".", filter=exclusion)

# Splunk 8 workaround
# Splunk scheduler may not run scheduled searches (alert/report) without this workaround
commands_conf_path = path.join(
    "default",
    "commands.conf",
)
commands_conf = ConfigParser()
commands_conf.read(commands_conf_path)
commands_conf["default"]["chunked"] = "false"
with open(commands_conf_path, "w") as f:
    commands_conf.write(f)

pkg_file_8 = f"updateiplocation-{version()}-splunk8.tar.gz"
print(f"Creating {pkg_file_8}...")
with tarfile.open(pkg_file_8, "w:gz") as tar:
    tar.add(".", filter=exclusion)

commands_conf["default"]["chunked"] = "true"
with open(commands_conf_path, "w") as f:
    commands_conf.write(f)
