#!/bin/sh

# Run this in the splunk host as root

set -efux

alias cp="cp -f"
alias mkdir="mkdir -p"
alias rm="rm -rf"

# https://github.com/which-distro/os-release
DISTRO=$(grep -oP '^ID="?\K\w+' "/etc/os-release")
IS_FEDORA_BASE=$(grep -oP '^ID_LIKE="?\K[\w\s]+' "/etc/os-release" | grep "fedora" || [ $? = 1 ])

cp "hosts" "/etc/hosts"

# optional: use static host key
# `HostKey /etc/ssh/splunk_host_ed25519_key` must be set in sshd_config
cp "splunk_host_ed25519_key" "/etc/ssh/splunk_host_ed25519_key"
chmod 600 "/etc/ssh/splunk_host_ed25519_key"
cp "splunk_host_ed25519_key.pub" "/etc/ssh/splunk_host_ed25519_key.pub"
chmod 644 "/etc/ssh/splunk_host_ed25519_key.pub"
chown -R root:root "/etc/ssh/"

mkdir "/etc/ssh/sshd_config.d/"
rm "/etc/ssh/sshd_config.d/50-cloud-init.conf"
cp "sshd_config" "/etc/ssh/splunk_host_ed25519_key"
echo "Installed SSH host key"

# optional: join AD
SSSD="sssd-ad sssd-tools realmd adcli"
if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
  apt install -y --no-upgrade "$SSSD"
elif [ -n "$IS_FEDORA_BASE" ]; then
  dnf install --refresh -y "$SSSD"
elif [ "$DISTRO" = "opensuse" ] || [ "$DISTRO" = "sles" ] || [ "$DISTRO" = "sled" ]; then
  zypper install -y "$SSSD"
fi

mkdir "/etc/sudoers.d/"
cp "sudoers" "/etc/sudoers.d/ad_group"
echo 'Installed "/etc/sudoers.d/ad_group"'

mkdir "/etc/sssd"
cp "sssd.conf" "/etc/sssd/sssd.conf"
systemctl reload sssd.service
echo 'Installed "/etc/sssd/sssd.conf"'

read -p 'Domain Admin username (enter "n" to skip): ' domain_admin
if [ -n "$domain_admin" ] && [ "$domain_admin" != "n" ]; then
  realm join -v "domain.example" -U "$domain_admin"
  echo "Joined Example AD domain"
fi

if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
  CERT_PATH="/usr/local/share/ca-certificates"
  UPDATE_CERT="update-ca-certificates"
elif [ -n "$IS_FEDORA_BASE" ]; then
  CERT_PATH="/usr/share/pki/ca-trust-source/anchors"
  UPDATE_CERT="update-ca-trust"
elif [ "$DISTRO" = "opensuse" ] || [ "$DISTRO" = "sles" ] || [ "$DISTRO" = "sled" ]; then
  # https://github.com/openSUSE/ca-certificates
  CERT_PATH="/usr/share/pki/trust/anchors"
  UPDATE_CERT="update-ca-certificates"
fi
mkdir "$CERT_PATH"
# Enterprise and Splunk Cloud root CA
cp "enterprise_root_cacert.crt" "$CERT_PATH/enterprise_cacert.crt"
cp "enterprise_intermediate_cacert.crt" "$CERT_PATH/enterprise_intermediate_cacert.crt"
# 100_splunkcloud
cp "100_splunkcloud_root_cacert.crt" "$CERT_PATH/100_splunkcloud_root_cacert.crt"
cp "100_splunkcloud_intermediate_cacert.crt" "$CERT_PATH/100_splunkcloud_intermediate_cacert.crt"
# UF CA
cp "splunkuf-ca.crt" "$CERT_PATH/splunkuf-ca.crt"
$UPDATE_CERT
echo "Installed custom CA certs"

# https://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonLinux#Information_on_expected_default_shell_and_caveats_for_Debian_shells
# https://unix.stackexchange.com/a/442518
IS_BASH=$(readlink -f "/bin/sh" | grep "bash" || [ $? = 1 ])
if [ -z "$IS_BASH" ]; then
  ln -sf bash "/bin/sh.bash"
  mv "/bin/sh.bash" "/bin/sh"
  echo "Switched default shell to bash"
fi
