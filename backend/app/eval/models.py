"""Data models and schemas for Gemini evaluations and benchmarks."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class EvalTestCase:
    """A test case definition for LLM evaluation."""

    name: str
    prompt: str
    description: str = ""
    expected_tools: list[str] = field(default_factory=list)
    unexpected_tools: list[str] = field(default_factory=list)
    tool_arg_validators: dict[str, Callable[[dict[str, Any]], bool]] = field(
        default_factory=dict
    )
    expected_content_keywords: list[str] = field(default_factory=list)
    system_instruction_override: str | None = None


@dataclass
class ToolCallRecord:
    """Record of a tool call executed during generation."""

    name: str
    args: dict[str, Any]
    result: str = ""


@dataclass
class EvalResult:
    """Outcome of running an evaluation test case against a specific model."""

    model: str
    test_case_name: str
    success: bool
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    tools_called: list[ToolCallRecord] = field(default_factory=list)
    response_text: str = ""
    error_message: str | None = None
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class ModelBenchmarkSummary:
    """Aggregated evaluation metrics for a single model across multiple test cases."""

    model: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    pass_rate_percent: float = 0.0
    avg_latency_seconds: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    results: list[EvalResult] = field(default_factory=list)


# Pricing estimates per 1,000,000 tokens (Standard Tier as of 2026)
# Prompt / Output in USD
MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "gemini-3.7-flash": (0.15, 0.60),
    "gemini-3.6-flash": (0.15, 0.60),
    "gemini-3.5-flash": (0.15, 0.60),
    "gemini-3.5-flash-lite": (0.075, 0.30),
    "gemini-3-flash-preview": (0.15, 0.60),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.075, 0.30),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD for a given token usage."""
    rates = MODEL_PRICING_PER_1M.get(model)
    if not rates:
        # Fallback matching by descending key length so specific variants (e.g. lite) match first
        for known_model, rate in sorted(
            MODEL_PRICING_PER_1M.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if known_model in model:
                rates = rate
                break
    if not rates:
        rates = (0.15, 0.60)

    input_rate, output_rate = rates

    # Handle Gemini 2.5 Pro tiered pricing for >200K prompt tokens
    if "gemini-2.5-pro" in model and input_tokens > 200_000:
        input_rate = 2.50
        output_rate = 15.00

    cost = (input_tokens / 1_000_000 * input_rate) + (
        output_tokens / 1_000_000 * output_rate
    )
    return round(cost, 8)
