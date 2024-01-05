#!/bin/sh

ports="21 23"
subnets="192.168.1.0/24 192.168.2.0/24 192.168.3.0/24"

mkdir -p "$SPLUNK_HOME/var/log/nmap"
cd "$SPLUNK_HOME/var/log/nmap"

for port in $ports; do
  filename="nmap_port${port}_$(date +%Y%m%d-%H%M%S).xml"
  nmap -p"$port" -sV -oX "$filename" -R --system-dns $subnets > /dev/null

  # "-z" requires GNU sed
  # remove prefix, suffix, host status (so that it port state is parsed instead)
  sed -z -u -e 's|.*</hosthint>\n<host |<host |g' -e 's|<runstats>.*||g' -e 's|<status state="[[:alpha:]]+" reason="[[:alpha:]-]+" reason_ttl="[[:digit:]]+"/>||g' -i "$filename"
done
