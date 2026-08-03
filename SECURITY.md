# Security

## Supported Trust Boundary

`aos8-mcp-server` is designed for a trusted, single-user local `stdio` deployment.
It is read-only by default and does not implement configuration POST requests or
`write_memory`.

Do not expose the current server as a shared or public network service. A remote or
multi-user deployment requires authenticated transport, independent caller identity,
server-side authorization by tool and target, managed secrets, central audit retention,
and deployment-specific network policy.

## Local Controls

- Use a dedicated least-privilege AOS8 read-only account.
- Keep TLS verification enabled and configure `AOS8_CA_BUNDLE` for an internal CA.
- Restrict show commands, configuration objects, and paths through the `AOS8_*` policy settings.
- Store `.env` and MCP client configuration with owner-only filesystem permissions.
- Do not place passwords, tokens, controller output, or private configuration in issues or logs.
- Review all additional show-command prefixes before enabling them.

## Reporting

Use the repository's GitHub security-reporting channel when available. Do not include
live credentials, private keys, customer configuration, IP addresses, or client data in
a public issue. Rotate any credential that may have been disclosed.
