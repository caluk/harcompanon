"""Provider registry + credential loading.

The provider list is config-driven: to add a model you register a factory here (and its
default model), and the rest of the pipeline can build it by name. Credentials are read from
the environment / a git-ignored ``.env`` — never hardcoded, never committed.
"""

from __future__ import annotations

from collections.abc import Callable

from dotenv import load_dotenv

from harcompanon.providers import (
    AnthropicProvider,
    GeminiProvider,
    LiteLLMProvider,
    OpenAICompatProvider,
    OpenAIProvider,
    Provider,
)
from harcompanon.providers.anthropic import DEFAULT_MAX_TOKENS


def _deepseek(model: str, max_tokens: int) -> Provider:
    return OpenAICompatProvider(
        "deepseek", "https://api.deepseek.com", "DEEPSEEK_API_KEY", model, max_tokens
    )


def _mistral(model: str, max_tokens: int) -> Provider:
    return OpenAICompatProvider(
        "mistral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY", model, max_tokens
    )


def _kimi(model: str, max_tokens: int) -> Provider:
    return OpenAICompatProvider(
        "kimi", "https://api.moonshot.ai/v1", "MOONSHOT_API_KEY", model, max_tokens
    )


#: name -> factory(model, max_tokens) -> Provider.
_REGISTRY: dict[str, Callable[[str, int], Provider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "deepseek": _deepseek,
    "mistral": _mistral,
    "kimi": _kimi,
}

#: name -> default model id used when the caller doesn't override it.
#: Pinned to FIXED, concrete versions for strict reproducibility — deliberately NO floating
#: "-latest" aliases. The two aliases the study originally ran (``gemini-pro-latest``,
#: ``mistral-large-latest``) are frozen here to the concrete versions they pointed at during the
#: runs, resolved live on 2026-09-06 (gemini via the response ``modelVersion``; mistral via the
#: ``/v1/models`` alias mapping). Override per account with --model. Gemini Pro and DeepSeek/Kimi
#: require a funded account; Mistral Large needs a subscription tier that permits it.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-5.2",
    "gemini": "gemini-3.1-pro-preview",
    "deepseek": "deepseek-v4-pro",
    "mistral": "mistral-large-2512",
    "kimi": "kimi-k3",
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
    backend: str = "native",
) -> Provider:
    """Construct a configured provider by name.

    ``backend="native"`` (default) uses each vendor's own SDK. ``backend="litellm"`` routes the
    same model through LiteLLM instead — an opt-in alternative (needs the ``litellm`` extra).
    """
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown provider {name!r}. Available: {', '.join(available_providers()) or '(none)'}."
        )
    resolved = model or DEFAULT_MODELS[name]
    if backend == "litellm":
        return LiteLLMProvider(name, resolved, max_tokens)
    if backend != "native":
        raise ValueError(f"Unknown backend {backend!r} (use 'native' or 'litellm').")
    return _REGISTRY[name](resolved, max_tokens)
