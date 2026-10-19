from .base import ModelTurn, Provider, ToolCall

__all__ = ["ModelTurn", "Provider", "ToolCall", "build_provider"]


def build_provider(settings):
    """Construct the live provider described by settings (imported lazily)."""
    from .. import config
    from .openai_compat import OpenAICompatProvider

    api_key = config.api_key_for(settings.provider)
    if not api_key:
        key_env = config.PROVIDERS[settings.provider]["key_env"]
        raise RuntimeError(f"{key_env} is not set; add it to .env (see .env.example)")
    return OpenAICompatProvider(settings=settings, api_key=api_key)
