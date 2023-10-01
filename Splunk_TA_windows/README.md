# Patches for [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)

## Additional fields extraction for Splunk_TA_windows

Field extraction/transformation on output log of [`Get-WindowsUpdateLog`](https://learn.microsoft.com/en-us/powershell/module/windowsupdate/get-windowsupdatelog) launched by "Splunk_TA_windows/bin/powershell/generate_windows_update_logs.ps1". Since Windows Server 2016 and Windows 10, Windows Update log is no longer available at "C:\Windows\WindowsUpdate.log".

## Build

```
build.py [--input] /path/to/splunk-add-on-for-vmware-esxi-logs_*.tgz [--cloud]
```

Options:

- **input**: Path to Splunk app. (default: "splunk-add-on-for-vmware-esxi-logs\_\*.tgz" in the current directory)
- **cloud**: Create Splunk Cloud-compatible app.

Outputs:

- Splunk_TA_esxilogs\_\*.tgz
- custom-Splunk_TA_esxilogs\_\*.tgz (if `--cloud` is specified)
