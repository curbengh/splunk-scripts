#!/bin/sh

# Run this in the splunk host as root

set -efux

alias cp="cp -f"
alias mkdir="mkdir -p"

SPLUNK_HOME="/opt/splunk"

# Create "splunk" user without password and shell
# Splunk app can still run shell scripts even without shell
id -u "splunk" >/dev/null 2>&1 || user_not_exist="$?"
if [ -n "$user_not_exist" ]; then
  echo '"splunk" user not found, creating...'
  useradd --system --create-home --home-dir "$SPLUNK_HOME" --shell "/usr/sbin/nologin" splunk
else
  echo '"splunk" user exists'
fi

tar xzf "splunk-setup-all.tar.gz"
tar xzf splunk-9*-Linux-x86_64.tgz -C "/opt"

SPLUNK_ETC="$SPLUNK_HOME/etc"
SPLUNK_SYSTEM="$SPLUNK_ETC/system/local"
SPLUNK_CERTS="$SPLUNK_ETC/auth/mycerts"
SPLUNK_APPS="$SPLUNK_ETC/apps"
SPLUNK_DEPLOY_APPS="$SPLUNK_ETC/deployment-apps"

cd "splunk/"

cp "splunk-launch.conf" "$SPLUNK_ETC/splunk-launch.conf"
mkdir "$SPLUNK_SYSTEM"
cp "authorize.conf" "$SPLUNK_SYSTEM/authorize.conf"
cp "indexes.conf" "$SPLUNK_SYSTEM/indexes.conf"
cp "inputs.conf" "$SPLUNK_SYSTEM/inputs.conf"
cp "limits.conf" "$SPLUNK_SYSTEM/limits.conf"
cp "server.conf" "$SPLUNK_SYSTEM/server.conf"
cp "user-seed.conf" "$SPLUNK_SYSTEM/user-seed.conf"
cp "web.conf" "$SPLUNK_SYSTEM/web.conf"

stty -echo
read -p 'Server private key password (input will not be displayed): ' SSL_PASSWORD
stty echo
echo

sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_SYSTEM/inputs.conf"
chmod 600 "$SPLUNK_SYSTEM/inputs.conf"
sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_SYSTEM/server.conf"
chmod 600 "$SPLUNK_SYSTEM/server.conf"
sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_SYSTEM/web.conf"
chmod 600 "$SPLUNK_SYSTEM/web.conf"

tar xzf "100_splunkcloud.tar.gz" -C "$SPLUNK_APPS"

# optional: customise login background
# see splunk/web.conf
APPSERVER="$SPLUNK_APPS/search/appserver/static"
mkdir "$APPSERVER/customfavicon"
cp "favicon.ico" "$APPSERVER/customfavicon/"
mkdir "$APPSERVER/logincustomlogo"
cp "logo.png" "$APPSERVER/logincustomlogo"
mkdir "$APPSERVER/logincustombg"
cp "background.png" "$APPSERVER/logincustombg/img.png"
mkdir "$APPSERVER/pdfcustomlogo"
cp "pdf-logo.jpg" "$APPSERVER/pdfcustomlogo/logo.jpg"

cd "../certs/"

mkdir "$SPLUNK_CERTS"
cp "splunk-cert.pem" "$SPLUNK_CERTS/splunk-cert.pem"
cp "splunk-cert.key" "$SPLUNK_CERTS/splunk-cert.key"
cp "splunk-cert-web.pem" "$SPLUNK_CERTS/splunk-cert-web.pem"
chmod 400 "$SPLUNK_CERTS/splunk-cert"*

# optional: SAML SSO
mkdir "$SPLUNK_ETC/etc/auth/idpCerts"
cp "idpCert.pem" "$SPLUNK_ETC/etc/auth/idpCerts/idpCert.pem"

# Deployment apps
cd "../deployment-apps"

mkdir "$SPLUNK_DEPLOY_APPS"
tar xzf "1-deploymentserver.tar.gz" -C "$SPLUNK_DEPLOY_APPS"
tar xzf "1-indexserver.tar.gz" -C "$SPLUNK_DEPLOY_APPS"
tar xzf "100_splunkcloud.tar.gz" -C "$SPLUNK_DEPLOY_APPS"

# forward logs to heavy forwarder
stty -echo
read -p '1-indexserver private key password (input will not be displayed): ' SSL_PASSWORD
stty echo
echo

sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_DEPLOY_APPS/1-indexserver/local/outputs.conf"

SSL_PASSWORD=""

# forward logs to splunk cloud
stty -echo
read -p '100_splunkcloud private key password (input will not be displayed): ' SSL_PASSWORD
stty echo
echo

sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_APPS/100_splunkcloud/local/outputs.conf"
sed -i "s/sslPassword = ..*/sslPassword = $SSL_PASSWORD/" "$SPLUNK_DEPLOY_APPS/100_splunkcloud/local/outputs.conf"

SSL_PASSWORD=""

# Use the latest cert store
cp "/etc/ssl/certs/ca-certificates.crt" "$SPLUNK_APPS/100_splunkcloud/local/"
cp "/etc/ssl/certs/ca-certificates.crt" "$SPLUNK_DEPLOY_APPS/100_splunkcloud/local/"
cp "/etc/ssl/certs/ca-certificates.crt" "$SPLUNK_DEPLOY_APPS/1-deploymentserver/local/"
cp "/etc/ssl/certs/ca-certificates.crt" "$SPLUNK_DEPLOY_APPS/1-indexserver/local/"

chown -R splunk:splunk "$SPLUNK_HOME"

cp "splunkd.service" "/etc/systemd/system/splunkd.service"
systemctl daemon-reload

read -p 'Start/restart splunk? (y/n): ' RESTART_SPLUNK

if [ "$RESTART_SPLUNK" = "y" ]; then
  echo "Start/restarting splunk..."
  IS_ENABLED=$(systemctl is-enabled "splunkd.service")
  if [ "$IS_ENABLED" != "enabled" ]; then
    systemctl enable --now "splunkd.service"
  else
    systemctl restart "splunkd.service"
  fi
fi
