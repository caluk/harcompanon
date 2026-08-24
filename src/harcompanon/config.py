"""Provider registry + credential loading.

The provider list is config-driven: to add a model you register a factory here (and its
default model), and the rest of the pipeline can build it by name. Credentials are read from
the environment / a git-ignored ``.env`` — never hardcoded, never committed.
"""

from __future__ import annotations

from collections.abc import Callable

from dotenv import load_dotenv

from harcompanon.providers import AnthropicProvider, Provider
from harcompanon.providers.anthropic import DEFAULT_MAX_TOKENS

#: name -> factory(model, max_tokens) -> Provider.
_REGISTRY: dict[str, Callable[[str, int], Provider]] = {
    "anthropic": AnthropicProvider,
}

#: name -> default model id used when the caller doesn't override it.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-opus-4-8",
}


def load_credentials() -> None:
    """Load a git-ignored ``.env`` into the environment (provider SDKs read keys from there)."""
    load_dotenv()


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def build_provider(
    name: str,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Provider:
    """Construct a configured provider by name."""
    factory = _REGISTRY.get(name)
    if factory is None:
        raise ValueError(
            f"Unknown provider {name!r}. Available: {', '.join(available_providers()) or '(none)'}."
        )
    return factory(model or DEFAULT_MODELS[name], max_tokens)
