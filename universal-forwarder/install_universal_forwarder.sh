#!/bin/sh

# Run this script as root

if ! (set -o pipefail 2>/dev/null); then
  # dash does not support pipefail
  set -efx
else
  set -efx -o pipefail
fi

# bash does not expand alias by default for non-interactive script
if [ -n "$BASH_VERSION" ]; then
  shopt -s expand_aliases
fi

alias cp="cp -f"
alias mkdir="mkdir -p"
alias rm="rm -rf"

TEMP_DIR="/tmp/splunkuf-$(date +%s)/"
SPLUNK_HOME="/opt/splunkforwarder"
SPLUNK_USER="splunkfwd"
. "/etc/os-release"
DISTRO="$ID"
DISTRO_BASE="$ID_LIKE"
IS_DEBIAN_BASE=$(printf "$DISTRO_BASE" | grep "debian" || [ $? = 1 ])
IS_UBUNTU_BASE=$(printf "$DISTRO_BASE" | grep "ubuntu" || [ $? = 1 ])
IS_FEDORA_BASE=$(printf "$DISTRO_BASE" | grep "fedora" || [ $? = 1 ])
IS_SUSE_BASE=$(printf "$DISTRO_BASE" | grep "suse" || [ $? = 1 ])
IS_ARCH_BASE=$(printf "$DISTRO_BASE" | grep "arch" || [ $? = 1 ])

# Create "splunkfwd" user without password and shell
# Splunk app can still run shell scripts even without shell
if ! id -u "$SPLUNK_USER" >/dev/null 2>&1; then
  echo "\"$SPLUNK_USER\" user not found, creating..."
  useradd --system --create-home --home-dir "$SPLUNK_HOME" --shell "/usr/sbin/nologin" "$SPLUNK_USER"
else
  echo "\"$SPLUNK_USER\" user exists"
fi

# Grant access to /var/log
if [ "$DISTRO" = "debian" ] || [ -n "$IS_DEBIAN_BASE" ] || [ -n "$IS_UBUNTU_BASE" ]; then
  usermod --append --groups "adm" "$SPLUNK_USER"
fi

mkdir "$TEMP_DIR"
SCRIPT_DIR=$(dirname "$0")
find "$SCRIPT_DIR" -type f -name 'splunkuf-setup-all-*.tar.gz' | xargs -I _ tar xzf _ -C "$TEMP_DIR"

cd "$TEMP_DIR"
find "." -type f -name 'splunkforwarder-*-linux-amd64.tgz' | xargs -I _ tar xzf _ -C "/opt"
tar xzf "1-deploymentserver.tar.gz" -C "$SPLUNK_HOME/etc/apps"

chown -R "$SPLUNK_USER":"$SPLUNK_USER" "$SPLUNK_HOME"

# Required by cpu_metric.sh & vmstat_metric.sh of Splunk_TA_nix
if [ "$DISTRO" = "debian" ] || [ -n "$IS_DEBIAN_BASE" ] || [ -n "$IS_UBUNTU_BASE" ]; then
  apt install -y --no-upgrade "sysstat"
elif [ "$DISTRO" = "fedora" ] || [ -n "$IS_FEDORA_BASE" ]; then
  if ! command -v dnf &> /dev/null
  then
    alias dnf="yum"
  fi
  dnf install -y "sysstat"
elif [ -n "$IS_SUSE_BASE" ]; then
  zypper install -y "sysstat"
elif [ "$DISTRO" = "photon" ]; then
  tdnf install --refresh -y "sysstat"
elif [ "$DISTRO" = "arch" ] || [ -n "$IS_ARCH_BASE" ]; then
  pacman -Sy --noconfirm "sysstat"
fi

cp "splunkd.service" "/etc/systemd/system/splunkd.service"

# "Executable path is not absolute" error
# this error is fixed in Ubuntu 20.04
# it's probably fixed prior to systemd 245, but definitely after systemd 237 (Ubuntu 18.04)
if [ $(systemctl --version | grep -oP 'systemd\s\K\d+') -lt "245" ]; then
  sed -E -i 's|([+-])chown|\1/bin/chown|g' "/etc/systemd/system/splunkd.service"
fi

# cgroup1
if [ -d "/sys/fs/cgroup/unified/" ]; then
  sed -i 's|cgroup/system.slice|cgroup/unified/system.slice|' "/etc/systemd/system/splunkd.service"
elif [ -d "/sys/fs/cgroup/systemd/" ]; then
  sed -i 's|cgroup/system.slice|cgroup/systemd/system.slice|' "/etc/systemd/system/splunkd.service"
fi

systemctl daemon-reload

echo "Start/restarting splunk..."
IS_ENABLED=$(systemctl is-enabled "splunkd.service" || [ $? = 1 ])
if [ "$IS_ENABLED" != "enabled" ]; then
  systemctl enable --now "splunkd.service"
else
  systemctl restart "splunkd.service"
fi
