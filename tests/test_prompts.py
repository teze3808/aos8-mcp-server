from aruba_aos8_mcp.server import (
    aos8_ap_group_profile_map,
    aos8_controller_failover_check,
    aos8_client_connectivity_review,
    aos8_compare_config_paths,
    aos8_configuration_flow_review,
    aos8_health_overview,
    aos8_hardening_review,
    aos8_review_ap_group,
    aos8_safe_show_command,
    aos8_security_review,
    aos8_structured_troubleshooting,
    aos8_troubleshoot_ap,
    aos8_troubleshoot_wlan,
    aos8_wlan_profile_review,
)


def test_health_prompt_names_core_tools() -> None:
    prompt = aos8_health_overview()

    assert "aos8_get_health_summary" in prompt
    assert "aos8_get_managed_devices" in prompt
    assert "aos8_get_ap_summary" in prompt
    assert "client, infrastructure, or WLAN function/service" in prompt


def test_troubleshoot_ap_prompt_includes_target() -> None:
    prompt = aos8_troubleshoot_ap("SE-AP505-AOS8")

    assert "SE-AP505-AOS8" in prompt
    assert "show ap details ap-name SE-AP505-AOS8" in prompt
    assert "Registration/discovery stage" in prompt


def test_wlan_profile_review_prompt_uses_config_path() -> None:
    prompt = aos8_wlan_profile_review("/md/SE")

    assert 'config_path "/md/SE"' in prompt
    assert "AP group -> VAP -> SSID profile" in prompt
    assert "Redact passphrases" in prompt


def test_controller_failover_prompt_checks_cluster_status() -> None:
    prompt = aos8_controller_failover_check()

    assert "aos8_get_cluster_status" in prompt
    assert "AP active/standby controller distribution" in prompt


def test_ap_group_map_prompt_cross_references_live_inventory() -> None:
    prompt = aos8_ap_group_profile_map("/md/SE")

    assert "aos8_get_ap_summary" in prompt
    assert "Cross-reference live AP groups" in prompt


def test_safe_show_prompt_rejects_non_show_commands() -> None:
    prompt = aos8_safe_show_command("reload")

    assert 'starts with "show "' in prompt
    assert "destructive commands" in prompt
    assert "reload" in prompt


def test_troubleshoot_wlan_prompt_builds_chain() -> None:
    prompt = aos8_troubleshoot_wlan("/md/SE", "SE-MGMT-AOS8")

    assert "SE-MGMT-AOS8" in prompt
    assert "AP group -> Virtual AP -> SSID profile" in prompt
    assert "show ap bss-table" in prompt
    assert "802.11 negotiation" in prompt


def test_review_ap_group_prompt_names_target_group() -> None:
    prompt = aos8_review_ap_group("/md/SE", "SE-AP-ONLY-MGMT")

    assert "SE-AP-ONLY-MGMT" in prompt
    assert "Live AP membership" in prompt
    assert "Non-default profile highlights" in prompt


def test_security_review_prompt_checks_radius_and_redaction() -> None:
    prompt = aos8_security_review("/md/SE")

    assert "RADIUS accounting" in prompt
    assert "CoA/RFC3576" in prompt
    assert "Redact passphrases" in prompt


def test_hardening_review_prompt_checks_management_plane() -> None:
    prompt = aos8_hardening_review("/md/SE")

    assert 'config_path "/md/SE"' in prompt
    assert "management-plane evidence" in prompt
    assert "TLS protocol/cipher posture" in prompt
    assert "QOTD/17" in prompt
    assert "Do not prescribe config changes" in prompt


def test_compare_config_paths_prompt_uses_both_paths() -> None:
    prompt = aos8_compare_config_paths("/md", "/md/SE")

    assert '"/md"' in prompt
    assert '"/md/SE"' in prompt
    assert "Added/removed/changed profile summary" in prompt


def test_client_connectivity_review_prompt_uses_client_mac() -> None:
    prompt = aos8_client_connectivity_review("/md/SE", "aa:bb:cc:dd:ee:ff")

    assert "aa:bb:cc:dd:ee:ff" in prompt
    assert "aos8_get_clients" in prompt
    assert "Most likely failure domain" in prompt
    assert "server-derived role" in prompt


def test_structured_troubleshooting_prompt_scopes_issue() -> None:
    prompt = aos8_structured_troubleshooting("guest clients cannot connect")

    assert "guest clients cannot connect" in prompt
    assert "Scope the blast radius" in prompt
    assert "five client phases" in prompt
    assert "client issue" in prompt


def test_configuration_flow_review_prompt_is_hierarchy_aware() -> None:
    prompt = aos8_configuration_flow_review("/md/SE")

    assert 'config_path "/md/SE"' in prompt
    assert "hierarchy path -> AP group -> Virtual AP" in prompt
    assert "Named VLAN/VLAN binding" in prompt
    assert "live operational state" in prompt
