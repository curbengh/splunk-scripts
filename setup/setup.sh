#!/bin/sh

# Run this in the splunk host as a normal user

PROFILE="$HOME/.profile"
if [ -f "$HOME/.bash_profile" ]; then
  PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.zprofile" ]; then
  PROFILE="$HOME/.zprofile"
fi

HAS_SPLUNK=$(grep -i "splunk" "$PROFILE" || [ $? = 1 ])

if [ -z "$HAS_SPLUNK" ]; then
  cat "profile" >> "$PROFILE"
fi

# load updated profile
. "$PROFILE"
