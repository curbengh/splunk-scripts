#!/usr/bin/env python

"""Build Splunk app package"""

import tarfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from configparser import ConfigParser
from os import getcwd, path
from pathlib import Path, PurePath
from posixpath import join as posixjoin
from re import search
from subprocess import check_call
from sys import executable

APPS_WITH_CERT = ("1-deploymentserver", "1-indexserver", "100_splunkcloud")


def get_version(dir_path: Path) -> str:
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


def exclusion(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Exclude dev files and cache, and reset file/folder permission"""

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
        if name.startswith(posixjoin(app, "bin")) and pathname.suffix in (
            ".sh",
            ".ps1",
            ".cmd",
            ".bat",
            ".py",
        ):
            tarinfo.mode = 0o744
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


def find_ca_cert(dir_arg: Path) -> Path | str:
    """Locate ca-certificates.crt in parent folder of app folder"""

    for i in range(2):
        cert_path = dir_arg.absolute().parents[i].joinpath("ca-certificates.crt")
        if cert_path.is_file():
            return cert_path
    return ""


def main(
    directory: Path | str = getcwd(),
    output: Path | str = getcwd(),
    splunk_sdk: bool = False,
) -> Path:
    """
    :param directory: Path to Splunk app
    :param output: Output folder
    :param splunk_sdk: Install splunk-sdk library
    """

    directory = Path(directory)
    app_name = directory.name
    output_dir = Path(output)
    if not output_dir.is_dir():
        output_dir.mkdir(mode=0o755, parents=True)

    pkg_file = f"{app_name}{get_version(directory)}.tar.gz"
    output_gz = output_dir.joinpath(pkg_file)

    if splunk_sdk is True:
        lib_path = path.join(directory, "lib")
        print(f'Installing splunk-sdk into "{lib_path}"...')
        check_call(
            [
                executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "splunk-sdk == 2.*",
                "-t",
                lib_path,
                "--upgrade",
            ]
        )

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

    print(f"Created {output_gz.absolute()}")
    return output_gz.absolute()


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
    parser.add_argument(
        "--splunk-sdk",
        "-s",
        help="Install splunk-sdk library",
        type="store_true",
    )

    args = parser.parse_args()

    main(**vars(args))
