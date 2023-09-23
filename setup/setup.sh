#!/bin/sh

# Run this in the splunk host as a normal user

cp "profile" "$HOME/.profile"
# load updated profile
. "$HOME/.profile"
