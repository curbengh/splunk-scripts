"""
Export BIND config of all zones
"""

# PEP 585 & 604 are not available in Python 3.7
# https://docs.splunk.com/Documentation/Splunk/9.3.0/Python3Migration/PythonCompatibility
# the following import is used to avoid error
from __future__ import annotations

import sys
from configparser import ConfigParser
from datetime import datetime, timezone
from os import environ, path
from time import time as unix_time
from urllib.parse import urlparse

import requests

sys.path.insert(0, path.join(path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import Configuration, GeneratingCommand, dispatch

# Do not change this, see cloudflare-api-key.py
USERNAME = "cloudflare_dns_api"


@Configuration()
class ExportCloudflareDNS(GeneratingCommand):
    def __get_api_key(self) -> str:
        """Query credential storage. Return the api key"""
        service = self.service
        storage_passwords = service.storage_passwords
        for storage_password in storage_passwords.list():
            if storage_password.username == USERNAME:
                return storage_password.clear_password

        raise ValueError("API key not found.")

    def __get_proxy(self, url: str) -> dict | dict[str, dict[str, str]]:
        """
        Determine http proxy setting of a URL according to Splunk server configuration.
        Return {dict} of http/https proxy value if a URL should be proxied.
        """
        hostname = urlparse(url).hostname

        server_conf_path = path.join(
            environ.get("SPLUNK_HOME", path.join("opt", "splunk")),
            "etc",
            "system",
            "local",
            "server.conf",
        )
        server_conf = ConfigParser()
        server_conf.read(server_conf_path)
        proxy_config = server_conf["proxyConfig"] if "proxyConfig" in server_conf.sections() else {}
        proxy_rules = proxy_config.get("proxy_rules", "")
        no_proxy_rules = proxy_config.get("no_proxy", "")
        http_proxy = proxy_config.get("http_proxy", "")
        https_proxy = proxy_config.get("https_proxy", "")

        # https://docs.splunk.com/Documentation/Splunk/9.0.3/Admin/Serverconf#Splunkd_http_proxy_configuration
        if (
            # either configs should not be empty
            (len(http_proxy) >= 1 or len(https_proxy) >= 1)
            # hostname should not be excluded by no_proxy
            and hostname not in no_proxy_rules
            # if proxy_rules is set, should include hostname
            and (len(proxy_rules) == 0 or (len(proxy_rules) >= 1 and hostname in proxy_rules))
        ):
            return {"proxies": {"http": http_proxy, "https": https_proxy}}

        return {}

    def __get(
        self,
        api_path: str = "",
        headers: dict = {},
        params: dict = {},
        is_json: bool = False,
    ) -> dict | str:
        """
        Send a GET request to the URL and return content of the response.

        :param api_path: cloudflare api path, e.g. /zones
        :param is_json: return decoded json response
        """

        url = "https://api.cloudflare.com/client/v4" + api_path
        proxy_config = self.__get_proxy(url)

        try:
            res = requests.get(url, headers=headers, params=params, timeout=5, **proxy_config)
            # pylint: disable=no-member
            if res.status_code == requests.codes.ok:
                if is_json is True:
                    return res.json()

                return res.text

            res.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            raise errh
        except requests.exceptions.ConnectionError as errc:
            raise errc
        except requests.exceptions.Timeout as errt:
            raise errt
        except requests.exceptions.RequestException as err:
            raise err

    def __list_zones(self, headers: dict = {}, result: list[dict] = [], page: int = 1) -> list[dict]:
        """List all zones"""

        params = {
            "per_page": 50,
            "page": page,
        }

        r_obj = self.__get("/zones", headers=headers, params=params, is_json=True)
        result.extend(r_obj["result"])

        if r_obj["result_info"]["page"] < r_obj["result_info"]["total_pages"]:
            return self.__list_zones(headers, result, page + 1)
        else:
            return result

    def __export_dns(self, headers: dict, zone_id: str) -> str:
        """Export BIND config of a DNS zone"""

        dns_records = self.__get(f"/zones/{zone_id}/dns_records/export", headers=headers)

        return dns_records

    def generate(self):
        api_key = self.__get_api_key()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        for zone in self.__list_zones(headers=headers):
            dns_records = self.__export_dns(headers=headers, zone_id=zone["id"])
            modified_on = (
                # Z suffix is only supported in Python >=3.11
                # https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat
                datetime.fromisoformat(zone["modified_on"][0:-1]).replace(tzinfo=timezone.utc).timestamp()
            )
            created_on = datetime.fromisoformat(zone["created_on"][0:-1]).replace(tzinfo=timezone.utc).timestamp()

            yield self.gen_record(
                _time=unix_time(),
                _raw=dns_records,
                host=zone["name"],
                status=zone["status"],
                modified_on=modified_on,
                created_on=created_on,
            )


dispatch(ExportCloudflareDNS, sys.argv, sys.stdin, sys.stdout, __name__)
