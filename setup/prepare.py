#!/usr/bin/env python

"""Prepare setup files for Splunk deployment and save them into splunk-setup-all.tar.gz"""

import tarfile
from os import chdir, path
from pathlib import Path
from re import search

from build import main as build_app

chdir_path = path.dirname(__file__)
chdir(chdir_path)


def exclusion(tarinfo):
    """Exclude self"""

    # exclude certain folders/files
    pathname = tarinfo.name
    if search(
        r"/\.|\\\.|__pycache__|pyproject\.toml|requirements|prepare\.py|splunk-setup-all\.tar\.gz",
        pathname,
    ):
        return None

    # reset file stats
    # based on https://splunkbase.splunk.com/app/833
    tarinfo.uid = 1001
    tarinfo.gid = 123
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isfile():
        # remove execution permission
        tarinfo.mode = 0o644

        # except for shell scripts
        if tarinfo.name.endswith(".sh"):
            tarinfo.mode = 0o744
    if tarinfo.isdir():
        # remove write permission from group & world
        tarinfo.mode = 0o755

    return tarinfo


while len(list(Path(".").glob("*-Linux-x86_64.tgz"))) <= 0:
    print(
        'Download the latest Splunk Enterprise from "https://www.splunk.com/en_us/download.html"'
        " with a Splunk.com account."
    )
    print(f"Save the *.tgz to {chdir_path}")
    input("Press Enter once done.\n")

while not path.isfile("splunk_host_ed25519_key"):
    print(f'Copy splunk_host_ed25519_key from secret storage to "{chdir_path}" folder.')
    input("Press Enter once done.\n")

while not (
    path.isfile(path.join("certs", "splunk-cert.key"))
    and path.isfile(path.join("certs", "splunk-cert.pem"))
    and path.isfile(path.join("certs", "splunk-cert-web.pem"))
):
    certs = path.join(chdir_path, "certs")
    print(
        f'Copy splunk-cert.key & splunk-cert.pem & splunk-cert-web.pem to "{certs}" folder.'
    )
    input("Press Enter once done.\n")

build_app(
    directory=path.join("..", "deployment-apps", "1-deploymentserver"), output="."
)
build_app(directory=path.join("..", "deployment-apps", "1-indexserver"), output=".")
build_app(directory=path.join("..", "deployment-apps", "100_splunkcloud"), output=".")

output_gz = path.join(chdir_path, "splunk-setup-all.tar.gz")
with tarfile.open(output_gz, "w:gz") as tar:
    tar.add(".", filter=exclusion)
    tar.add(
        path.join("..", "enterprise_root_cacert.crt"),
        arcname="./enterprise_root_cacert.crt",
        filter=exclusion,
    )
    tar.add(
        path.join("..", "enterprise_intermediate_cacert.crt"),
        arcname="./enterprise_intermediate_cacert.crt",
        filter=exclusion,
    )
    tar.add(
        path.join(
            "..",
            "deployment-apps",
            "100_splunkcloud",
            "default",
            "100_splunkcloud_root_cacert.crt",
        ),
        arcname="./100_splunkcloud_root_cacert.crt",
        filter=exclusion,
    )
    tar.add(
        path.join(
            "..",
            "deployment-apps",
            "100_splunkcloud",
            "default",
            "100_splunkcloud_intermediate_cacert.crt",
        ),
        arcname="./100_splunkcloud_intermediate_cacert.crt",
        filter=exclusion,
    )

print(f"Created {output_gz}")
