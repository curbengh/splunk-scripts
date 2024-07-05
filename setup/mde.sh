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

if ! command -v python &> /dev/null
then
  alias python="python3"
fi

alias cp="cp -f"
alias curl="curl -sSL"
alias mkdir="mkdir -p"

DISTRO=$(grep -oP '^ID="?\K\w+' "/etc/os-release")
DISTRO_VERSION=$(grep -oP '^VERSION_ID="?\K[\w\.]+' "/etc/os-release" || [ $? = 1 ])
MAJOR_VERSION="${DISTRO_VERSION%.*}"
DISTRO_BASE=$(grep -oP '^ID_LIKE="?\K[\w\s]+' "/etc/os-release" || [ $? = 1 ])
IS_DEBIAN_BASE=$(printf "$DISTRO_BASE" | grep "debian" || [ $? = 1 ])
IS_UBUNTU_BASE=$(printf "$DISTRO_BASE" | grep "ubuntu" || [ $? = 1 ])
IS_FEDORA_BASE=$(printf "$DISTRO_BASE" | grep "fedora" || [ $? = 1 ])
IS_SUSE_BASE=$(printf "$DISTRO_BASE" | grep "suse" || [ $? = 1 ])
IS_OPENSUSE=$(printf "$DISTRO" | grep "^opensuse" || [ $? = 1 ])

if [ "$DISTRO" = "debian" ] || [ -n "$IS_DEBIAN_BASE" ]; then
  # Pop!_OS
  if [ -n "$IS_UBUNTU_BASE" ]; then
    DISTRO="ubuntu"
  fi

  mkdir "/etc/apt/sources.list.d/"

  curl "https://packages.microsoft.com/config/$DISTRO/$DISTRO_VERSION/prod.list" -o "/tmp/microsoft.list"
  curl "https://packages.microsoft.com/keys/microsoft.asc" | gpg --dearmor > "/tmp/microsoft.gpg"

  cp "/tmp/microsoft.list" "/etc/apt/sources.list.d/microsoft-prod.list"

  # https://learn.microsoft.com/en-us/defender-endpoint/linux-install-manually#ubuntu-and-debian-systems
  KEYRING=$(grep -ioP 'signed-by="?\K[^\s\]"]+' "/tmp/microsoft.list" || [ $? = 1 ])
  if [ -z "$KEYRING" ]; then
    KEYRING="/etc/apt/trusted.gpg.d/microsoft.gpg"
  fi
  mkdir "$(dirname $KEYRING)"
  cp "/tmp/microsoft.gpg" "$KEYRING"

  apt update
  apt install -y --no-upgrade mdatp libplist-utils
elif [ "$DISTRO" = "fedora" ] || [ -n "$IS_FEDORA_BASE" ]; then
  # packages.microsoft.com/config/centos/9/ does not exist
  if [ "$DISTRO" = "centos" ] && [ "$DISTRO_VERSION" -ge "9" ]; then
    DISTRO="rhel"
  fi

  # packages.microsoft.com/config/almalinux/ does not exist
  if [ "$DISTRO" = "almalinux" ]; then
    DISTRO="alma"
  fi

  # packages.microsoft.com/config/rhel/9.4/ does not exist
  DISTRO_VERSION="$MAJOR_VERSION"
  DNF_REPO="https://packages.microsoft.com/config/$DISTRO/$DISTRO_VERSION/prod.repo"

  dnf config-manager --add-repo "$DNF_REPO"
  rpm --import "https://packages.microsoft.com/keys/microsoft.asc"

  dnf install --refresh -y "mdatp"
elif [ -n "$IS_SUSE_BASE" ]; then
  # opensuse-leap/opensuse-tumbleweed
  if [ -n "$IS_OPENSUSE" ]; then
    DISTRO="opensuse"
    # 12 & 15
    if [ "$MAJOR_VERSION" != "42" ] && [ "$MAJOR_VERSION" != "43" ]; then
      DISTRO_VERSION="$MAJOR_VERSION"
    fi
  fi

  if [ "$DISTRO" = "sled" ]; then
    DISTRO="sles"
  fi

  zypper addrepo -c -f -n microsoft-prod "https://packages.microsoft.com/config/$DISTRO/$DISTRO_VERSION/prod.repo"
  rpm --import "https://packages.microsoft.com/keys/microsoft.asc"

  zypper install -y -l "mdatp"
fi

# https://learn.microsoft.com/en-us/defender-endpoint/linux-install-manually#client-configuration
python "MicrosoftDefenderATPOnboardingLinuxServer.py"
mkdir "/etc/opt/microsoft/mdatp/managed/"
cp "mdatp_managed.json" "/etc/opt/microsoft/mdatp/managed/mdatp_managed.json"
echo "Installed Defender for Endpoint"
