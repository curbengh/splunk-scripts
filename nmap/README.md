# Nmap

Run nmap port scanner and ingest the XML result into Splunk.

nmap is executed per-port basis (`nmap -p20`) instead of all ports (`nmap -p20,21,22`) because the Splunk XML parser (specified through [`KV_MODE`](https://docs.splunk.com/Documentation/Splunk/latest/admin/propsconf#Field_extraction_configuration)) is unable to parse `<ports>` as an array nor depth `a.b.c.d`.

[nmap.sh](./bin/nmap.sh) runs the default [TCP SYN/connect](https://nmap.org/book/man-port-scanning-techniques.html) scan. To run more than one scanning technique (e.g. TCP+UDP), run nmap separately (e.g. `nmap -sT` + `nmap -sU`).

## See also

[XtremeNmapParser](https://github.com/xtormin/XtremeNmapParser): Parse nmap XML to CSV/XLSX/JSON. This is currently not used, to keep things simple.

- Parsing to JSON may enable the use of `nmap -p20,21,22`.
- XNP is more suitable for scanning a wide range of (>10) ports. It can filter port status so that only open ports are ingested into Splunk.
