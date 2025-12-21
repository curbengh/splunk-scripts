# Patches for [Splunk_SA_CIM](https://splunkbase.splunk.com/app/1621)

- Extract `uri_path` and `uri_query` from `url` [field](https://docs.splunk.com/Documentation/CIM/latest/User/Web).
- Add `src_ip` field to [Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication) and [Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change) to differentiate from `src` which is usually aliased from `src_nt_host`/`src_host`.
