# Splunk Universal Forwarder

## Build

```
prepare.py [--windows] [--linux]
```

Options:

- **windows**: Prepare Windows setup
- **linux**: Prepare Linux setup

If neither options is specified, `--windows` will be the default.

Outputs:

- splunkuf-setup-all.zip (`--windows`)
- splunkuf-setup-all.tar.gz (`--linux`)

## Install

Windows: Copy "splunkuf-setup-all.zip" to the target, unzip and run the script.
Linux: Copy "install_universal_forwarder.sh" and "splunkuf-setup-all.tar.gz" to the target and run the script.
