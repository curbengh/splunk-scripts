#!/bin/sh

# dash does not support pipefail
IS_DASH=$(readlink -f "/bin/sh" | grep "dash" || [ $? = 1 ])
if [ -n "$IS_DASH" ]; then
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

DISTRO=$(grep -oP '^ID="?\K\w+' "/etc/os-release")
DISTRO_BASE=$(grep -oP '^ID_LIKE="?\K[\w\s]+' "/etc/os-release" || [ $? = 1 ])
IS_DEBIAN_BASE=$(printf "$DISTRO_BASE" | grep "debian" || [ $? = 1 ])
IS_FEDORA_BASE=$(printf "$DISTRO_BASE" | grep "fedora" || [ $? = 1 ])
IS_SUSE_BASE=$(printf "$DISTRO_BASE" | grep "suse" || [ $? = 1 ])

SSSD="sssd-ad sssd-tools realmd adcli"
if [ "$DISTRO" = "debian" ] || [ -n "$IS_DEBIAN_BASE" ]; then
  apt install -y --no-upgrade $SSSD
elif [ "$DISTRO" = "fedora" ] || [ -n "$IS_FEDORA_BASE" ]; then
  dnf install --refresh -y $SSSD
elif [ -n "$IS_SUSE_BASE" ]; then
  zypper install -y $SSSD
fi

mkdir "/etc/sudoers.d/"
cp "sudoers" "/etc/sudoers.d/ad_group"
echo 'Installed "/etc/sudoers.d/ad_group"'

mkdir "/etc/sssd"
cp "sssd.conf" "/etc/sssd/sssd.conf"
systemctl restart sssd.service
echo 'Installed "/etc/sssd/sssd.conf"'

read -p 'Domain Admin username (enter "n" to skip): ' domain_admin
if [ -n "$domain_admin" ] && [ "$domain_admin" != "n" ]; then
  realm join -v "domain.example" -U "$domain_admin"
  echo "Joined Example AD domain"
fi
