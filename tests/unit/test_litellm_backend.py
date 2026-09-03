"""Tests for the optional LiteLLM backend — construction and routing only (no network).

These don't import ``litellm`` (it's lazy, inside ``complete()``), so they pass whether or not the
optional extra is installed. A real call is an opt-in, live thing the user drives.
"""

from __future__ import annotations

import pytest

from harcompanon.config import build_provider
from harcompanon.providers import LiteLLMProvider, Provider


def test_build_provider_litellm_backend_maps_the_route() -> None:
    p = build_provider("anthropic", backend="litellm")
    assert isinstance(p, LiteLLMProvider)
    assert isinstance(p, Provider)  # satisfies the same protocol as the native providers
    assert p.name == "anthropic"
    assert p.model == "claude-opus-4-8"  # the flagship default
    assert p.litellm_model == "anthropic/claude-opus-4-8"


def test_kimi_routes_to_moonshot() -> None:
    p = build_provider("kimi", model="kimi-k3", backend="litellm")
    assert isinstance(p, LiteLLMProvider)
    assert p.litellm_model == "moonshot/kimi-k3"  # our 'kimi' is LiteLLM's 'moonshot'


def test_native_backend_is_the_default_and_not_a_litellm_provider() -> None:
    assert not isinstance(build_provider("openai"), LiteLLMProvider)


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError, match="Unknown backend"):
        build_provider("anthropic", backend="langchain")
