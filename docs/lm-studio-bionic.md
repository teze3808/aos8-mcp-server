# LM Studio Bionic Setup

This procedure connects LM Studio Bionic to a local `aos8-mcp-server` process.
It validates each layer separately so a controller problem is not confused with
an MCP installation problem or a model interpretation error.

## Connection Layers

```text
Bionic model -> LM Studio MCP host -> local stdio process -> AOS8 REST API
```

Treat each layer as a separate checkpoint. A green MCP status proves only that
LM Studio started the local process and discovered its tools. It does not prove
that the process can reach or authenticate to the controller.

## 1. Prepare and Validate the Server

From the repository directory:

```bash
command -v uv
uv sync --locked
cp .env.example .env  # only when .env does not already exist
```

Edit `.env` and confirm the endpoint before opening LM Studio:

```env
AOS8_BASE_URL=https://aos8-controller.example.com:4343
AOS8_USERNAME=your-username
AOS8_PASSWORD=your-password
AOS8_VERIFY_SSL=true
AOS8_REQUEST_TIMEOUT=30
```

Keep `.env` out of source control. Use `AOS8_CA_BUNDLE` for an internal CA.
Set `AOS8_VERIFY_SSL=false` only for a temporary lab connection with a
self-signed certificate.

Run the preflight check:

```bash
uv run aos8-mcp-check
```

Do not proceed until it returns `"status": "ok"`, the intended target, and an
AOS version. This command uses the same `.env`, login API, and `show version`
path as the MCP connection test.

## 2. Add the MCP Server in Bionic

In LM Studio, open **Settings -> Connected Apps -> Custom MCP**.

- Name: `aos8-mcp-server`
- Connection: **On this computer**
- Command: the absolute path returned by `command -v uv`

Add these as four separate arguments, in this order:

```text
run
--directory
/absolute/path/to/aos8-mcp-server
aos8-mcp-server
```

Do not enter the four arguments as one combined line. If LM Studio stores them
as a single array item, `uv` treats the whole line as one invalid argument and
the MCP entry fails with `-32000: Connection closed`.

When `.env` is in the repository, credentials do not need to be duplicated in
LM Studio. `uv --directory` starts the server in that directory, allowing the
server to load `.env`.

For a private controller address, enable **LM Studio** or **Bionic** under
**macOS System Settings -> Privacy & Security -> Local Network**. If a proxy is
configured on the Mac, add this MCP environment variable with the appropriate
controller address:

```text
NO_PROXY=10.0.0.10,localhost,127.0.0.1
```

After changing `.env`, arguments, environment variables, or Local Network
permission, fully restart LM Studio. Toggling the MCP entry may leave an old
process or cached settings in place.

## 3. Validate in Bionic

Use a new chat and validate in this order.

### Checkpoint A: local tool execution

```text
Call aos8_list_command_targets. Return the raw tool result only.
```

Expected: `status` is `ok`, the base URL matches `.env`, and the default target
is listed. This tool does not contact the controller.

### Checkpoint B: controller connection

```text
Call aos8_test_connection with target_node omitted. Return the raw tool result
only. Do not interpret, retry, or substitute values.
```

Expected: `status` is `ok`, `data.ok` is `true`, and `show version` returns an
AOS version. Omit `target_node` to use the default endpoint; do not pass the
literal name `default`.

### Checkpoint C: operational data

```text
Call aos8_get_health_summary with target_node omitted. Preserve status, target,
warnings, issues, and findings verbatim before summarizing. Do not infer that
an empty client or tunnel table represents the entire environment.
```

Live client and tunnel tables can depend on controller context. An empty table
from a Mobility Conductor does not prove there are no clients or tunnels. Use
`aos8_get_node_hierarchy` and configure `AOS8_NODE_TARGETS` before making a
managed-device-specific conclusion.

## Small-Model Guidance

Qwen 3 4B can use these tools, but 25 tool definitions and large raw results can
reduce its reliability. Use a low temperature, a context window of at least
16K, one tool call at a time, and explicit instructions to preserve raw fields.
Treat Bionic's prose as a summary, not as the authoritative tool result.

Recommended instruction:

```text
Use aos8-mcp-server for AOS8 facts. Call one tool at a time. Never claim a tool
ran unless a tool result is present. Preserve status, target, warnings, issues,
and errors exactly. Do not invent missing values. Omit target_node for the
default endpoint. Empty live tables are context-specific evidence, not proof
that the whole network has no clients or tunnels.
```

## Failure Guide

| Symptom | Layer | Likely cause | Action |
| --- | --- | --- | --- |
| `-32000: Connection closed` | LM Studio -> stdio | Command arguments were combined, executable path is wrong, or startup validation failed | Use an absolute `uv` path and four separate arguments; run `uv run aos8-mcp-check` |
| 25 tools ready, but local target-list call fails | Bionic MCP host | Stale or faulty MCP process | Fully restart LM Studio and retry in a new chat |
| Target-list works, connection test times out | MCP process -> AOS8 | Wrong `.env` endpoint, Local Network permission, proxy, routing, or controller availability | Compare target to `.env`, run preflight, enable Local Network access, and set `NO_PROXY` if needed |
| Bionic waits about 60 seconds and returns `-32001` | Bionic MCP host | Its tool-call deadline expired before the server's configured retries completed | Fix reachability first; temporarily reduce request timeout/retries only for diagnosis |
| Tool succeeds but Bionic reports different ports or values | Model interpretation | Small model transcribed or inferred values incorrectly | Inspect the tool card and request raw output before interpretation |
| Empty client table at the conductor | AOS8 query context | Live state may reside on a managed device | Discover hierarchy and configure named direct-node targets |

## What Went Wrong in the Initial Setup

The observed setup encountered independent failures:

1. LM Studio stored all `uv` arguments as one string, so `uv` exited and LM
   Studio reported `-32000: Connection closed`.
2. The repository `.env` still pointed to an old controller address that timed
   out, while the working client configuration used a different address.
3. After correcting `.env`, Bionic needed its MCP process restarted and private
   network access available. Its 60-second host timeout surfaced as `-32001`,
   even though the same MCP command worked from Terminal.
4. Qwen 3 4B sometimes inferred details in prose, including target reachability
   and port values, instead of copying the raw tool result exactly.
5. The server emitted an unconditional direct-target warning. That warning was
   corrected so it appears only when named direct-node targets are configured.

The successful sequence was: validate `.env` outside LM Studio, use separate
stdio arguments, restart the host, validate a local-only MCP tool, validate the
controller connection, and only then run operational summaries.
