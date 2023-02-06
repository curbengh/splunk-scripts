# updateiplocation

A simple add-on to update iplocation database. I created this mostly to learn about [credential storage](https://dev.splunk.com/enterprise/docs/developapps/manageknowledge/secretstorage/secretstoragepython). It's probably better to use [Auto Update MaxMind Database](https://splunkbase.splunk.com/app/5482) app instead, though I've never used it.

## Install

1. `python build.py`
2. Install the output \*.tar.gz

## [updateiplocation](./bin/updateiplocation.py)

[`iplocation`](https://docs.splunk.com/Documentation/SplunkCloud/latest/SearchReference/Iplocation) free database located at "$SPLUNK_HOME/share/GeoLite2-City.mmdb" is only updated in each Splunk release. Run `| updateiplocation` as an alert to receive regular update, MaxMind updates GeoLite2 database twice weekly, Tuesday and Friday.

It uses MaxMind license key from the credential storage located at "$SPLUNK_HOME/etc/apps/updateiplocation/local/passwords.conf". Run [maxmind-license.py](#naxmind-license) to query/add/update one.

`updateiplocation` will generate an event for successful update. When creating an alert, you can trigger an action if there is no result to receive a notification for failed update.

Updated database will be stored at "$SPLUNK_HOME/share/GeoLite2-City-**latest**.mmdb". Splunk needs to be configured to use the new database for `iplocation` through [limits.conf](https://docs.splunk.com/Documentation/Splunk/9.0.3/Admin/Limitsconf#.5Biplocation.5D)

```
# $SPLUNK_HOME/etc/system/local/limits.conf
[iplocation]
db_path = /opt/splunk/share/GeoLite2-City-latest.mmdb
# must be an absolute path,
# "db_path" setting does not support standard Splunk environment variables such as SPLUNK_HOME.
# Windows
# db_path = C:\Splunk\share\GeoLite2-City-latest.mmdb
```

## [naxmind-license](./maxmind-license.py)

_[Install](#install) the addon before running this._

Query/add/update MaxMind license key to the credential storage. A free GeoLite2 license key can be generated using a [MaxMind account](https://www.maxmind.com/en/geolite2/signup).

License key will be validated prior to addition if download.maxmind.com is reachable or `--skip-validate` is not specified.

```
maxmind-license.py [--host] https://localhost:8089 [--check-key] [--skip-validate] [--update] [--delete]
```

Options:

- **host**: Splunk management endpoint. (default: https://localhost:8089)
- **verify**: Verify TLS verification for https connections. (default: False)
- **check-key**: Check whether an input license key is valid by attempting to download GeoLite2-City.tar.gz.sha256 from download.maxmind.com. If it is valid, ask if want to save it. Other options have no effect.
- **skip-validate**: Skip validating license check when adding/updating a license key. License check is automatically skipped if download.maxmind.com is unreachable.
- **update**: Add license key even if there is an existing license key.
- **delete**: Delete existing license key from the credential storage, regardless the key exists or not.

Example:

```
maxmind-license.py
```

1. Prompt for Splunk credential.
2. Prompt for license key.
3. Check license validity.
4. If existing license exists, ask if want to update it.
5. Add license key to the credential storage.

## Credit

MaxMind is either trademark or registered trademark of MaxMind, Inc.
