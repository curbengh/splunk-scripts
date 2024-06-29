# Technology Add-On for Aruba Clearpass

[Authentication](https://docs.splunk.com/Documentation/CIM/5.3.2/User/Authentication) CIM mapping for sourcetype `aruba:clearpass:syslog`.

Install this app on the search head.

## UDP Syslog

```
Jun 28 12:34:56 10.0.0.1 2024-06-28 12:34:56,789 10.0.0.1 Syslog to Splunk 11111 1 0 Common.Username=user,Common.Service=Service Name,Common.Roles=Role Name, [User Authenticated],RADIUS.Auth-Source=AD:ad-domain.full.fqdn,RADIUS.Auth-Method=EAP-PEAP,EAP-MSCHAPv2,Common.System-Posture-Token=UNKNOWN,Common.Enforcement-Profiles=[Profile Name], Enforcement Profile Name (VLAN123),Common.Host-MAC-Address=abcdef123456,Common.NAS-IP-Address=10.1.0.1,Common.Error-Code=0,Common.Request-Timestamp=2024-06-28 12:33:44+01:00
```

- `10.0.0.1`: Clearpass controller IP.
- `2024-06-28 12:34:56,789`: Event time in local time, usually later than the `Common.Request-Timestamp`.
- `Syslog to Splunk`: Configurable syslog name.
- `11111`: Unique event id.
- `RADIUS.Auth-Method`: Can contain multiple methods.
- `Common.NAS-IP-Address`: Network Access Server, can be same or different than the controller IP.
