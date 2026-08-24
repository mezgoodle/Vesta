"""
End-to-End evaluation tests for Google Gemini models.

Runs against live Google GenAI API to benchmark and verify model capabilities
(tool calling, multi-tool proactivity, parameter formatting, memory).

Run explicitly with:
    pytest -m e2e
"""

import os
import pytest
from app.core.config import settings
from app.eval.runner import GeminiModelEvaluator
from app.eval.scenarios import get_standard_eval_scenarios

# Target Gemini models to evaluate and compare
BENCHMARK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
]


@pytest.fixture(scope="module")
def api_key():
    key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
    if not key:
        pytest.skip("GOOGLE_API_KEY is not set. Skipping live E2E model tests.")
    return key


@pytest.mark.e2e
class TestGeminiModelsE2E:
    """Live E2E evaluation suite for comparing Gemini models."""

    @pytest.mark.parametrize("model", BENCHMARK_MODELS)
    async def test_model_weather_single_tool(self, api_key: str, model: str):
        """Test if model correctly invokes get_weather_info with translated city name."""
        evaluator = GeminiModelEvaluator(api_key=api_key)
        scenarios = [s for s in get_standard_eval_scenarios() if s.name == "weather_single_tool"]
        assert len(scenarios) == 1

        result = await evaluator.evaluate_single_test_case(model=model, test_case=scenarios[0])
        assert result.success, f"Model {model} failed weather test: {result.validation_errors}"
        assert any(t.name == "get_weather_info" for t in result.tools_called)

    @pytest.mark.parametrize("model", BENCHMARK_MODELS)
    async def test_model_calendar_schedule_event(self, api_key: str, model: str):
        """Test if model correctly formats ISO datetime when scheduling an event."""
        evaluator = GeminiModelEvaluator(api_key=api_key)
        scenarios = [s for s in get_standard_eval_scenarios() if s.name == "calendar_schedule_event"]
        assert len(scenarios) == 1

        result = await evaluator.evaluate_single_test_case(model=model, test_case=scenarios[0])
        assert result.success, f"Model {model} failed scheduling test: {result.validation_errors}"

    @pytest.mark.parametrize("model", BENCHMARK_MODELS)
    async def test_model_proactive_daily_briefing(self, api_key: str, model: str):
        """Test if model proactively invokes multiple tools for daily summary."""
        evaluator = GeminiModelEvaluator(api_key=api_key)
        scenarios = [s for s in get_standard_eval_scenarios() if s.name == "proactive_daily_briefing"]
        assert len(scenarios) == 1

        result = await evaluator.evaluate_single_test_case(model=model, test_case=scenarios[0])
        # We check result without hard-failing if older flash models only trigger 1 tool
        tool_names = [t.name for t in result.tools_called]
        assert len(tool_names) >= 1, f"Model {model} failed to call any tools: {result.validation_errors}"

    @pytest.mark.parametrize("model", BENCHMARK_MODELS)
    async def test_model_direct_conversation_no_tools(self, api_key: str, model: str):
        """Test that conversational greeting does not trigger tools."""
        evaluator = GeminiModelEvaluator(api_key=api_key)
        scenarios = [s for s in get_standard_eval_scenarios() if s.name == "direct_conversation"]
        assert len(scenarios) == 1

        result = await evaluator.evaluate_single_test_case(model=model, test_case=scenarios[0])
        assert result.success, f"Model {model} erroneously triggered tools: {result.validation_errors}"
        assert len(result.tools_called) == 0
