# Changelog

All notable changes to this project are documented here.

## 0.3.0 - 2026-08-03

### Added

- Central policy for show commands, configuration objects, and hierarchy paths.
- Normalized wireless-client and WLAN relationship summaries.
- Profile-scoped deterministic WLAN security findings with confidence and rule version.
- Optional rotating JSONL audit log with sanitized correlation records.
- Response-size limits, text redaction, bounded query parameters, and safer API errors.
- Security and operations documentation plus dependency auditing in CI.

### Changed

- Generic show commands now require a reviewed policy prefix.
- Running/startup configuration and unsafe shell-like command forms are blocked.
- WLAN analysis maps findings to affected WLANs instead of scanning arbitrary strings.

## 0.2.0 - 2026-07-18

- Added node-aware targeting, normalized result envelopes, deterministic analyzers,
  retry/backoff, TLS verification defaults, and expanded CI coverage.
