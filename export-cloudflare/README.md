# Export Cloudflare DNS records in [BIND config](https://en.wikipedia.org/wiki/Zone_file) format

`| exportcloudflaredns`

Each event represents a zone output.

## Install

`python ../build.py -d export-cloudflare --splunk-sdk`

## [cloudflare-api-key](./cloudflare-api-key.py)

_[Install](#install) the addon before running this._

Query/add/update Cloudflare api key to the credential storage. The [API token](https://dash.cloudflare.com/profile/api-tokens) should have `Zone.Zone.Read` and `Zone.DNS.Read` permissions with IP restriction (if applicable).

API key will be validated prior to addition if api.cloudflare.com is reachable unless `--skip-validate` is specified.

```
cloudflare-api-key.py [--host] https://localhost:8089 [--verify] [--check-key] [--skip-validate] [--update] [--delete]
```

Options:

- **host**: Splunk management endpoint. (default: https://localhost:8089)
- **verify**: Verify TLS verification for https connections. (default: False)
- **check-key**: Check key validity using [`user/tokens/verify`](https://api.cloudflare.com/client/v4/user/tokens/verify) endpoint, without checking for permissions. If it is valid, ask if want to save it. Other options have no effect.
- **skip-validate**: Skip validating api key when adding/updating a license key. Key check is automatically skipped if api.cloudflare.com is unreachable.
- **update**: Add api key even if there is an existing api key.
- **delete**: Delete existing api key from the credential storage, regardless the key exists or not.

Example:

```
cloudflare-api-key.py
```

1. Prompt for Splunk credential.
   - User should have [`edit_storage_passwords`](https://docs.splunk.com/Documentation/Splunk/9.2.1/Installation/AboutupgradingREADTHISFIRST#A_new_capability_has_been_added_that_lets_you_edit_passwords_stored_within_an_app) permission.
2. Prompt for api key.
3. Check key validity.
4. If existing key exists, ask if want to update it.
5. Add api key to the credential storage.
