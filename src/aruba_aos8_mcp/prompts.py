from __future__ import annotations

from collections.abc import Callable

from mcp.server.fastmcp import FastMCP


def aos8_health_overview() -> str:
    """Guide an operator-friendly health overview of an AOS8 environment."""
    return """
You are an Aruba AOS8 operations assistant. Build a concise health overview using live MCP tools.

Workflow:
1. Call aos8_get_health_summary.
2. Call aos8_get_managed_devices and summarize conductor, standby, and managed-device status.
3. Call aos8_get_ap_summary and summarize AP count by group/model plus any down APs.
4. If the health summary reports empty clients or tunnels, state that clearly without treating it as a hard failure.
5. Classify any issue by troubleshooting zone: client, infrastructure, or WLAN function/service.

Output:
- Start with overall status: ok, attention, or degraded.
- Include short tables for controllers/managed devices and APs.
- Call out exact issues and likely next checks.
- Include scope questions when evidence is incomplete: one client or many, one AP or many, one SSID or many, one location or many, and what changed.
- Do not paste raw full JSON unless the user asks.
"""


def aos8_troubleshoot_ap(ap_name: str = "") -> str:
    """Guide troubleshooting for one AP or all APs if no AP name is provided."""
    target = ap_name or "<all APs>"
    return f"""
You are troubleshooting AOS8 AP connectivity for: {target}.

Workflow:
1. Call aos8_get_ap_summary to identify AP status, group, active controller, standby controller, serial, and model.
2. If ap_name is provided, call aos8_show_command with "show ap details ap-name {target}".
3. Also check "show ap database long" and, when relevant, "show ap active", "show ap bss-table", and "show ap essid".
4. If APs are up but BSS/ESSID/radio tables are empty, explain whether that may be due to AP group/profile assignment or query context.
5. For AP discovery/registration issues, check DHCP/IP reachability, controller discovery, AP group, LMS/backup LMS, cluster node list behavior, licenses, and platform AP capacity.

Output:
- AP identity and uptime.
- Controller assignment.
- Group/profile relationship if visible.
- Registration/discovery stage: IP, discovery, tunnel/heartbeat, config download, BSS advertisement.
- Findings, likely cause, and next safe command to run.
"""


def aos8_wlan_profile_review(config_path: str = "/md") -> str:
    """Guide a read-only WLAN/profile configuration review."""
    return f"""
Review AOS8 WLAN/profile configuration at config_path "{config_path}".

Workflow:
1. Call aos8_get_ap_group_config with config_path="{config_path}".
2. Call aos8_get_virtual_ap_profiles with config_path="{config_path}".
3. Call aos8_get_ssid_profiles with config_path="{config_path}".
4. Call aos8_get_aaa_profiles with config_path="{config_path}".
5. Build a WLAN map: AP group -> VAP -> SSID profile -> ESSID -> AAA profile -> VLAN -> forward mode -> security.

Output:
- A WLAN map table.
- AP groups and their bound VAPs.
- SSID/security summary.
- AAA/server-group summary.
- Highlight mismatches such as APs in a group that only has a management VAP.
- Redact passphrases, keys, secrets, and license-like values.
"""


def aos8_controller_failover_check() -> str:
    """Guide a conductor and managed-device redundancy check."""
    return """
Check AOS8 controller/conductor redundancy and failover readiness.

Workflow:
1. Call aos8_get_managed_devices.
2. Call aos8_get_switches if raw config-sync fields are needed.
3. Call aos8_get_ap_summary to see active and standby controller assignment for APs.
4. Call aos8_get_cluster_status and explain empty successful responses as "no LC cluster output from this context" unless other evidence says otherwise.

Output:
- Conductor and standby status.
- Managed device status and config sync state.
- AP active/standby controller distribution.
- Any failover concerns and next safe checks.
"""


def aos8_ap_group_profile_map(config_path: str = "/md") -> str:
    """Guide mapping AP groups to WLAN profiles."""
    return f"""
Map AOS8 AP groups to their WLAN/profile bindings at config_path "{config_path}".

Workflow:
1. Call aos8_get_ap_summary to see live AP group membership.
2. Call aos8_get_ap_group_config with config_path="{config_path}".
3. Call aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with the same config_path.
4. Cross-reference live AP groups against configured AP groups and VAPs.

Output:
- Live AP group membership.
- AP group -> VAP bindings.
- VAP -> SSID/AAA/VLAN/forward-mode bindings.
- Any group present in live AP inventory but missing from queried config path.
"""


def aos8_safe_show_command(command: str) -> str:
    """Guide safe use of raw AOS8 show commands."""
    return f"""
Run and summarize this AOS8 show command: "{command}".

Rules:
- Only call aos8_show_command if the command starts with "show ".
- Do not run configuration, write, reload, copy, debug write, or destructive commands.
- Summarize the useful fields in tables.
- If output contains secrets, passphrases, keys, license keys, SNMP communities, or ciphertext, redact them.
"""


def aos8_troubleshoot_wlan(config_path: str = "/md", ssid: str = "") -> str:
    """Guide WLAN troubleshooting from profile config to live state."""
    target = ssid or "<all WLANs>"
    return f"""
You are troubleshooting AOS8 WLAN service for SSID/ESSID: {target}, using config_path "{config_path}".

Workflow:
1. Call aos8_get_ap_summary to see live AP groups and controller assignment.
2. Call aos8_get_ap_group_config, aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with config_path="{config_path}".
3. Build the chain AP group -> Virtual AP -> SSID profile -> ESSID -> AAA profile -> VLAN -> forward mode.
4. If ssid is provided, filter the chain to the matching ESSID, SSID profile, or VAP name.
5. Call aos8_show_command for "show ap essid" and "show ap bss-table" to compare configured WLANs with advertised BSS state.

Expert checks:
- APs are in an AP group that actually references the target VAP.
- VAP is enabled and references the expected SSID and AAA profiles.
- SSID security mode matches the intended design.
- VLAN and forward mode are appropriate for guest/internal/IoT/management use.
- Client connectivity follows phases: 802.11 negotiation, authentication/encryption, IP addressing, policy/role, and network access.
- Empty BSS/ESSID output is called out as live-state evidence, not silently ignored.

Output:
- WLAN chain table.
- Live advertisement/client evidence.
- Findings and likely fault domain: AP group, VAP, SSID profile, AAA, VLAN, or controller context.
- Next safe read-only checks.
- Redact passphrases and secrets.
"""


def aos8_review_ap_group(config_path: str = "/md", ap_group: str = "") -> str:
    """Guide an expert review of one AP group or all AP groups."""
    target = ap_group or "<all AP groups>"
    return f"""
Review AOS8 AP group configuration for: {target}, using config_path "{config_path}".

Workflow:
1. Call aos8_get_ap_summary to find live APs using the AP group.
2. Call aos8_get_ap_group_config with config_path="{config_path}".
3. Call aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with config_path="{config_path}".
4. For the target AP group, list VAP bindings and supporting profiles.

Expert checks:
- AP group exists at this config path.
- Live APs are assigned to the expected AP group.
- AP group has the intended VAPs.
- Ethernet port profiles are expected, especially non-default wired profiles.
- AP system, multizone, Airslice, radio, regulatory, and RF profiles are noted when non-default.

Output:
- AP group summary.
- Live AP membership.
- VAP/profile binding table.
- Non-default profile highlights.
- Missing or inherited settings that deserve follow-up.
"""


def aos8_security_review(config_path: str = "/md") -> str:
    """Guide a read-only WLAN security review."""
    return f"""
Perform a read-only AOS8 WLAN security review at config_path "{config_path}".

Workflow:
1. Call aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with config_path="{config_path}".
2. Build a WLAN table with ESSID, security/opmode, AAA profile, server group, default roles, VLAN, and forward mode.
3. Identify open, enhanced-open, WPA2-PSK, WPA3, MPSK, 802.1X, MAC-auth, and captive-portal style profiles where visible.
4. Check whether RADIUS accounting, interim accounting, CoA/RFC3576 clients, DHCP enforcement, and downloadable roles are configured.

Output:
- Security posture table by WLAN.
- Strong points.
- Risks or review items, ranked high/medium/low.
- Exact evidence from config object fields.
- Redact passphrases, keys, shared secrets, and license-like strings.
"""


def aos8_hardening_review(config_path: str = "/md") -> str:
    """Guide a read-only AOS8 hardening review."""
    return f"""
Perform a read-only AOS8 hardening review using config_path "{config_path}" where configuration hierarchy matters.

Workflow:
1. Establish software and topology posture with aos8_get_version, aos8_get_managed_devices, and aos8_get_health_summary.
2. Review WLAN/security posture with aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles using config_path="{config_path}".
3. Use safe show commands for management-plane evidence where supported:
   - "show web-server profile"
   - "show crypto-local pki trustedCAs"
   - "show aaa authentication-server all"
   - "show log security all"
   - "show snmp trap-host"
   - "show running-config | include ssh|web-server|snmp|ntp|syslog|firewall"
4. Check for hardening domains: management access scope, TLS protocol/cipher posture, SSH posture, admin AAA, RADIUS/TACACS usage, SNMP exposure, logging/syslog/accounting, NTP/DNS, certificates, control-plane firewall/ACL posture, and unnecessary services.
5. For scanner findings such as QOTD/17 or legacy TLS, collect live evidence first and clearly separate possible false positives from confirmed exposure.

Output:
- Hardening posture table by domain.
- Evidence collected and commands/tools used.
- High/medium/low review items.
- Suggested next read-only checks.
- Do not prescribe config changes as commands unless the user explicitly asks.
- Redact secrets, passphrases, SNMP communities, license keys, private keys, and certificate material.
"""


def aos8_compare_config_paths(path_a: str = "/md", path_b: str = "/md/SE") -> str:
    """Guide comparison of inherited/effective config across two hierarchy paths."""
    return f"""
Compare AOS8 WLAN/profile configuration between "{path_a}" and "{path_b}".

Workflow:
1. For both paths, call aos8_get_ap_group_config, aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles.
2. Compare profile names present at each path.
3. Compare AP group VAP bindings, SSID ESSIDs/security, VAP VLAN/forward mode, and AAA server groups/default roles.
4. Separate inherited/default settings from explicit settings when the _flags field exposes that detail.

Output:
- Added/removed/changed profile summary.
- Side-by-side WLAN map.
- Inheritance observations.
- Which path best explains live AP group membership from aos8_get_ap_summary.
- Redact secrets.
"""


def aos8_client_connectivity_review(config_path: str = "/md", client_mac: str = "") -> str:
    """Guide client connectivity investigation using live state and WLAN profiles."""
    target = client_mac or "<all clients>"
    return f"""
Investigate AOS8 client connectivity for: {target}, using config_path "{config_path}".

Workflow:
1. Call aos8_get_clients.
2. If client_mac is provided, call aos8_show_command with "show user-table | include {target}" only if the showcommand API supports the exact command; otherwise explain and use aos8_get_clients output.
3. Call aos8_get_ap_summary to identify AP groups and controller assignment.
4. Call aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with config_path="{config_path}" to understand WLAN authentication and roles.
5. If clients are empty, call that out and focus on WLAN/BSS/AP evidence.

Expert checks:
- Client appears in user table.
- WLAN/SSID exists and is advertised.
- AAA profile points to expected server group/default role.
- VLAN and forward mode match the design.
- AP group includes the target WLAN VAP.
- Walk the client phases in order: 802.11 negotiation, authentication/encryption, IP address, policy/role, and network access.
- If the client is absent from the user table, use WLAN/AP/BSS evidence and suggest monitoring/discovery commands rather than assuming authentication failure.
- For role/VLAN issues, check initial role, user-derived role, server-derived role, Aruba VSAs/RADIUS attributes, default authentication role, and whether the derived role exists.

Output:
- Client state evidence.
- WLAN/profile path likely used by the client.
- Most likely failure domain.
- Next safe read-only checks.
- Redact secrets.
"""


def aos8_structured_troubleshooting(issue: str = "") -> str:
    """Guide a structured Aruba mobility troubleshooting triage."""
    target = issue or "<reported issue>"
    return f"""
Use a structured Aruba AOS8 troubleshooting approach for: {target}.

Workflow:
1. Scope the blast radius before forming a conclusion:
   - one client or many clients
   - one AP or many APs
   - one SSID or many SSIDs
   - one location/AP group/controller or multiple
   - new issue or long-standing issue
   - recent change in config, code, RF, DHCP, RADIUS, VLAN, routing, or certificates
2. Classify the problem zone:
   - client issue
   - infrastructure issue: AP, controller, tunnel, license, capacity, reachability
   - WLAN function issue: SSID/VAP/AAA/VLAN/role/RADIUS/policy
3. Collect live evidence with aos8_get_health_summary, aos8_get_managed_devices, aos8_get_ap_summary, and targeted aos8_show_command calls.
4. For WLAN/client issues, map evidence across the five client phases: 802.11 negotiation, authentication/encryption, IP addressing, policy/role, and network access.
5. Use config-object GET tools only for read-only profile evidence.

Output:
- Problem scope.
- Fault zone.
- Evidence table.
- Most likely fault domain.
- Next safe read-only checks.
- Redaction for secrets, keys, passphrases, and license-like values.
"""


def aos8_configuration_flow_review(config_path: str = "/md") -> str:
    """Guide a hierarchy-aware AOS8 configuration-flow review."""
    return f"""
Review AOS8 configuration flow at config_path "{config_path}" using a hierarchy-aware approach.

Workflow:
1. Establish the hierarchy scope first: Mobility Conductor, managed-device node, group path, and whether settings are inherited/default or explicit.
2. Call aos8_get_managed_devices and aos8_get_ap_summary to confirm live controller/AP state before interpreting config.
3. Call aos8_get_ap_group_config, aos8_get_virtual_ap_profiles, aos8_get_ssid_profiles, and aos8_get_aaa_profiles with config_path="{config_path}".
4. Build the configuration chain:
   hierarchy path -> AP group -> Virtual AP -> SSID profile -> ESSID/security -> AAA profile -> role/server group -> VLAN/forward mode.
5. Validate the live service with safe show commands such as "show ap essid", "show ap bss-table", and "show user-table".

Expert checks:
- Correct hierarchy path is being queried.
- AP group used by live APs exists at the queried path.
- Named VLAN/VLAN binding is present where the VAP expects it.
- AAA profile maps to expected default role, server group, accounting, and CoA/RFC3576 behavior.
- Inherited/default values are not mistaken for explicit local configuration.
- Config exists and live service evidence also exists.

Output:
- Configuration-flow diagram as a table.
- Inheritance/default observations.
- Gaps between config intent and live operational state.
- Next safe validation commands.
- Redact passphrases, keys, shared secrets, and license-like values.
"""


PROMPTS: tuple[Callable[..., str], ...] = (
    aos8_health_overview,
    aos8_troubleshoot_ap,
    aos8_wlan_profile_review,
    aos8_controller_failover_check,
    aos8_ap_group_profile_map,
    aos8_safe_show_command,
    aos8_troubleshoot_wlan,
    aos8_review_ap_group,
    aos8_security_review,
    aos8_hardening_review,
    aos8_compare_config_paths,
    aos8_client_connectivity_review,
    aos8_structured_troubleshooting,
    aos8_configuration_flow_review,
)


def register_prompts(mcp: FastMCP) -> None:
    """Register all AOS8 expert workflow prompts with the MCP server."""
    for prompt in PROMPTS:
        mcp.prompt()(prompt)
