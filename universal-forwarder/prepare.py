#!/usr/bin/env python

"""Prepare setup files for Splunk deployment and save them into splunk-setup-all.tar.gz"""

import tarfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import date
from os import chdir, path
from pathlib import Path, PurePath
from re import search, sub
from sys import path as sys_path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

today = date.today().strftime("%Y%m%d")

chdir_path = path.dirname(__file__)
chdir(chdir_path)
sys_path.append("..")
from build import main as build_app  # noqa: E402


def exclusion(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Exclude self"""

    # exclude certain folders/files
    pathname = tarinfo.name
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements|prepare\.py|splunkuf-setup-all",
        pathname,
    ):
        return None

    tarinfo.name = sub(r"^\./", "", pathname)

    # reset file stats
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isfile():
        # remove execution permission
        tarinfo.mode = 0o644
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


def glob(pattern, out_path="") -> Path | str:
    filelist = list(Path(".").glob(pattern))
    pattern_ext = PurePath(pattern).suffix
    if len(filelist) >= 1:
        return filelist[0]

    if path.isfile(out_path) and (
        len(pattern_ext) <= 0
        or (len(pattern_ext) >= 1 and PurePath(out_path).suffix == pattern_ext)
    ):
        return out_path

    out_path = path.abspath(Path(input(f"Path to {pattern}: ")))

    if not path.isfile(out_path):
        print(f'"{out_path}" is not a file or does not exist.')
    elif len(pattern_ext) >= 1 and PurePath(out_path).suffix != pattern_ext:
        print(f'"{out_path}" is not a *{pattern_ext} file.')

    return glob(pattern, out_path)


def build_windows():
    uf_msi = glob("splunkforwarder-*-x64-release.msi")
    uf_version = search(r"splunkforwarder-([^-]+)", uf_msi).group(1)
    out_zip = path.join(
        path.dirname(uf_msi), f"splunkuf-setup-all-{uf_version}-{today}.zip"
    )
    print(f"Preparing {path.basename(out_zip)}...")
    with ZipFile(out_zip, "w") as zip:
        zip.write("install_universal_forwarder.ps1")
        zip.write(
            uf_msi,
            arcname=path.basename(uf_msi),
        )
        print(f'Included "{path.basename(uf_msi)}"')
        zip.write(
            path.join("..", "ca-certificates.crt"),
            arcname="ca-certificates.crt",
        )
        print('Included "ca-certificates.crt"')

    print(f"Created {out_zip}")
    print(
        f"\nTo install Universal Forwarder, copy {path.basename(out_zip)} to the device."
    )
    print("Unzip it and run install_universal_forwarder.ps1")


def build_linux():
    uf_gz = glob("splunkforwarder-*-linux-amd64.tgz")
    uf_version = search(r"splunkforwarder-([^-]+)", uf_gz).group(1)
    output_gz = path.join(
        path.dirname(uf_gz), f"splunkuf-setup-all-{uf_version}-{today}.tar.gz"
    )
    with TemporaryDirectory() as tmpdir:
        deploymentserver = build_app(
            # see ../setup/README.md#deployment-apps
            directory=path.join("..", "deployment-apps", "1-deploymentserver"),
            output=tmpdir,
        )
        print(f"Preparing {path.basename(output_gz)}...")
        with tarfile.open(output_gz, "w:gz") as tar:
            tar.add(".", filter=exclusion)
            tar.add(
                deploymentserver,
                filter=exclusion,
                arcname=path.basename(deploymentserver),
            )
            print(f'Included "{path.basename(deploymentserver)}"')
            tar.add(uf_gz, filter=exclusion, arcname=path.basename(uf_gz))
            print(f'Included "{path.basename(uf_gz)}"')

    print(f'Created "{output_gz}"')
    print(
        f"\nTo install Universal Forwarder, {path.basename(output_gz)} to the device."
    )
    print("Then execute the shell script as root.")


def main(windows: bool = False, linux: bool = False):
    """
    :param windows: Prepare Windows setup
    :param linux: Prepare Linux setup
    """

    if windows is False and linux is False:
        windows = True

    if windows:
        build_windows()
    if linux:
        build_linux()


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Prepare Splunk Universal Forwarder setup files.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--windows",
        "-w",
        help="Prepare Windows setup.",
        action="store_true",
    )
    parser.add_argument(
        "--linux",
        "-l",
        help="Prepare Linux setup.",
        action="store_true",
    )

    args = parser.parse_args()
    main(**vars(args))
