# aos8-mcp-server

Community MCP server for Aruba AOS8 Mobility Conductor and Mobility Controller environments. It exposes safe AOS8 operational data, configuration-object reads, discovery, and plan-only configuration workflows to AI assistants through the Model Context Protocol.

> Warning
>
> This is an unofficial community project and is not an HPE-supported product.
> Review your organization's device, credential, and AI data-handling policies before connecting any network system to an AI assistant.
> This server is read-only by default. Plan-only configuration tools can describe proposed AOS8 API requests, but they do not send writes or save configuration.

## Overview

`aos8-mcp-server` wraps ArubaOS 8 REST APIs and exposes them as MCP tools and guided prompts. Once configured, an AI assistant can answer questions like:

- "Show all APs in my AOS8 environment."
- "Review AOS8 hardening for `/md/Example-Site`."
- "Show all WLAN and profile configuration under `/md/Example-Site`."
- "Troubleshoot why clients cannot connect to `LAB-CORP-WIFI`."
- "Plan a new SSID called `LAB-TEST-WIFI` under `/md/Example-Site`."
- "List native AOS8 configuration objects available from this controller."

## Safety Model

This project intentionally separates operational reads from configuration changes.

| Stage | Status | Behavior |
| --- | --- | --- |
| Stage 1 | Implemented | Read-only show commands and config-object GET |
| Stage 2 | Implemented | Plan-only configuration payloads and redacted diffs |
| Stage 3 | Not implemented | Confirmed configuration writes |
| Stage 4 | Not implemented | Explicit save / `write_memory` |

The current server does not expose POST writes or `write_memory`. The plan-only tool may show what a future POST request could look like, but it does not send that request.

## APIs Used

The server currently uses these AOS8 REST APIs:

```text
POST /v1/api/login
POST /v1/api/logout
GET  /v1/configuration/showcommand
GET  /v1/configuration/object
GET  /v1/configuration/container
GET  /v1/configuration/object/<object_name>
```

## Tool Categories

### Health and Inventory

| Tool | Description |
| --- | --- |
| `aos8_test_connection` | Log in and run `show version` |
| `aos8_get_version` | Return AOS8 version information |
| `aos8_get_switches` | Return controller / managed-device inventory |
| `aos8_get_managed_devices` | Return normalized controller / managed-device inventory |
| `aos8_get_access_points` | Return AP database |
| `aos8_get_ap_summary` | Return normalized AP inventory and AP health summary |
| `aos8_get_health_summary` | Return a concise health summary across controllers, APs, clients, and tunnels |
| `aos8_get_clients` | Return wireless user table |
| `aos8_get_tunnels` | Return datapath tunnel information |
| `aos8_get_license_summary` | Return license information with license keys redacted |
| `aos8_get_cluster_status` | Return cluster membership information |

### Show Commands

| Tool | Description |
| --- | --- |
| `aos8_show_command` | Run an arbitrary read-only `show ...` command |

Only commands beginning with `show ` are accepted.

### Configuration Reads

| Tool | Description |
| --- | --- |
| `aos8_get_config_object` | Return a read-only configuration object by object name and config path |
| `aos8_get_ap_group_config` | Return AP group configuration |
| `aos8_get_virtual_ap_profiles` | Return Virtual AP profile configuration |
| `aos8_get_ssid_profiles` | Return SSID profile configuration |
| `aos8_get_aaa_profiles` | Return AAA profile configuration |

### Discovery

| Tool | Description |
| --- | --- |
| `aos8_list_config_objects` | Discover native AOS8 configuration object names exposed by the controller |
| `aos8_list_config_containers` | Discover native AOS8 configuration container names exposed by the controller |

Discovery results are cached in the MCP process. Pass `refresh=true` to force a new controller read.

### Plan-Only Configuration

| Tool | Description |
| --- | --- |
| `aos8_plan_config_object_change` | Build a redacted plan-only native config-object POST payload and before/after diff without writing |

This tool returns `writes_executed=false` and `save_executed=false`.

## Guided Prompts

Prompt text lives in `src/aruba_aos8_mcp/prompts.py`. Edit that file when tailoring expert workflows, then run `uv run pytest` and `uv run ruff check`.

| Prompt | Natural-language use |
| --- | --- |
| `aos8_health_overview` | "Give me an AOS8 health overview." |
| `aos8_troubleshoot_ap` | "Troubleshoot AP `AP-LAB-01`." |
| `aos8_wlan_profile_review` | "Show WLAN/profile configuration under `/md/Example-Site`." |
| `aos8_controller_failover_check` | "Check controller and AP failover readiness." |
| `aos8_ap_group_profile_map` | "Map AP groups to VAP, SSID, AAA, VLAN, and forward mode." |
| `aos8_safe_show_command` | "Run and summarize this safe show command." |
| `aos8_troubleshoot_wlan` | "Troubleshoot clients connecting to `LAB-CORP-WIFI`." |
| `aos8_review_ap_group` | "Review AP group `LAB-AP-GROUP`." |
| `aos8_security_review` | "Review WLAN security posture." |
| `aos8_hardening_review` | "Review AOS8 hardening for `/md/Example-Site`." |
| `aos8_compare_config_paths` | "Compare `/md` and `/md/Example-Site` profile configuration." |
| `aos8_config_change_plan` | "Plan a new SSID without writing config." |
| `aos8_client_connectivity_review` | "Investigate a client by MAC address." |
| `aos8_structured_troubleshooting` | "Use a structured troubleshooting workflow for a reported issue." |
| `aos8_configuration_flow_review` | "Review config flow from hierarchy path to AP group, VAP, SSID, AAA, role, VLAN, and live state." |

## Example Questions

Try these in an MCP-capable AI client:

```text
Show all AOS8 APs.
Show controller and managed-device status.
Show all WLAN/profile configuration under /md/Example-Site.
Review AOS8 hardening for /md/Example-Site.
Troubleshoot why clients cannot connect to LAB-CORP-WIFI.
Compare WLAN profiles between /md and /md/Example-Site.
Plan a new SSID called LAB-TEST-WIFI under /md/Example-Site.
List native AOS8 config objects.
Run show switches on AOS8.
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

Edit `.env` with your AOS8 controller details:

```env
AOS8_BASE_URL=https://aos8-controller.example.com:4343
AOS8_USERNAME=your-username
AOS8_PASSWORD=your-password
AOS8_VERIFY_SSL=false
AOS8_REQUEST_TIMEOUT=30
```

Do not commit `.env`.

## Run Locally

```bash
uv run aos8-mcp-server
```

For MCP inspector testing:

```bash
uv run mcp dev src/aruba_aos8_mcp/server.py
```

## MCP Client Configuration

### Codex

Add this to your Codex MCP config after replacing the placeholders:

```toml
[mcp_servers.aos8_mcp_server]
command = "uv"
args = ["run", "--directory", "/path/to/aos8-mcp-server", "aos8-mcp-server"]
startup_timeout_sec = 30

[mcp_servers.aos8_mcp_server.env]
AOS8_BASE_URL = "https://aos8-controller.example.com:4343"
AOS8_USERNAME = "your-username"
AOS8_PASSWORD = "your-password"
AOS8_VERIFY_SSL = "false"
AOS8_REQUEST_TIMEOUT = "30"
```

Restart the MCP client after editing the config.

### Generic Stdio MCP Client

Use this command from the project directory:

```bash
uv run aos8-mcp-server
```

Pass the `AOS8_*` environment variables through your MCP client config.

## Dev Setup

Run tests and lint:

```bash
uv run pytest
uv run ruff check
```

## Publish To Your Own GitHub Repo

Create an empty GitHub repository, then run:

```bash
git add .
git commit -m "Initial aos8-mcp-server"
git branch -M main
git remote add origin git@github.com:YOUR-ORG/aos8-mcp-server.git
git push -u origin main
```

## Notes

- AOS8 config object names are native API object names, not always CLI names.
- Live state is usually best collected through the showcommand API.
- Configuration intent is usually best collected through config-object GET.
- Plan-only output is for operator review and schema validation before any future write capability is considered.
