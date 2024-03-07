#!/bin/sh

ports="21 23"
subnets="192.168.1.0/24 192.168.2.0/24 192.168.3.0/24"

mkdir -p "$SPLUNK_HOME/var/log/nmap/"

for port in $ports; do
  xml_location="/tmp/nmap_port${port}_$(date +%Y%m%d-%H%M%S).xml"

  nmap -p"$port" -sV -oX "$xml_location" -R --system-dns $subnets > /dev/null

  # "-z" requires GNU sed
  # remove prefix, suffix, host status (so that it port state is parsed instead)
  # hosthint element may not exist
  sed -r -z -u \
    -e 's@.*(</hosthint>|<debugging level="[[:digit:]]+"/>)\n<host @<host @g' \
    -e 's|<runstats>.*||g' \
    -e 's|<status state="([[:alpha:]]+)" reason="([[:alpha:]-]+)" reason_ttl="([[:digit:]]+)"/>|<status host_state="\1" host_reason="\2" host_reason_ttl="\3"/>|g' \
    -e 's/<hostname name=/<hostname hostname=/g' \
    -e 's/<service name=/<service service_name=/g' \
    -i "$xml_location"

  # save to monitored folder only after sed,
  # otherwise splunk will ingest partial output while nmap is running
  cp "$xml_location" "$SPLUNK_HOME/var/log/nmap/"
done
