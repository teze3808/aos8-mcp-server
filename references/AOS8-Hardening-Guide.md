# AOS 8 Hardening Guide Reference

Canonical support document:
https://support.hpe.com/hpesc/public/docDisplay?docId=a00107216en_us

Notes:

- The support page is reachable, but the document body was not exposed through the local browser/tooling during review on 2026-06-04.
- HPE/Airheads references identify this as the ArubaOS / AOS 8 controller hardening guide.
- Community references point to hardening topics such as management-plane exposure, TLS protocol/cipher settings, and vulnerability-scanner findings including QOTD/17 false positives.

Prompt design implication:

- Treat hardening as a read-only evidence review unless the user explicitly asks for changes.
- Start with management-plane exposure and version posture before WLAN-specific security.
- Review web-server TLS/cipher posture, SSH exposure, management access scope, control-plane firewall/ACL posture, AAA/admin authentication, logging/accounting, SNMP, NTP/DNS/syslog, certificates, and unnecessary services.
- Distinguish scanner false positives from confirmed exposure by collecting live evidence first.
- Redact secrets, passphrases, SNMP communities, license keys, private keys, and certificate material.
