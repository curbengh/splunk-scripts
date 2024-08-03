#!/usr/bin/env python

"""
Add Cloudflare API key to the Splunk credential storage
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from getpass import getpass
from os import environ, path
from socket import gaierror
from sys import exit as sys_exit
from urllib.parse import ParseResult, urlparse

from requests import Response, get
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout
from splunklib import client
from splunklib.binding import AuthenticationError
from splunklib.binding import HTTPError as SplunkHTTPError
from splunklib.client import Service

# username to identify the api key stored as a password
# this is not your Cloudflare account login
USERNAME = "cloudflare_dns_api"

NAMESPACE = {
    "owner": "nobody",
    "app": "export-cloudflare",
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
    :param skip_validate: Skip validating the api key before storing it
    :param check_key: Validate an input api key
    :param delete: Delete existing api key
    :param update: Always replace api key
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
        api_key: str = prompt_key()
        if is_valid_key(api_key):
            is_add_key = input("Do you wish to save it? [y/n] ")
            if is_add_key.lower() == "y":
                # is_valid_key already validated the key
                main(skip_validate=True)
        print("Nothing to do.")
        sys_exit()
    elif delete:
        service: Service = login(**login_params)
        delete_key(service)
    else:
        service: Service = login(**login_params)
        api_key: str = prompt_key()
        add_key(service, api_key, validate, always_update)


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

    print("The user's role must have 'edit_storage_passwords' capability.")
    username = input("Username: ")
    password = getpass("Password: ")

    try:
        service: Service = client.connect(
            username=username, password=password, **login_params, **NAMESPACE
        )
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
            print(
                "Splunk management port 8089 uses https by default and may not respond to http"
            )
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


def add_key(
    service: Service,
    api_key: str,
    validate: bool = True,
    always_update: bool = False,
):
    """
    Add api key to credential storage

    :param service: Authenticated Splunk connection
    :param api_key: API key
    :param validate: Validate api key, default: True
    :param always_update: Add api key even if there is an existing api key, default: False
    """

    if validate and is_cloudflare_up() and not is_valid_key(api_key):
        return
    if validate is False or not is_cloudflare_up():
        print("Skipping api key check...")

    try:
        print("Saving api key...")
        service.storage_passwords.create(api_key, USERNAME)
    except SplunkHTTPError as err:
        if "password already exists" in str(err):
            print("Existing api key found.")
            if always_update:
                print("--update option specified, proceed to delete existing key...")
            is_replace = (
                always_update
                or input("Do you wish to update it? [y/n] ").lower() == "y"
            )
            if is_replace:
                delete_key(service)
                add_key(service, api_key, validate)
    else:
        print(f"Saved api key with username '{USERNAME}'.")
        pwd_conf = path.join(
            environ.get("SPLUNK_HOME", "$SPLUNK_HOME"),
            "etc",
            "apps",
            "export-cloudflare",
            "local",
            "passwords.conf",
        )
        print(
            f"The encrypted password can be found in the `[credential::{USERNAME}:]` stanza of {pwd_conf}"
        )


def delete_key(service: Service):
    """Delete api key"""
    try:
        service.storage_passwords.delete(USERNAME)
        print("api key deleted.")
    except KeyError:
        print("api key not found.")
    except SplunkHTTPError as err:
        raise err


def prompt_key(api_key: str = "") -> str:
    """Prompt for api key if no argument or invalid key format"""
    if not (isinstance(api_key, str) and len(api_key) == 40):
        if len(api_key) >= 1:
            print("Invalid api key format.")
        api_key = input("API Key: ").strip()
        prompt_key(api_key)
    return api_key


def prompt_retry() -> bool:
    """Ask if user wants to retry entering api key"""
    retry = input("Retry? [y/n] ").strip()
    if retry.lower() == "y":
        api_key = prompt_key()
        return is_valid_key(api_key)
    return False


def is_valid_key(api_key: str = "") -> bool:
    """
    Attempts to verify api key
    Return true if the key is valid.
    """

    api_key: str = prompt_key(api_key)
    headers = {"Authorization": f"Bearer {api_key}"}

    print("Validating api key...")
    try:
        r: Response = get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers=headers,
            timeout=5,
        )
        r.raise_for_status()
        print("Valid api key.")
        return True
    except HTTPError as err:
        res = err.response
        if res.status_code == 401 and "Invalid API Token" in res.text:
            print("Invalid api key.")
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


def is_cloudflare_up() -> bool:
    """Return true if api.cloudflare.com is reachable"""
    try:
        res: Response = get("https://api.cloudflare.com/client/v4/ips", timeout=5)
        res.raise_for_status()
        return True
    except HTTPError:
        print("api.cloudflare.com is unreachable")
        return False
    except RequestsConnectionError:
        print("api.cloudflare.com is unreachable")
        return False
    except Timeout:
        print("api.cloudflare.com is unreachable")
        return False
    except RequestException:
        print("api.cloudflare.com is unreachable")
        return False


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Add Cloudflare API key to the Splunk credential storage.",
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
    parser.add_argument(
        "--check-key", "-k", help="Validate an input api key.", action="store_true"
    )
    parser.add_argument(
        "--skip-validate",
        "-s",
        help="Skip validating the api key before storing it.",
        action="store_true",
    )
    parser.add_argument(
        "--update", "-y", help="Always replace api key.", action="store_true"
    )
    parser.add_argument(
        "--delete", "-d", help="Delete existing api key.", action="store_true"
    )

    main(**vars(parser.parse_args()))
