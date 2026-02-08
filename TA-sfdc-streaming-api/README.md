# [Splunk Add-on for Salesforce Streaming API](https://splunkbase.splunk.com/app/5689)

The Splunk add-on utilises OAuth 2.0 [Username-Password](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&type=5) Flow which is no longer supported by latest Salesforce connected app. This patch switch it to [Client Credentials](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5) Flow instead.

## Apply patch

Tested on v1.1.1 of the Splunk add-on.

```
patch < fix-client-creds-flow.patch TA-sfdc-streaming-api/lib/aiosfstream/auth.py
```

## Installation

Patched TA-sfdc-streaming-api can only be installed in Splunk Enterprise, Splunk Cloud does not allow uploading apps with app IDs that already exist on Splunkbase. I tried changing the app ID to get around this restriction, but the app ended up broken with generic `exit code=2` when I add a new input.
