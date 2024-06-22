# Patches for [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

- Add a new sourcetype aws:firehose:waf
  - Map fields to [Web data model](https://docs.splunk.com/Documentation/CIM/5.3.2/User/Web)
  - See [this section](https://gitlab.com/curben/aws-scripts/-/tree/main/waf-firehose-splunk?ref_type=heads#waf-event) for example JSON event.
