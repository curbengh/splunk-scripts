#!/usr/bin/env python

"""Build Splunk app package"""

import tarfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from configparser import ConfigParser
from os import getcwd, path
from pathlib import Path, PurePath
from posixpath import join as posixjoin
from re import search

APPS_WITH_CERT = ("1-deploymentserver", "1-indexserver", "100_splunkcloud")


def get_version(dir_path):
    """Return version number from app.conf"""

    app_conf_path = path.join(
        dir_path,
        "default",
        "app.conf",
    )
    app_conf = ConfigParser()
    app_conf.read(app_conf_path)
    launcher = app_conf["launcher"] if "launcher" in app_conf.sections() else {}
    version = launcher.get("version", "")
    return f"-{version}" if len(version) >= 1 else ""


def exclusion(tarinfo):
    """Exclude dev files and cache, and reset file/folder permission"""

    # exclude certain folders/files
    pathname = tarinfo.name
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements|build\.py|tar\.gz", pathname
    ):
        return None

    app = PurePath(pathname).parts[0]

    # reset file stats
    # based on https://splunkbase.splunk.com/app/833
    tarinfo.uid = 1001
    tarinfo.gid = 123
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isfile():
        # remove execution permission
        tarinfo.mode = 0o644

        # except for scripts
        # tarinfo uses posix (not nt)
        if tarinfo.name.startswith(posixjoin(app, "bin")) and path.splitext(
            tarinfo.name
        )[-1] in (".sh", ".ps1", ".cmd"):
            tarinfo.mode = 0o744
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


def find_ca_cert(dir_arg):
    """Locate ca-certificates.crt in parent folder of app folder"""

    for i in range(2):
        cert_path = path.join(PurePath(dir_arg).parents[i], "ca-certificates.crt")
        if path.isfile(cert_path):
            return cert_path
    return ""


def main(**kwargs):
    """
    :param directory (str) Path to Splunk app
    :param output (str) Output folder
    """

    cwd = getcwd()

    directory = kwargs.get("directory", cwd)
    app_name = PurePath(directory).parts[-1]
    output_dir = Path(kwargs.get("output", cwd))
    if not path.isdir(output_dir):
        output_dir.mkdir(mode=0o755, parents=True)

    pkg_file = f"{app_name}{get_version(directory)}.tar.gz"
    output_gz = path.join(output_dir, pkg_file)

    with tarfile.open(output_gz, "w:gz") as tar:
        # arcname: rename directory to app_name
        tar.add(directory, arcname=app_name, filter=exclusion)
        # only certain apps need ca-certificates.crt
        ca_cert = find_ca_cert(directory)
        if app_name in APPS_WITH_CERT and len(ca_cert) >= 1:
            tar.add(
                ca_cert,
                arcname=path.join(app_name, "local", "ca-certificates.crt"),
                filter=exclusion,
            )

    print(f"Created {path.abspath(output_gz)}")


if __name__ == "__main__":
    cwd_default = getcwd()
    parser = ArgumentParser(
        description="Create Splunk app package.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--directory",
        "-d",
        help="Path to Splunk app.",
        default=cwd_default,
        type=Path,
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output folder. Automatically create one if not found.",
        default=cwd_default,
        type=Path,
    )

    args = parser.parse_args()

    main(**vars(args))
