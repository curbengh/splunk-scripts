# Patches for [TA-librenms-data-poller](https://splunkbase.splunk.com/app/5394)

Field extraction on the [LibreNMS](https://www.librenms.org/) polling API. Enable the appropriate stanza in [inputs.conf](./inputs.conf) and update the index. The polling interval is set as 600 seconds (10 minutes), you may want to reduce the interval (for more frequent polling).

To use the the addon, create a new user in LibreNMS and create an API token for that user (Settings > API > API Settings > Create API access token).

Note that [props.conf](./props.conf) includes forwarder and search head config. If you have a separate search head (e.g. Splunk Cloud), the second half of the config will need to be installed there (through a custom app or the Splunk Web).

## "Unable to get local issuer certificate" error

```
ExecProcessor [1643 ExecProcessor] - message from "/opt/splunk/bin/python3.7 /opt/splunk/etc/apps/TA-librenms-data-poller/bin/librenms.py" ERRORHTTPSConnectionPool(host='nms.domain.example', port=443): Max retries exceeded with url: /api/v0/logs/authlog (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1106)')))
```

The addon uses its own bundled [requests](https://pypi.org/project/requests/) which in turn uses the bundled [certifi](https://pypi.org/project/certifi/) root cert store that does not include custom enterprise root cert.

During Splunk Enterprise [setup](../setup/setup-root.sh), enterprise root certs are installed to "/etc/ssl/certs/ca-certificates.crt", so the solution is to replace certifi with that.

```
# root/sudo
cd /opt/splunk/etc/apps/TA-librenms-data-poller/bin/ta_librenms_data_poller/aob_py3/certifi/
mv cacert.pem cacert.pem.old
cp /etc/ssl/certs/ca-certificates.crt cacert.pem
```
