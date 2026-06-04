# aos8-mcp-server

Read-only MCP server for Aruba AOS8 Mobility Conductor, Mobility Controller, and standalone controller monitoring.

The first version focuses on safe operational inspection through AOS8 login and `showcommand` APIs. Configuration writes are intentionally not included yet.

## Tools

- `aos8_test_connection` - log in and run `show version`
- `aos8_show_command` - run an arbitrary read-only `show ...` command
- `aos8_get_version` - return AOS8 version information
- `aos8_get_switches` - return controller / managed-device inventory
- `aos8_get_access_points` - return AP database
- `aos8_get_clients` - return wireless user table
- `aos8_get_tunnels` - return datapath tunnel information
- `aos8_get_license_summary` - return license information
- `aos8_get_cluster_status` - return cluster membership information
- `aos8_get_managed_devices` - return normalized controller / managed-device inventory
- `aos8_get_ap_summary` - return normalized AP inventory and AP health summary
- `aos8_get_health_summary` - return a concise health summary across controllers, APs, clients, and tunnels
- `aos8_get_config_object` - return a read-only configuration object by object name and config path
- `aos8_list_config_objects` - discover native AOS8 configuration object names exposed by the controller
- `aos8_list_config_containers` - discover native AOS8 configuration container names exposed by the controller
- `aos8_plan_config_object_change` - build a redacted plan-only native config-object POST payload and before/after diff without writing
- `aos8_get_ap_group_config` - return AP group configuration
- `aos8_get_virtual_ap_profiles` - return Virtual AP profile configuration
- `aos8_get_ssid_profiles` - return SSID profile configuration
- `aos8_get_aaa_profiles` - return AAA profile configuration

## Prompts

Prompt text lives in `src/aruba_aos8_mcp/prompts.py`. Edit that file when tailoring expert workflows, then run `uv run pytest` and `uv run ruff check`.

- `aos8_health_overview` - guided health summary for conductors, managed devices, APs, clients, and tunnels
- `aos8_troubleshoot_ap` - AP troubleshooting workflow for one AP or all APs
- `aos8_wlan_profile_review` - WLAN/profile review using config-object GET
- `aos8_controller_failover_check` - conductor, managed-device, and AP standby assignment review
- `aos8_ap_group_profile_map` - map AP groups to VAP, SSID, AAA, VLAN, and forward-mode bindings
- `aos8_safe_show_command` - safe raw `show ...` command helper with redaction guidance
- `aos8_troubleshoot_wlan` - WLAN troubleshooting from AP group to VAP, SSID, AAA, VLAN, and BSS state
- `aos8_review_ap_group` - expert AP group review with live AP membership and non-default profile highlights
- `aos8_security_review` - read-only WLAN security posture review
- `aos8_hardening_review` - read-only AOS8 management-plane and WLAN hardening review
- `aos8_compare_config_paths` - compare inherited/effective WLAN profiles across two hierarchy paths
- `aos8_config_change_plan` - plan-only workflow for preparing native config-object changes without sending writes
- `aos8_client_connectivity_review` - client connectivity workflow combining user table, APs, and WLAN profile config
- `aos8_structured_troubleshooting` - expert triage workflow for scoping, fault-domain classification, and phased evidence collection
- `aos8_configuration_flow_review` - hierarchy-aware review from config path through AP group, VAP, SSID, AAA, role, VLAN, and live validation

Example prompts to try in an MCP client:

```text
Use the aos8_health_overview prompt
Use the aos8_wlan_profile_review prompt with config_path=/md/SE
Use the aos8_troubleshoot_ap prompt for SE-AP505-AOS8
Use the aos8_troubleshoot_wlan prompt with config_path=/md/SE and ssid=SE-MGMT-AOS8
Use the aos8_security_review prompt with config_path=/md/SE
Use the aos8_hardening_review prompt with config_path=/md/SE
Use the aos8_compare_config_paths prompt with path_a=/md and path_b=/md/SE
Use the aos8_config_change_plan prompt with object_name=ssid_prof, config_path=/md/SE, and change_goal="rename an ESSID"
Use the aos8_structured_troubleshooting prompt with issue="guest clients cannot connect"
Use the aos8_configuration_flow_review prompt with config_path=/md/SE
```

## Setup

Install `uv` if you do not already have it, then run:

```bash
uv sync
```

Create your local env file:

```bash
cp .env.example .env
```

Edit `.env` with your AOS8 controller details.

## Run Locally

```bash
uv run aos8-mcp-server
```

For MCP inspector testing:

```bash
uv run mcp dev src/aruba_aos8_mcp/server.py
```

## Codex Config

Add this to `/Users/vincent/.codex/config.toml` after replacing the placeholders:

```toml
[mcp_servers.aruba_aos8]
command = "uv"
args = ["run", "--directory", "/Users/vincent/Documents/aos8-mcp-server", "aos8-mcp-server"]
startup_timeout_sec = 30

[mcp_servers.aruba_aos8.env]
AOS8_BASE_URL = "https://YOUR-AOS8-MM:4343"
AOS8_USERNAME = "YOUR_USERNAME"
AOS8_PASSWORD = "YOUR_PASSWORD"
AOS8_VERIFY_SSL = "false"
AOS8_REQUEST_TIMEOUT = "30"
```

Restart Codex after editing the config.

## Push To GitHub

Create an empty GitHub repository, then run:

```bash
git add .
git commit -m "Initial aos8-mcp-server"
git branch -M main
git remote add origin git@github.com:YOUR-USER/aos8-mcp-server.git
git push -u origin main
```

## Safety

This MCP only accepts commands beginning with `show `. It does not expose configuration writes or `write memory`.

Configuration object tools are read-only and use `GET /v1/configuration/object/<object_name>`.
Discovery tools are read-only and use `GET /v1/configuration/object` and `GET /v1/configuration/container`.
Discovery results are cached in the MCP process; pass `refresh=true` to force a new controller read.
Plan-only tools may describe a proposed `POST /v1/configuration/object/<object_name>` request, but they do not send it.
They do not expose POST or `write_memory`.
