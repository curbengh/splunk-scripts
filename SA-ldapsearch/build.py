#!/usr/bin/env python

"""Build custom SA-ldapsearch app"""

import tarfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os import getcwd, path
from pathlib import Path, PurePath
from posixpath import join as posixjoin
from re import search
from shutil import rmtree

old_flag = "names.append('TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION')\n\n"
new_flags = """names.append('TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION')
    if flags & 0x2000000:
        names.append('NO_AUTH_DATA_REQUIRED')
    if flags & 0x4000000:
        names.append('PARTIAL_SECRETS_ACCOUNT')
    if flags & 0x8000000:
        names.append('USE_AES_KEYS')

"""
old_format = "'1.2.840.113556.1.4.8':             format_user_flag_enum,         # User-Account-Control\n\n"
new_format = """'1.2.840.113556.1.4.8':             format_user_flag_enum,         # User-Account-Control
    '1.2.840.113556.1.4.1460':          format_user_flag_enum,         # ms-DS-User-Account-Control-Computed

"""


def exclusion(tarinfo):
    """Exclude self"""

    # exclude certain folders/files
    pathname = tarinfo.name
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements|build\.py|\.tar\.gz|\.tgz",
        pathname,
    ):
        return None

    app = PurePath(pathname).parts[0]

    # reset file stats
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isfile():
        # remove execution permission
        tarinfo.mode = 0o644

        # except for scripts
        # tarinfo uses posix (not nt)
        if (
            tarinfo.name.startswith(posixjoin(app, "bin"))
            and path.splitext(tarinfo.name)[-1] == ".py"
        ):
            tarinfo.mode = 0o744
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


def main(**kwargs):
    """
    :param input (str) Path to the downloaded Splunk app
    """

    app_gz = kwargs.get("input", "")
    while not path.isfile(app_gz):
        print(
            "Download the latest [Splunk Supporting Add-on for Active Directory]",
            "(https://splunkbase.splunk.com/app/1151) with a Splunk.com account.",
        )
        app_gz = input("Path to splunk-supporting-add-on-for-active-directory_*.tgz: ")

    app_dir, app_filename = path.split(app_gz)
    version = path.splitext(app_filename)[0].split("_")[-1]
    new_gz = path.join(app_dir, f"SA-ldapsearch_{version}.tgz")
    path.dirname(__file__)

    app = ""
    with tarfile.open(app_gz) as tar:
        app = path.commonpath(tar.getnames())
        tar.extractall(path=app_dir, filter="data")

    app_out_dir = path.join(app_dir, app)
    print(f'Extracted "{app_gz}" to "{app_out_dir}"')

    with tarfile.open(new_gz, "w:gz") as tar_server:
        r_str = ""
        f_path = path.join(
            app_out_dir, "bin", "packages", "app", "formatting_extensions.py"
        )
        with open(f_path, encoding="utf-8") as r:
            r_str = r.read()
        with open(f_path, "w", encoding="utf-8") as w:
            w.write(r_str.replace(old_flag, new_flags).replace(old_format, new_format))

        tar_server.add(app_out_dir, filter=exclusion, arcname=app)

    print(f'Created "{new_gz}"')

    rmtree(app_out_dir, ignore_errors=True)
    print(f'Removed "{app_out_dir}"')


if __name__ == "__main__":
    files = Path(getcwd()).glob("splunk-supporting-add-on-for-active-directory_*.tgz")
    app_paths = []
    for i in files:
        app_paths.append(i)
    app_path = app_paths[0] if len(app_paths) >= 1 else ""

    parser = ArgumentParser(
        description="Create Splunk app package.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Path to Splunk app.",
        default=app_path,
        type=Path,
    )

    args = parser.parse_args()
    main(**vars(args))
