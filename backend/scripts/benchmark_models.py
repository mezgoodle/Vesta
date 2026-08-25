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
        default=4,
        help="Maximum concurrent API calls (must be >= 1, default: 4)",
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

    # Print summary table to terminal
    print("\n" + "=" * 80)
    print(f"{'Model':<20} | {'Pass Rate':<10} | {'Passed':<8} | {'Avg Time':<10} | {'Tokens':<10} | {'Est. Cost':<10}")
    print("-" * 80)
    for s in summaries.values():
        pass_str = f"{s.pass_rate_percent}%"
        passed_str = f"{s.passed_tests}/{s.total_tests}"
        time_str = f"{s.avg_latency_seconds}s"
        cost_str = f"${s.total_estimated_cost_usd:.5f}"
        print(
            f"{s.model:<20} | {pass_str:<10} | {passed_str:<8} | {time_str:<10} | {s.total_tokens:<10} | {cost_str:<10}"
        )
    print("=" * 80 + "\n")

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
