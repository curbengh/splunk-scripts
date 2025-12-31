#!/usr/bin/env python

"""
Add your free MaxMind GeoLite2 license key to the credential storage
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from getpass import getpass
from os import environ, path
from socket import gaierror
from sys import exit as sys_exit
from urllib.parse import ParseResult, urlparse

from requests import get
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout
from splunklib import client
from splunklib.binding import AuthenticationError
from splunklib.binding import HTTPError as SplunkHTTPError
from splunklib.client import Service

# username to identify the license key stored as a password
# this is not your MaxMind account login
LICENSE_USERNAME = "maxmind"

NAMESPACE = {
    "owner": "nobody",
    "app": "updateiplocation",
    "sharing": "app",
}


def main(
    host: str = "https://localhost:8089",
    verify: bool = False,
    skip_validate: bool = False,
    check_key: bool = False,
    delete: bool = False,
    update: bool = False,
):
    """
    :param host: Splunk management endpoint
    :param verify: Verify TLS verification for https connections
    :param skip_validate: Skip validating a license key before storing it
    :param check_key: Validate an input license key
    :param delete: Delete existing license key
    :param update: Always replace license key
    """

    host: ParseResult = urlparse(host)
    login_params = {
        "host": host.hostname or "localhost",
        "port": host.port or 8089,
        "scheme": host.scheme or "https",
        "verify": verify,
    }

    validate: bool = not skip_validate
    always_update: bool = update

    if check_key:
        license_key = prompt_license()
        if is_valid_license(license_key):
            is_add_key = input("Do you wish to save it? [y/n] ")
            if is_add_key.lower() == "y":
                # is_valid_license already validated the key
                main(skip_validate=True)
        print("Nothing to do.")
        sys_exit()
    elif delete:
        service = login(**login_params)
        delete_license(service)
    else:
        service = login(**login_params)
        license_key = prompt_license()
        add_license(service, license_key, validate, always_update)


# pylint:disable=inconsistent-return-statements
def login(
    host: str = "localhost",
    port: int = 8089,
    scheme: str = "https",
    verify: bool = False,
) -> Service:
    """
    Connect to the Splunk management endpoint.

    :param host: Splunk hostname.
    :param port: Splunk port.
    :param scheme: The scheme for accessing the service, https or http.
    :param verify: Enable SSL verification for https connections.

    Return an authenticated {splunklib.client.Service} connection
    """

    login_params = {"host": host, "port": port, "scheme": scheme, "verify": verify}

    print("The user's role must have 'admin_all_objects' capability.")
    username = input("Username: ")
    password = getpass("Password: ")

    try:
        service = client.connect(username=username, password=password, **login_params, **NAMESPACE)
        print("Successfully login.")
        return service
    except gaierror as err:
        print("Encountered socket.gaierror")
        if "Name or service not known" in str(err):
            print(f"Unable to resolve {login_params['host']}")
        login(**login_params)
    except ConnectionResetError:
        print("Encountered ConnectionResetError")
        if login_params["scheme"] != "https":
            print("Splunk management port 8089 uses https by default and may not respond to http")
        login(**login_params)
    except ConnectionRefusedError:
        print("Encountered ConnectionResetError")
        if login_params["port"] != 8089:
            print("Possible incorrect port. Splunk management port defaults to 8089")
        login(**login_params)
    except AuthenticationError:
        print("Encountered AuthenticationError")
        login(**login_params)
    except SplunkHTTPError:
        print("Encountered HTTPError")
        login(**login_params)


# Unused, it may be more efficient through error catching
# def has_license(service: Service) -> bool:
#     """Return true if there is an existing license key"""
#     storage_passwords = service.storage_passwords
#     for storage_password in storage_passwords.list():
#         if storage_password.username == LICENSE_USERNAME:
#             print("Existing license key found.")
#             return True
#     return False


def add_license(
    service: Service,
    license_key: str,
    validate: bool = True,
    always_update: bool = False,
):
    """
    Add license key to credential storage

    :param service: Authenticated Splunk connection
    :param license_key: License key
    :param validate: Validate license key, default: True
    :param always_update: Add license key even if there is an existing license key, default: False
    """

    if validate and is_maxmind_up() and not is_valid_license(license_key):
        return
    if validate is False or not is_maxmind_up():
        print("Skipping license check...")

    try:
        print("Saving license key...")
        service.storage_passwords.create(license_key, LICENSE_USERNAME)
    except SplunkHTTPError as err:
        if "password already exists" in str(err):
            print("Existing license key found.")
            if always_update:
                print("--update option specified, proceed to delete existing key...")
            is_replace = always_update or input("Do you wish to update it? [y/n] ").lower() == "y"
            if is_replace:
                delete_license(service)
                add_license(service, license_key, validate)
    else:
        print(f"Saved license key with username '{LICENSE_USERNAME}'.")
        pwd_conf = path.join(
            environ.get("SPLUNK_HOME", "$SPLUNK_HOME"),
            "etc",
            "apps",
            "updateiplocation",
            "passwords.conf",
        )
        print(f"The encrypted password can be found in the `[credential::maxmind:]` stanza of {pwd_conf}")


def delete_license(service: Service):
    """Delete license key"""
    try:
        service.storage_passwords.delete(LICENSE_USERNAME)
        print("License key deleted.")
    except KeyError:
        print("License key not found.")
    except SplunkHTTPError as err:
        raise err


def prompt_license(license_key: str = "") -> str:
    """Prompt for license key if no argument or invalid key format"""
    if not (isinstance(license_key, str) and len(license_key) == 16):
        if len(license_key) >= 1:
            print("Invalid license key format.")
        license_key = input("License Key: ").strip()
        prompt_license(license_key)
    return license_key


def prompt_retry() -> bool:
    """Ask if user wants to retry entering license key"""
    retry = input("Retry? [y/n] ").strip()
    if retry.lower() == "y":
        license_key = prompt_license()
        return is_valid_license(license_key)
    return False


def is_valid_license(license_key: str = "") -> bool:
    """
    Attempts to download GeoLite2-City.tar.gz.sha256 using the license_key
    Return true if download is okay.
    """

    license_key = prompt_license(license_key)
    params = {"edition_id": "GeoLite2-City", "license_key": license_key}

    print("Validating license key...")
    try:
        geolite2_sha256 = get(
            "https://download.maxmind.com/app/geoip_download",
            params={**params, **{"suffix": "tar.gz.sha256"}},
            timeout=5,
        )
        geolite2_sha256.raise_for_status()
        print("Valid license key.")
        return True
    except HTTPError as err:
        res = err.response
        if res.status_code == 401 and "Invalid license key" in res.text:
            print("Invalid license key.")
        else:
            print(err)
        return prompt_retry()
    except RequestsConnectionError as err:
        print(err)
        return prompt_retry()
    except Timeout as err:
        print(err)
        return prompt_retry()
    except RequestException as err:
        print(err)
        return prompt_retry()


def is_maxmind_up() -> bool:
    """Return true if download.maxmind.com is reachable"""
    try:
        res = get("https://download.maxmind.com", timeout=5)
        res.raise_for_status()
        return True
    except HTTPError:
        print("download.maxmind.com is unreachable")
        return False
    except RequestsConnectionError:
        print("download.maxmind.com is unreachable")
        return False
    except Timeout:
        print("download.maxmind.com is unreachable")
        return False
    except RequestException:
        print("download.maxmind.com is unreachable")
        return False


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Add your free MaxMind GeoLite2 license key to the credential storage.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        "-H",
        help="Splunk management endpoint",
        default="https://localhost:8089",
    )
    parser.add_argument(
        "--verify",
        "-V",
        help="Verify TLS verification for https connections.",
        action="store_true",
    )
    parser.add_argument("--check-key", "-k", help="Validate an input license key.", action="store_true")
    parser.add_argument(
        "--skip-validate",
        "-s",
        help="Skip validating a license key before storing it.",
        action="store_true",
    )
    parser.add_argument("--update", "-y", help="Always replace license key.", action="store_true")
    parser.add_argument("--delete", "-d", help="Delete existing license key.", action="store_true")

    main(**vars(parser.parse_args()))
