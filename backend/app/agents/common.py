"""Common utilities and configuration builders for ADK agents."""

from google.genai.types import GenerateContentConfig, ThinkingConfig


def build_thinking_config(
    model: str,
    thinking_budget: int | None = None,
) -> ThinkingConfig | None:
    """
    Build the appropriate ThinkingConfig based on the model family.

    For Gemini 3 models (e.g. gemini-3.5-flash-lite, gemini-3.7-flash),
    thinking_level="LOW" is used because integer thinking_budget is unsupported.
    For Gemini 2.x models, thinking_budget is passed directly.
    """
    if thinking_budget is None:
        return None

    model_lower = model.lower()
    if "gemini-3" in model_lower:
        return ThinkingConfig(thinking_level="LOW")
    return ThinkingConfig(thinking_budget=thinking_budget)


def build_agent_generate_content_config(
    model: str,
    thinking_budget: int | None = None,
) -> GenerateContentConfig | None:
    """Build a GenerateContentConfig with model-appropriate thinking configuration."""
    thinking_config = build_thinking_config(model=model, thinking_budget=thinking_budget)
    if thinking_config is not None:
        return GenerateContentConfig(thinking_config=thinking_config)
    return None
