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
