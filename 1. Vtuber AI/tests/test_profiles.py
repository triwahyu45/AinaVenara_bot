from types import SimpleNamespace

import pytest

from aina_companion.profiles import ApiProfile, ApiProfileManager, retry_delay_seconds


def test_auto_failover_honors_cooldown():
    now = [100.0]
    first = ApiProfile("one", "One", priority=1)
    second = ApiProfile("two", "Two", priority=2)
    manager = ApiProfileManager(
        [first, second], lambda profile_id: f"key-{profile_id}", now=lambda: now[0]
    )

    def operation(_secret, profile):
        if profile.id == "one":
            raise RuntimeError("429 RESOURCE_EXHAUSTED Please retry in 12s")
        return profile.id

    assert manager.call(operation) == "two"
    assert first.cooldown_until == 112.0
    assert first.health_status == "cooldown"
    assert second.health_status == "healthy"
    assert [item.id for item in manager.candidates()] == ["two"]


def test_specific_mode_uses_selected_profile():
    profiles = [ApiProfile("one", "One"), ApiProfile("two", "Two")]
    manager = ApiProfileManager(
        profiles, lambda profile_id: profile_id, mode="specific", specific_profile_id="two"
    )
    assert manager.call(lambda secret, _profile: secret) == "two"


def test_retry_delay_default():
    assert retry_delay_seconds(RuntimeError("quota"), default=42) == 42


def test_specific_mode_does_not_retry_profile_during_cooldown():
    profile = ApiProfile("one", "One", cooldown_until=200)
    manager = ApiProfileManager(
        [profile],
        lambda profile_id: profile_id,
        mode="specific",
        specific_profile_id="one",
        now=lambda: 100,
    )
    assert manager.candidates() == []


def test_profile_metadata_never_contains_secret():
    profile = ApiProfile("one", "One", health_status="healthy")
    assert profile.to_dict() == {
        "id": "one",
        "label": "One",
        "enabled": True,
        "priority": 100,
        "cooldown_until": 0.0,
        "last_error": "",
        "health_status": "healthy",
    }


def test_retry_delay_uses_response_header_when_available():
    error = RuntimeError("429 RESOURCE_EXHAUSTED")
    error.response = SimpleNamespace(headers={"retry-after": "7"})
    assert retry_delay_seconds(error) == 7


def test_missing_secret_marks_profile_without_calling_operation():
    profile = ApiProfile("one", "One")
    manager = ApiProfileManager([profile], lambda _profile_id: None)
    with pytest.raises(RuntimeError, match="belum memiliki secret"):
        manager.call(lambda _secret, _profile: pytest.fail("operation tidak boleh dipanggil"))
    assert profile.health_status == "missing_secret"
