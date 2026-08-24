from unittest.mock import AsyncMock, MagicMock

from app.eval.mock_tools import create_mock_tools
from app.eval.models import (
    EvalResult,
    EvalTestCase,
    ModelBenchmarkSummary,
    ToolCallRecord,
    calculate_cost,
)
from app.eval.runner import GeminiModelEvaluator
from app.eval.scenarios import (
    _validate_schedule_args,
    _validate_weather_args,
    get_standard_eval_scenarios,
)


def test_calculate_cost():
    """Test cost estimation for different models."""
    cost_flash = calculate_cost("gemini-2.5-flash", 1_000_000, 1_000_000)
    assert cost_flash == 0.75  # 0.15 + 0.60

    cost_pro = calculate_cost("gemini-2.5-pro", 1_000_000, 1_000_000)
    assert cost_pro == 6.25  # 1.25 + 5.00


def test_scenario_validators():
    """Test argument validation functions."""
    assert _validate_weather_args({"city": "Kyiv"}) is True
    assert _validate_weather_args({"city": "Київ"}) is False
    assert _validate_weather_args({"city": ""}) is False

    assert (
        _validate_schedule_args(
            {"summary": "Meeting", "start_time_iso": "2026-08-25T14:30:00"}
        )
        is True
    )
    assert _validate_schedule_args({"summary": "", "start_time_iso": "2026-08-25"}) is False
    assert _validate_schedule_args({"summary": "Meeting", "start_time_iso": "invalid"}) is False


async def test_mock_tools_execution():
    """Test that all mock tools can be invoked and record calls."""
    recorded_calls = []

    def on_call(name, args):
        recorded_calls.append((name, args))

    tools = create_mock_tools(on_tool_call=on_call)
    assert len(tools) >= 10

    # Test weather mock tool
    weather_tool = next(t for t in tools if t.__name__ == "get_weather_info")
    weather_res = await weather_tool(city="Kyiv", days=3)
    assert "Current weather in Kyiv" in weather_res
    assert ("get_weather_info", {"city": "Kyiv", "days": 3}) in recorded_calls

    # Test calendar events mock tool
    calendar_tool = next(t for t in tools if t.__name__ == "get_calendar_events")
    cal_res = await calendar_tool(days=7)
    assert "Upcoming events" in cal_res

    # Test schedule event mock tool
    sched_tool = next(t for t in tools if t.__name__ == "schedule_event_tool")
    sched_res = await sched_tool(summary="Test Sync", start_time_iso="2026-08-25T10:00:00")
    assert "successfully created" in sched_res

    # Test tasks mock tool
    task_tool = next(t for t in tools if t.__name__ == "create_task_tool")
    task_res = await task_tool(title="Buy milk")
    assert "Buy milk" in task_res


def test_standard_eval_scenarios_structure():
    """Test standard scenarios list contains expected test definitions."""
    scenarios = get_standard_eval_scenarios()
    assert len(scenarios) >= 5
    names = [s.name for s in scenarios]
    assert "direct_conversation" in names
    assert "weather_single_tool" in names
    assert "calendar_schedule_event" in names
    assert "proactive_daily_briefing" in names


async def test_evaluator_evaluate_single_test_case_mocked():
    """Test evaluator run logic with mocked Google GenAI client."""
    evaluator = GeminiModelEvaluator(api_key="test_key_fake")

    mock_part = MagicMock()
    mock_part.function_call = MagicMock()
    mock_part.function_call.name = "get_weather_info"
    mock_part.function_call.args = {"city": "Kyiv", "days": 7}

    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    mock_response.text = "In Kyiv the weather is sunny."
    mock_response.usage_metadata.prompt_token_count = 100
    mock_response.usage_metadata.candidates_token_count = 50
    mock_response.usage_metadata.total_token_count = 150

    evaluator.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    test_case = EvalTestCase(
        name="test_weather",
        prompt="Weather in Kyiv?",
        expected_tools=["get_weather_info"],
        tool_arg_validators={"get_weather_info": _validate_weather_args},
    )

    result = await evaluator.evaluate_single_test_case(
        model="gemini-2.5-flash", test_case=test_case
    )

    assert result.success is True
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert len(result.tools_called) == 1
    assert result.tools_called[0].name == "get_weather_info"


def test_generate_markdown_report():
    """Test generating markdown report from evaluation summaries."""
    summaries = {
        "gemini-2.5-flash": ModelBenchmarkSummary(
            model="gemini-2.5-flash",
            total_tests=2,
            passed_tests=2,
            failed_tests=0,
            pass_rate_percent=100.0,
            avg_latency_seconds=0.85,
            total_tokens=500,
            total_estimated_cost_usd=0.0003,
            results=[
                EvalResult(
                    model="gemini-2.5-flash",
                    test_case_name="weather_test",
                    success=True,
                    latency_seconds=0.85,
                    input_tokens=200,
                    output_tokens=50,
                    total_tokens=250,
                    estimated_cost_usd=0.00015,
                    tools_called=[ToolCallRecord(name="get_weather_info", args={"city": "Kyiv"})],
                    response_text="Sunny in Kyiv",
                )
            ],
        )
    }

    report = GeminiModelEvaluator.generate_markdown_report(summaries)
    assert "# 📊 Gemini Models E2E Evaluation & Benchmark Report" in report
    assert "gemini-2.5-flash" in report
    assert "100.0%" in report
