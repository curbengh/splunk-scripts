#!/bin/sh

# Run this script as root

set -efux

alias cp="cp -f"
alias mkdir="mkdir -p"
alias rm="rm -rf"

TEMP_DIR="/tmp/splunkuf-$(date +%s)/"
SPLUNK_HOME="/opt/splunkforwarder"
# https://github.com/which-distro/os-release
DISTRO=$(grep -oP '(?<=^NAME=")[\w]+' "/etc/os-release")
DISTRO_VERSION=$(grep -oP '(?<=VERSION_ID=")[\d.]+' "/etc/os-release")

# Create "splunkfwd" user without password and shell
# Splunk app can still run shell scripts even without shell
id -u "splunkfwd" >/dev/null 2>&1 || user_not_exist="$?"
if [ -n "$user_not_exist" ]; then
  echo '"splunkfwd" user not found, creating...'
  useradd --system --create-home --home-dir "$SPLUNK_HOME" --shell "/usr/sbin/nologin" splunkfwd
else
  echo '"splunkfwd" user exists'
fi

mkdir "$TEMP_DIR"
SCRIPT_DIR=$(dirname "$0")
tar xzf "$SCRIPT_DIR/splunkuf-setup-all.tar.gz" -C "$TEMP_DIR"

cd "$TEMP_DIR"
find "." -type f -name 'splunkforwarder-*-Linux-x86_64.tgz' | xargs -I _ tar xzf _ -C "/opt"
tar xzf "1-deploymentserver.tar.gz" -C "$SPLUNK_HOME/etc/apps"

chown -R splunkfwd:splunkfwd "$SPLUNK_HOME"

cp "splunkd.service" "/etc/systemd/system/splunkd.service"

if [ "$DISTRO" = "Ubuntu" ]; then
  # Required by cpu_metric.sh & vmstat_metric.sh of Splunk_TA_nix
  apt install -y --no-upgrade "sysstat"
  if [ "$DISTRO_VERSION" = "18.04" ] || [ "$DISTRO_VERSION" = "20.04" ]; then
    # cgroup1
    sed -i 's|cgroup/system.slice|cgroup/unified/system.slice|' "/etc/systemd/system/splunkd.service"
    if [ "$DISTRO_VERSION" = "18.04" ]; then
      # "Executable path is not absolute" error
      sed -E -i 's|([+-])chown|\1/bin/chown|g' "/etc/systemd/system/splunkd.service"
    fi
  fi
elif [ "$DISTRO" = "CentOS Stream" ]; then
  dnf install --refresh -y "sysstat"
fi

systemctl daemon-reload

echo "Start/restarting splunk..."
IS_ENABLED=$(systemctl is-enabled "splunkd.service")
if [ "$IS_ENABLED" != "enabled" ]; then
  systemctl enable --now "splunkd.service"
else
  systemctl restart "splunkd.service"
fi
