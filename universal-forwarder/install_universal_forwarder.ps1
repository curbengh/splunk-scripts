Function Rmf {
    foreach ($arg in $args) {
        if (test-path -path $arg) { remove-item -path $arg }
    }
}

set-location -path "$PSScriptRoot"
$argument_list = @(
    "/i",
    "PATH_TO_MSI",
    "USE_LOCAL_SYSTEM=1",
    "AGREETOLICENSE=Yes",
    "/quiet"
)

$FILELIST = Get-ChildItem -Path "." -Filter splunkforwarder-*-x64-release.msi
$SPLUNK_MSI = ""
if ($null -ne $FILELIST) {
    $SPLUNK_MSI = $FILELIST[0] | select-object -expandproperty fullname
}
else {
    write-host "Unable to locate splunkforwarder-*-x64-release.msi in the current folder." -ForegroundColor Red
    exit 1
}
$argument_list = $argument_list -replace "PATH_TO_MSI", "$SPLUNK_MSI"

write-host "Installing Universal Forwarder, please wait.." -ForegroundColor Yellow
start-process msiexec.exe -argumentlist $argument_list -wait -nonewwindow

# DEPLOYMENT_SERVER flag may be lost if UF crashes on first run
$config_file_content = '[deployment-client]
disabled = 0
sslVerifyServerCert = 1
sslVerifyServerName = 1
caCertFile = $SPLUNK_HOME/etc/apps/1-deploymentserver/local/ca-certificates.crt
sslCommonNameToCheck = splunkhostname.domain.example
sslAltNameToCheck = splunkhostname

[target-broker:deploymentServer]
targetUri = https://splunkhostname:8089
'

$uf_dirs = @("$env:programfiles\SplunkUniversalForwarder", "C:\Splunk")
foreach ($uf_dir in $uf_dirs) {
    if (test-path -path "$uf_dir\bin\splunk.exe") {
        $config_file_directory = "$uf_dir\etc\apps\1-deploymentserver\local"
        # after successful sync, this config will be replaced by
        # deployment server's, which has the same content
        $config_file = "$config_file_directory\deploymentclient.conf"

        new-item -ItemType Directory $config_file_directory -Force | out-null
        set-content $config_file $config_file_content
        copy-item -path "ca-certificates.crt" -Destination "$config_file_directory\ca-certificates.crt"

        $uf_system_config = "$uf_dir\etc\system\local"

        # Undo mistake
        Rmf "$uf_system_config\deploymentclient.conf" "$uf_system_config\outputs.conf" "$uf_system_config\server.conf"

        write-host "Restarting Splunk service to apply changes, please wait" -ForegroundColor Yellow
        start-process "$uf_dir\bin\splunk.exe" -ArgumentList restart -NoNewWindow
    }
}
