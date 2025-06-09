Function Rmf {
    foreach ($arg in $args) {
        if (test-path -path $arg) { remove-item -Recurse -Force -path $arg }
    }
}

set-location -path "$PSScriptRoot"
$uf_dir = "$env:programfiles\SplunkUniversalForwarder"
$argument_list = @(
    "/i",
    "PATH_TO_MSI",
    "USE_LOCAL_SYSTEM=1",
    "AGREETOLICENSE=Yes",
    "INSTALLDIR=""$uf_dir""",
    "/quiet"
)

$FILELIST = Get-ChildItem -Path "." -Filter splunkforwarder-*-windows-x64.msi
$SPLUNK_MSI = ""
if ($null -ne $FILELIST) {
    $SPLUNK_MSI = $FILELIST[0] | select-object -expandproperty fullname
}
else {
    write-host "Unable to locate splunkforwarder-*-windows-x64.msi in the current folder." -ForegroundColor Red
    exit 1
}
$argument_list = $argument_list -replace "PATH_TO_MSI", "$SPLUNK_MSI"

## Unable to stop service
# $SplunkForwarder = Get-Service -Name "SplunkForwarder" -ErrorAction SilentlyContinue
# if ($null -ne $SplunkForwarder -and $SplunkForwarder.status -eq "Running") {
#     write-host "Stopping Universal Forwarder, please wait.." -ForegroundColor Yellow
#     stop-service -Name "SplunkForwarder"
# }

# Remove configs in C:\Splunk & $SPLUNK_HOME\etc\system\local
# that may conflict with $SPLUNK_HOME\etc\apps\
write-host "Uninstalling Universal Forwarder, please wait..." -ForegroundColor Yellow
start-process msiexec.exe -argumentlist @("/x", "$SPLUNK_MSI", "/quiet") -wait -nonewwindow
Rmf "$uf_dir" "C:\Splunk"

write-host "Installing Universal Forwarder, please wait..." -ForegroundColor Yellow
start-process msiexec.exe -argumentlist $argument_list -wait -nonewwindow

# config file is more reliable,
# DEPLOYMENT_SERVER msi flag may be lost if UF crashes during the initial start
$config_file_content = '[deployment-client]
disabled = 0
sslVerifyServerCert = 1
sslVerifyServerName = 1
caCertFile = $SPLUNK_HOME/etc/apps/1-deploymentserver/local/ca-certificates.crt
sslCommonNameToCheck = splunkhostname.domain.example
sslAltNameToCheck = splunkhostname

[target-broker:deploymentServer]
targetUri = https://splunkhostname.domain.example:8089
'

if (test-path -path "$uf_dir\bin\splunk.exe") {
    $config_file_directory = "$uf_dir\etc\apps\1-deploymentserver\local"
    # after successful sync, this config will be replaced by
    # deployment server's, which has the same content
    $config_file = "$config_file_directory\deploymentclient.conf"

    new-item -ItemType Directory $config_file_directory -Force | out-null
    set-content $config_file $config_file_content
    copy-item -path "ca-certificates.crt" -Destination "$config_file_directory\ca-certificates.crt"

    write-host "Restarting Splunk service to apply changes, please wait..." -ForegroundColor Yellow
    restart-service -name "SplunkForwarder"
}
