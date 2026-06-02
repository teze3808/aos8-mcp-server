from aruba_aos8_mcp.server import (
    aos8_ap_group_profile_map,
    aos8_controller_failover_check,
    aos8_health_overview,
    aos8_safe_show_command,
    aos8_troubleshoot_ap,
    aos8_wlan_profile_review,
)


def test_health_prompt_names_core_tools() -> None:
    prompt = aos8_health_overview()

    assert "aos8_get_health_summary" in prompt
    assert "aos8_get_managed_devices" in prompt
    assert "aos8_get_ap_summary" in prompt


def test_troubleshoot_ap_prompt_includes_target() -> None:
    prompt = aos8_troubleshoot_ap("SE-AP505-AOS8")

    assert "SE-AP505-AOS8" in prompt
    assert "show ap details ap-name SE-AP505-AOS8" in prompt


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
