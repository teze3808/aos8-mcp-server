# aos8-mcp-server

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/linting-Ruff-purple)
![MCP](https://img.shields.io/badge/MCP-server-0b7f5f)
![ArubaOS](https://img.shields.io/badge/ArubaOS-8-orange)
![Status](https://img.shields.io/badge/status-unofficial%20community%20project-lightgrey)

Community MCP server for Aruba AOS8 Mobility Conductor and Mobility Controller environments. It helps HPE Aruba Networking customers, partners, and lab teams inspect AOS8 operational state, read configuration objects, discover native API objects, and prepare plan-only configuration payloads through the Model Context Protocol.

> Warning
>
> This is an unofficial and unsupported community project, not an HPE-supported product.
> It is not affiliated with, endorsed by, or maintained by Hewlett Packard Enterprise or HPE Aruba Networking.
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

## Architecture

![Animated AOS8 MCP request flow](assets/aos8-mcp-flow.svg)

## Operational Scope

This project intentionally separates operational visibility from configuration execution.

- Implemented: read-only show commands through the AOS8 showcommand API.
- Implemented: read-only configuration object GET for native AOS8 objects.
- Implemented: plan-only configuration payloads with redacted before/after diffs.
- Not implemented: configuration POST writes, reloads, or `write_memory`.

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
Show AOS8 version and controller uptime.
Summarize AOS8 health across controllers, APs, clients, and tunnels.
Show all managed devices and their config sync status.
Show all APs grouped by AP group and model.
Show current wireless clients.
Show AOS8 license summary.
Show cluster status.
Run show switches on AOS8.
Run show ap database on AOS8.

Show all WLAN/profile configuration under /md/Example-Site.
Map AP groups to VAP, SSID, AAA, VLAN, and forward mode under /md/Example-Site.
Show SSID profiles under /md/Example-Site.
Show AAA profiles under /md/Example-Site.
Show AP group configuration for LAB-AP-GROUP.
Compare WLAN profiles between /md and /md/Example-Site.
List native AOS8 config objects.
List native AOS8 config containers.

Review AOS8 hardening for /md/Example-Site.
Review WLAN security posture for /md/Example-Site.
Troubleshoot why clients cannot connect to LAB-CORP-WIFI.
Troubleshoot AP AP-LAB-01.
Investigate client aa:bb:cc:dd:ee:ff.
Use structured troubleshooting for guest clients cannot connect.

Plan a new SSID called LAB-TEST-WIFI under /md/Example-Site.
Plan changing the ESSID of LAB-CORP-WIFI without writing config.
Create a plan-only payload to add a VAP to LAB-AP-GROUP.
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

### Claude Desktop

Add this to your Claude Desktop MCP configuration after replacing the placeholders:

```json
{
  "mcpServers": {
    "aos8-mcp-server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/aos8-mcp-server",
        "aos8-mcp-server"
      ],
      "env": {
        "AOS8_BASE_URL": "https://aos8-controller.example.com:4343",
        "AOS8_USERNAME": "your-username",
        "AOS8_PASSWORD": "your-password",
        "AOS8_VERIFY_SSL": "false",
        "AOS8_REQUEST_TIMEOUT": "30"
      }
    }
  }
}
```

Restart Claude Desktop after editing the config.

### Claude Code

Claude Code can add a stdio MCP server from JSON:

```bash
claude mcp add-json aos8-mcp-server '{
  "type": "stdio",
  "command": "uv",
  "args": ["run", "--directory", "/path/to/aos8-mcp-server", "aos8-mcp-server"],
  "env": {
    "AOS8_BASE_URL": "https://aos8-controller.example.com:4343",
    "AOS8_USERNAME": "your-username",
    "AOS8_PASSWORD": "your-password",
    "AOS8_VERIFY_SSL": "false",
    "AOS8_REQUEST_TIMEOUT": "30"
  }
}'
```

### Visual Studio Code With GitHub Copilot

VS Code stores MCP server configuration in `mcp.json`, either in your workspace as `.vscode/mcp.json` or in your user profile. Add a server entry like this:

```json
{
  "servers": {
    "aos8-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/aos8-mcp-server",
        "aos8-mcp-server"
      ],
      "env": {
        "AOS8_BASE_URL": "https://aos8-controller.example.com:4343",
        "AOS8_USERNAME": "your-username",
        "AOS8_PASSWORD": "your-password",
        "AOS8_VERIFY_SSL": "false",
        "AOS8_REQUEST_TIMEOUT": "30"
      }
    }
  }
}
```

Save the file and reload/restart the MCP server from VS Code if prompted.

### Generic Stdio MCP Client

Use this command from the project directory:

```bash
uv run aos8-mcp-server
```

Pass the `AOS8_*` environment variables through your MCP client config.

## Notes

- AOS8 config object names are native API object names, not always CLI names.
- Live state is usually best collected through the showcommand API.
- Configuration intent is usually best collected through config-object GET.
- Plan-only output is for operator review and schema validation before any future write capability is considered.
- This project is intended as a community starting point for lab, demo, validation, and operational-assist workflows. Use appropriate review and change-control before adapting it for production operations.

## Client Documentation

- [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp)
- [VS Code MCP configuration reference](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)
