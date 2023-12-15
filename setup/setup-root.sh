#!/bin/sh

# Run this in the splunk host as root

set -efux

alias cp="cp -f"
alias mkdir="mkdir -p"
alias rm="rm -rf"

cp "hosts" "/etc/hosts"

# optional: use static host key
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
apt install -y --no-upgrade "sssd-ad sssd-tools realmd adcli"

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

# Enterprise and Splunk Cloud root CA
mkdir "/usr/local/share/ca-certificates"
cp "enterprise_root_cacert.crt" "/usr/local/share/ca-certificates/enterprise_cacert.crt"
cp "enterprise_intermediate_cacert.crt" "/usr/local/share/ca-certificates/enterprise_intermediate_cacert.crt"
# 100_splunkcloud
cp "100_splunkcloud_root_cacert.crt" "/usr/local/share/ca-certificates/100_splunkcloud_root_cacert.crt"
cp "100_splunkcloud_intermediate_cacert.crt" "/usr/local/share/ca-certificates/100_splunkcloud_intermediate_cacert.crt"
# UF CA
cp "splunkuf-ca.crt" "/usr/local/share/ca-certificates/splunkuf-ca.crt"
update-ca-certificates
echo "Installed custom CA certs"

# https://docs.splunk.com/Documentation/Splunk/latest/Installation/InstallonLinux#Information_on_expected_default_shell_and_caveats_for_Debian_shells
# https://unix.stackexchange.com/a/442518
IS_BASH=$(readlink -f "/bin/sh" | grep "bash" || [ $? = 1 ])
if [ -z "$IS_BASH" ]; then
  ln -sf bash "/bin/sh.bash"
  mv "/bin/sh.bash" "/bin/sh"
  echo "Switched default shell to bash"
fi
