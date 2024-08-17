# Splunk add-ons, patches and setup scripts

## Packaging Splunk apps

`python build.py -d path/to/app-folder -o path/to/output-folder`

[build.py](./build.py) is necessary to remove execute permission from all files. Splunk Cloud will reject any app that contains files with execute permission, except for the "bin/" folder. Some folders have custom build.py to build patched add-on.

## [export-cloudflare](./export-cloudflare/)

Export Cloudflare DNS records to Splunk

## [nmap](./nmap/)

Run nmap port scanner and ingest the XML result into Splunk.

## [setup](./setup/)

Splunk Enterprise setup.

## [universal-forwarder](./universal-forwarder/)

Universal Forwarder setup.

## [updateiplocation](./updateiplocation/)

[`iplocation`](https://docs.splunk.com/Documentation/SplunkCloud/latest/SearchReference/Iplocation) bundled database located at "$SPLUNK_HOME/share/GeoLite2-City.mmdb" is only updated in each Splunk release. Use [`updateiplocation`](./updateiplocation/) to manually update it.
