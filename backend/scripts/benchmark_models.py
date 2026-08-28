"""
CLI runner for Gemini models benchmarking and evaluation.

Usage:
    uv run python -m scripts.benchmark_models
    uv run python -m scripts.benchmark_models --models gemini-2.5-flash,gemini-2.0-flash
    uv run python -m scripts.benchmark_models --output-md benchmark_results.md
"""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings  # noqa: E402
from app.eval.runner import GeminiModelEvaluator  # noqa: E402
from app.eval.scenarios import get_standard_eval_scenarios  # noqa: E402

DEFAULT_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
]


def _positive_int(value: str) -> int:
    try:
        ival = int(value)
        if ival < 1:
            raise argparse.ArgumentTypeError("Concurrency must be at least 1")
        return ival
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer: {value}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark and evaluate multiple Gemini models on Vesta agent capabilities."
    )
    parser.add_argument(
        "--models",
        type=str,
        default=",".join(DEFAULT_MODELS),
        help=f"Comma-separated list of Gemini models to test (default: {','.join(DEFAULT_MODELS)})",
    )
    parser.add_argument(
        "--concurrency",
        type=_positive_int,
        default=2,
        help="Maximum concurrent API calls (must be >= 1, default: 2)",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="",
        help="Optional path to save Markdown report",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="",
        help="Optional path to save raw JSON results",
    )
    return parser.parse_args()


async def main_async():
    args = parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY is not configured in settings or environment.", file=sys.stderr)
        sys.exit(1)

    print("🚀 Starting Gemini Models Benchmark...")
    print(f"📦 Models to evaluate: {', '.join(models)}")
    scenarios = get_standard_eval_scenarios()
    print(f"🧪 Test scenarios count: {len(scenarios)}")
    print(f"⚡ Max concurrency: {args.concurrency}")
    print("-" * 80)

    evaluator = GeminiModelEvaluator(api_key=api_key, max_concurrency=args.concurrency)
    summaries = await evaluator.run_benchmark(models=models, test_cases=scenarios)

    # Print hierarchical summary table to terminal
    print("\n" + "=" * 95)
    print(f"{'Model / Test Scenario':<32} | {'Status':<9} | {'Time (s)':<9} | {'In / Out':<12} | {'Tools / Details'}")
    print("=" * 95)
    for s in summaries.values():
        pass_badge = "🟢" if s.pass_rate_percent == 100 else ("🟡" if s.pass_rate_percent >= 75 else "🔴")
        model_header = f"📦 {s.model}"
        pass_str = f"{pass_badge} {s.pass_rate_percent}%"
        time_str = f"{s.avg_latency_seconds}s"
        tokens_str = f"{s.total_tokens:,} tot"
        details_str = f"{s.passed_tests}/{s.total_tests} passed (${s.total_estimated_cost_usd:.5f})"

        print(f"{model_header:<32} | {pass_str:<9} | {time_str:<9} | {tokens_str:<12} | {details_str}")

        # Breakdown by specific task
        for i, r in enumerate(s.results):
            is_last = (i == len(s.results) - 1)
            branch = "  └─ " if is_last else "  ├─ "
            task_col = f"{branch}{r.test_case_name}"
            status_str = "✅ PASS" if r.success else "❌ FAIL"
            r_time = f"{r.latency_seconds}s"
            r_tokens = f"{r.input_tokens}/{r.output_tokens}"
            
            if r.success:
                tools_str = ", ".join(t.name for t in r.tools_called) or "(none)"
                r_details = f"Tools: {tools_str}"
            else:
                err_msg = "; ".join(r.validation_errors) if r.validation_errors else (r.error_message or "failed")
                r_details = f"Err: {err_msg[:45]}"

            print(f"{task_col:<32} | {status_str:<9} | {r_time:<9} | {r_tokens:<12} | {r_details}")
        print("-" * 95)
    print("=" * 95 + "\n")

    # Generate Markdown Report
    md_report = evaluator.generate_markdown_report(summaries)

    if args.output_md:
        out_path = Path(args.output_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_report, encoding="utf-8")
        print(f"📝 Markdown report saved to: {out_path}")

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        json_data = {model: asdict(summary) for model, summary in summaries.items()}
        out_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
        print(f"💾 JSON report saved to: {out_path}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
