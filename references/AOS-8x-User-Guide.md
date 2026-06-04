# AOS-8.x User Guide Reference

Canonical PDF URL:
https://arubanetworking.hpe.com/techdocs/ArubaOS-8.x-Books/AOS-8x-User-Guide.pdf

PDF index page:
https://arubanetworking.hpe.com/techdocs/ArubaOS/AOS_8x_WebHelp/Content/view-pdfs.htm

Direct PDF download returned HTTP 403 from the documentation host during local download attempts on 2026-06-04, so this file stores the canonical reference link and the configuration-flow topics to use when improving MCP prompts.

Useful configuration-flow topics from the indexed guide:

- Mobility Conductor configuration hierarchy
- Centralized configuration and validation
- Managed devices configuration workflow
- VLAN assignment and named VLANs
- Basic user-centric network configuration
- Campus WLAN workflow
- Control Plane Security and AP allowlists
- Backup Mobility Conductor and redundancy
- Configuration validation and serviceability

Prompt design implication:

- Start configuration review at the correct hierarchy path.
- Validate managed device and AP live state before analyzing WLAN config.
- Map VLANs, AP groups, Virtual APs, SSID profiles, AAA profiles, user roles, and server groups together.
- Separate intended design from inherited/default values.
- Confirm live advertisement/client evidence after config review.
