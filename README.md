# Misc scripts/addon for Splunk

## [updateiplocation](./updateiplocation/)

[`iplocation`](https://docs.splunk.com/Documentation/SplunkCloud/latest/SearchReference/Iplocation) free database located at "$SPLUNK_HOME/share/GeoLite2-City.mmdb" is only updated in each Splunk release. Use [`updateiplocation`](./updateiplocation/) to update it.

## [setup](./setup/)

Splunk setup

## Packaging Splunk apps

`python build.py -d path/to/app-folder -o path/to/output-folder`

[build.py](./build.py) is necessary to remove execute permission from all files. Splunk Cloud will reject any app that contains files with execute permission, except for the "bin/" folder.
