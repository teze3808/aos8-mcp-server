# Operations Runbook

## Start and Validate

1. Confirm the local `.env` or MCP client configuration contains the intended target.
2. Verify TLS with the system trust store or `AOS8_CA_BUNDLE`.
3. Start with `uv run aos8-mcp-server` or the configured MCP host.
4. Run `aos8_test_connection`, then `aos8_get_health_summary`.
5. Confirm normalized AP, client, and WLAN summaries before relying on analysis findings.

## Common Failures

| Symptom | Check | Safe response |
| --- | --- | --- |
| TLS verification failure | Certificate name, expiry, and CA chain | Install the correct CA chain; do not disable TLS verification in production-like use |
| Unknown target | `AOS8_NODE_TARGETS` JSON and target alias | Correct the alias or endpoint; never fall back silently |
| Command blocked | Built-in policy and additional prefixes | Use an intent-level tool or review one narrow prefix |
| Config object/path blocked | Allowed object and path-root settings | Confirm business need before expanding scope |
| HTTP 429/5xx | Controller health and retry audit events | Reduce polling; wait for bounded backoff; do not create an unbounded retry loop |
| Truncated result | `_meta.truncated` and configured size limit | Narrow the target/filter instead of increasing limits first |
| Empty live table | Query context, managed-device target, and AP/WLAN state | Treat it as evidence, not proof that the service is healthy or unhealthy |

## Audit and Incident Handling

- Keep stderr logs in the MCP host's protected log destination.
- For local durable audit, set `AOS8_AUDIT_LOG_PATH` to a protected writable path.
- Correlate failures using `correlation_id`, operation, target, outcome, and latency.
- If output may have exposed a secret, stop the MCP process, preserve sanitized audit
  metadata, rotate the downstream credential, and review client conversation retention.

## Upgrade and Rollback

1. Run `uv sync --locked`, `uv run ruff check .`, `uv run pytest`, and `uv run pip-audit`.
2. Validate with an MCP Inspector and the actual target host before rollout.
3. Keep the previous package/commit available for rollback.
4. After rollback, confirm tool discovery, target policy, TLS, and test connection.
