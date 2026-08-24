"""Conventional software tests (pytest) for the provider abstraction and registry."""

from __future__ import annotations

import pytest

from harcompanon.config import available_providers, build_provider
from harcompanon.providers import AnthropicProvider, Provider, RawResponse, estimate_cost


def test_estimate_cost_known_and_unknown() -> None:
    # claude-opus-4-8 is $5/$25 per 1M tokens.
    assert estimate_cost("claude-opus-4-8", 1_000_000, 1_000_000) == pytest.approx(30.0)
    assert estimate_cost("claude-opus-4-8", None, 10) is None
    assert estimate_cost("some-unpriced-model", 100, 100) is None


def test_estimate_cost_normalizes_dated_model_id() -> None:
    # The API can return a dated snapshot; pricing is keyed on the alias.
    assert estimate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000) == pytest.approx(6.0)


def test_registry_builds_anthropic_with_default_model() -> None:
    assert "anthropic" in available_providers()
    provider = build_provider("anthropic")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-4-8"
    assert build_provider("anthropic", model="claude-haiku-4-5").model == "claude-haiku-4-5"


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        build_provider("does-not-exist")


def test_anthropic_provider_satisfies_protocol() -> None:
    # runtime_checkable Protocol: name, model, complete().
    assert isinstance(AnthropicProvider(), Provider)


def test_raw_response_round_trips() -> None:
    r = RawResponse(provider="anthropic", model="claude-opus-4-8", text="hi", input_tokens=3)
    assert r.model_dump()["text"] == "hi"
    assert r.output_tokens is None
