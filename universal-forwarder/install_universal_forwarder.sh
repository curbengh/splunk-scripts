#!/bin/sh

# Run this script as root

set -efux

alias cp="cp -f"
alias mkdir="mkdir -p"
alias rm="rm -rf"

TEMP_DIR="/tmp/splunkuf-$(date +%s)/"
SPLUNK_HOME="/opt/splunkforwarder"
# https://github.com/which-distro/os-release
DISTRO=$(grep -oP '^ID="?\K\w+' "/etc/os-release")
DISTRO_VERSION=$(grep -oP '^VERSION_ID="?\K[\d.]+' "/etc/os-release")

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

case "$DISTRO" in
  "ubuntu")
    INSTALL="apt install -y --no-upgrade"
    ;;
  "debian")
    INSTALL="apt-get install -y --no-upgrade"
    ;;
  "centos")
    INSTALL="dnf install --refresh -y"
    ;;
  "fedora")
    INSTALL="dnf install --refresh -y"
    ;;
  "opensuse-leap")
    INSTALL="zypper install -y"
    ;;
  "opensuse-tumbleweed")
    INSTALL="zypper install -y"
    ;;
  "photon")
    INSTALL="tdnf install --refresh -y"
    ;;
esac

# Required by cpu_metric.sh & vmstat_metric.sh of Splunk_TA_nix
$INSTALL "sysstat"

# "Executable path is not absolute" error
# this error is fixed in Ubuntu 20.04
# it's probably fixed in prior to systemd 245, but definitely after systemd 237 (Ubuntu 18.04)
if [ $(systemctl --version | grep -oP 'systemd\s\K\d+') -lt "245" ];
  sed -E -i 's|([+-])chown|\1/bin/chown|g' "/etc/systemd/system/splunkd.service"
fi

# cgroup1
if [ -d "/sys/fs/cgroup/unified/" ]; then
  sed -i 's|cgroup/system.slice|cgroup/unified/system.slice|' "/etc/systemd/system/splunkd.service"
fi

systemctl daemon-reload

echo "Start/restarting splunk..."
IS_ENABLED=$(systemctl is-enabled "splunkd.service")
if [ "$IS_ENABLED" != "enabled" ]; then
  systemctl enable --now "splunkd.service"
else
  systemctl restart "splunkd.service"
fi
