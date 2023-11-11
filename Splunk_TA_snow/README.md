# Patches for [Splunk_TA_snow](https://splunkbase.splunk.com/app/1928)

## Add "change" tag

The tag is necessary to include change_request and change_task events into the Ticket Management data model.

## Fix src_user alias

`src_user` field should alias to `adv_caller_id` field (incident) or `dv_opened_by`, instead of `sys_created_by`. `sys_created_by` is either user ID or "system" for auto-created tickets. `src_user` field is used in [Ticket Management](https://docs.splunk.com/Documentation/CIM/latest/User/TicketManagement#Fields_for_Ticket_Management_event_datasets) data model.

## Build

```
build.py [--input] /path/to/splunk-add-on-for-servicenow_*.tgz [--cloud]
```

Options:

- **input**: Path to Splunk app. (default: "splunk-add-on-for-servicenow\_\*.tgz" in the current directory)
- **cloud**: Create Splunk Cloud-compatible app.

Outputs:

- Splunk_TA_snow\_\*.tgz
- custom-Splunk_TA_snow\_\*.tgz (if `--cloud` is specified)
