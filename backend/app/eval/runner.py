"""
Execution engine for evaluating and benchmarking multiple Gemini models.
"""

import asyncio
import datetime
import logging
import time
from zoneinfo import ZoneInfo

from google import genai
from google.genai import types

from app.core.config import settings
from app.eval.mock_tools import create_mock_tools
from app.eval.models import (
    EvalResult,
    EvalTestCase,
    ModelBenchmarkSummary,
    ToolCallRecord,
    calculate_cost,
)

logger = logging.getLogger(__name__)


class GeminiModelEvaluator:
    """Evaluates and benchmarks multiple Gemini models concurrently."""

    def __init__(
        self,
        api_key: str | None = None,
        max_concurrency: int = 4,
    ) -> None:
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY must be provided or configured in settings"
            )

        self.client = genai.Client(api_key=self.api_key)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _build_system_instruction(self) -> str:
        try:
            tz = ZoneInfo("Europe/Kyiv")
        except Exception:
            tz = ZoneInfo("Europe/Kiev")
        now = datetime.datetime.now(tz)
        current_time_str = now.strftime("%Y-%m-%d %H:%M (%A)")

        return (
            f"{settings.SYSTEM_INSTRUCTION}\n"
            f"Current Date and Time: {current_time_str}.\n"
            f"User's Location: Ukraine (default for weather).\n"
            f"--- TOOL GUIDELINES ---\n"
            f"1. Proactivity: If the user asks about 'today' or 'my day', proactively call BOTH `get_calendar_events(days=1)` and `get_weather_info(city='<resolved_city>', days=1)` to provide a complete summary.\n"
            f"2. Weather: You can fetch both current weather and forecast for up to 14 days using `get_weather_info`. Always translate city name to English.\n"
            f"3. Scheduling: When using `schedule_event_tool`, always use the 'Current Date' above as a reference to calculate relative dates like 'tomorrow' or 'next Friday'.\n"
            f"4. Memory: When user shares personal details or preferences, use `remember_user_fact`."
        )

    async def evaluate_single_test_case(
        self,
        model: str,
        test_case: EvalTestCase,
    ) -> EvalResult:
        """Run a single test case against a specified model."""
        async with self.semaphore:
            tools_called: list[ToolCallRecord] = []

            def on_tool_call(name: str, args: dict):
                tools_called.append(ToolCallRecord(name=name, args=args))

            tools = create_mock_tools(on_tool_call=on_tool_call)
            system_instruction = (
                test_case.system_instruction_override
                or self._build_system_instruction()
            )

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                temperature=0.0,  # Deterministic for benchmark
            )

            start_time = time.perf_counter()
            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=test_case.prompt,
                    config=config,
                )
                latency = time.perf_counter() - start_time

                # Extract tool calls from response parts if not captured via mock execution
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            name = part.function_call.name
                            args = getattr(part.function_call, "args", {}) or {}
                            if not any(tc.name == name for tc in tools_called):
                                tools_called.append(
                                    ToolCallRecord(name=name, args=dict(args))
                                )

                usage = getattr(response, "usage_metadata", None)
                in_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
                out_tokens = (
                    getattr(usage, "candidates_token_count", 0) if usage else 0
                )
                tot_tokens = getattr(usage, "total_token_count", 0) if usage else 0
                cost = calculate_cost(model, in_tokens, out_tokens)

                # Validation
                validation_errors = []
                called_tool_names = [tc.name for tc in tools_called]

                for expected in test_case.expected_tools:
                    if expected not in called_tool_names:
                        validation_errors.append(
                            f"Expected tool '{expected}' was not called (called: {called_tool_names})"
                        )

                for unexpected in test_case.unexpected_tools:
                    if unexpected in called_tool_names:
                        validation_errors.append(
                            f"Unexpected tool '{unexpected}' was called"
                        )

                for tc_record in tools_called:
                    if tc_record.name in test_case.tool_arg_validators:
                        validator = test_case.tool_arg_validators[tc_record.name]
                        if not validator(tc_record.args):
                            validation_errors.append(
                                f"Arguments for tool '{tc_record.name}' failed validation: {tc_record.args}"
                            )

                response_text = response.text or ""
                for kw in test_case.expected_content_keywords:
                    if kw.lower() not in response_text.lower():
                        validation_errors.append(
                            f"Expected keyword '{kw}' missing in response"
                        )

                success = len(validation_errors) == 0

                return EvalResult(
                    model=model,
                    test_case_name=test_case.name,
                    success=success,
                    latency_seconds=round(latency, 3),
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    total_tokens=tot_tokens,
                    estimated_cost_usd=cost,
                    tools_called=tools_called,
                    response_text=response_text,
                    validation_errors=validation_errors,
                )

            except Exception as e:
                latency = time.perf_counter() - start_time
                logger.exception("Evaluation error for model %s: %s", model, e)
                return EvalResult(
                    model=model,
                    test_case_name=test_case.name,
                    success=False,
                    latency_seconds=round(latency, 3),
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    estimated_cost_usd=0.0,
                    tools_called=[],
                    response_text="",
                    error_message=str(e),
                    validation_errors=[f"API Exception: {str(e)}"],
                )

    async def run_benchmark(
        self,
        models: list[str],
        test_cases: list[EvalTestCase],
    ) -> dict[str, ModelBenchmarkSummary]:
        """
        Run all test cases across multiple models in parallel.

        Returns:
            Dictionary mapping model name to ModelBenchmarkSummary.
        """
        tasks = []
        for model in models:
            for tc in test_cases:
                tasks.append(self.evaluate_single_test_case(model, tc))

        raw_results: list[EvalResult] = await asyncio.gather(*tasks)

        summaries: dict[str, ModelBenchmarkSummary] = {}
        for model in models:
            summaries[model] = ModelBenchmarkSummary(model=model)

        for res in raw_results:
            summary = summaries[res.model]
            summary.total_tests += 1
            if res.success:
                summary.passed_tests += 1
            else:
                summary.failed_tests += 1
            summary.total_input_tokens += res.input_tokens
            summary.total_output_tokens += res.output_tokens
            summary.total_tokens += res.total_tokens
            summary.total_estimated_cost_usd += res.estimated_cost_usd
            summary.results.append(res)

        for summary in summaries.values():
            if summary.total_tests > 0:
                summary.pass_rate_percent = round(
                    (summary.passed_tests / summary.total_tests) * 100, 1
                )
                total_latency = sum(r.latency_seconds for r in summary.results)
                summary.avg_latency_seconds = round(
                    total_latency / summary.total_tests, 2
                )
                summary.total_estimated_cost_usd = round(
                    summary.total_estimated_cost_usd, 6
                )

        return summaries

    @staticmethod
    def generate_markdown_report(
        summaries: dict[str, ModelBenchmarkSummary],
    ) -> str:
        """Generate a GitHub-flavored markdown report of benchmark results."""
        lines = [
            "# 📊 Gemini Models E2E Evaluation & Benchmark Report",
            "",
            f"**Generated:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## 🏆 Model Performance Summary",
            "",
            "| Model | Pass Rate | Passed / Total | Avg Latency | Total Tokens | Est. Cost ($) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for s in summaries.values():
            pass_badge = "🟢" if s.pass_rate_percent == 100 else ("🟡" if s.pass_rate_percent >= 75 else "🔴")
            lines.append(
                f"| `{s.model}` | {pass_badge} {s.pass_rate_percent}% | {s.passed_tests}/{s.total_tests} | "
                f"{s.avg_latency_seconds}s | {s.total_tokens:,} | ${s.total_estimated_cost_usd:.6f} |"
            )

        lines.extend([
            "",
            "## 📋 Detailed Test Case Breakdown",
            "",
            "| Test Case | Model | Status | Latency | Tokens (In/Out) | Tools Called | Errors |",
            "| :--- | :--- | :---: | :---: | :---: | :--- | :--- |",
        ])

        for s in summaries.values():
            for r in s.results:
                status_icon = "✅ PASS" if r.success else "❌ FAIL"
                tools_str = ", ".join(f"`{t.name}`" for t in r.tools_called) or "*(none)*"
                err_str = "; ".join(r.validation_errors) if r.validation_errors else "—"
                lines.append(
                    f"| `{r.test_case_name}` | `{r.model}` | {status_icon} | {r.latency_seconds}s | "
                    f"{r.input_tokens}/{r.output_tokens} | {tools_str} | {err_str} |"
                )

        return "\n".join(lines)
