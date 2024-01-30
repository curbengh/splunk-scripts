"""
Download the latest GeoLite2 database and save it to $SPLUNK_HOME/share/GeoLite2-City-latest.mmdb
"""

import sys
import tarfile
from hashlib import sha256
from io import BytesIO
from os import environ
from pathlib import Path
from time import time

from requests import get
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

sys.path.insert(0, str(Path(__file__).parent.joinpath("..", "lib").resolve()))
from splunklib.searchcommands import Configuration, GeneratingCommand, dispatch

# Do not change this, see "maxmind-license.py"
LICENSE_USERNAME = "maxmind"

MMDB_PATH = Path(environ.get("SPLUNK_HOME")).joinpath("share")


@Configuration()
class UpdateGeoIP(GeneratingCommand):
    """Defines a search command that generates event records"""

    def __get_license(self):
        """Query credential storage. Return the {str} license key"""
        service = self.service
        storage_passwords = service.storage_passwords
        for storage_password in storage_passwords.list():
            if storage_password.username == LICENSE_USERNAME:
                return storage_password.clear_password

        raise ValueError("License key not found.")

    def __get_mmdb(self, members):
        """Return the {tarfile.TarInfo} mmdb file found in a gzip"""
        for tarinfo in members:
            if Path(tarinfo.name).suffix == ".mmdb":
                # Avoid replacing the default database "GeoLite2-City.mmdb"
                # Custom path needs to be specified in $SPLUNK_HOME/etc/system/local/limits.conf
                tarinfo.name = "GeoLite2-City-latest.mmdb"
                return tarinfo
        raise FileNotFoundError(
            "Unable to locate any mmdb file in the downloaded gzip."
        )

    def __download(self):
        """Download GeoLite2-City.tar.gz and return its binary content"""
        license_key = self.__get_license()

        params = {"edition_id": "GeoLite2-City", "license_key": license_key}

        try:
            geolite2 = get(
                "https://download.maxmind.com/app/geoip_download",
                params={**params, **{"suffix": "tar.gz"}},
                timeout=5,
            )
            geolite2.raise_for_status()

            geolite2_sha256 = get(
                "https://download.maxmind.com/app/geoip_download",
                params={**params, **{"suffix": "tar.gz.sha256"}},
                timeout=5,
            )
            geolite2_sha256.raise_for_status()

            sha256sum = geolite2_sha256.text.split(" ")[0]

            if sha256(geolite2.content).hexdigest() == sha256sum:
                return geolite2.content

            raise IOError("Hashsum mismatched.")
        except HTTPError as err:
            raise err
        except RequestsConnectionError as err:
            raise err
        except Timeout as err:
            raise err
        except RequestException as err:
            raise err
        except IOError as err:
            raise err

    def update_mmdb(self):
        """Download GeoLite2 gzip and extract its mmdb"""
        gzip_content = self.__download()
        with tarfile.open(fileobj=BytesIO(gzip_content), mode="r:gz") as tar:
            mmdb = self.__get_mmdb(tar)
            filter_param = {}
            if sys.version_info >= (3, 2):
                filter_param.update({"set_attrs": False})
            if sys.version_info >= (3, 11, 4):
                filter_param.update({"filter": "data"})
            tar.extract(mmdb, path=MMDB_PATH, **filter_param)

    def generate(self):
        self.update_mmdb()
        yield self.gen_record(_time=time(), message=f"Successfully updated {MMDB_PATH}")


dispatch(UpdateGeoIP, sys.argv, sys.stdin, sys.stdout, __name__)
