@ECHO OFF
set SplunkApp=TA-Applocker

powershell.exe -command ". '%SPLUNK_HOME%\etc\apps\%SplunkApp%\bin\%1'"

