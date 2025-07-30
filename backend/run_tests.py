#!/usr/bin/env python3
"""
Test runner script for the FastAPI application.
"""

import os
import subprocess
import sys


def run_tests(test_type="all", coverage=True, verbose=False):
    """Run tests with optional coverage and verbosity."""

    # Change to the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.extend(["-q"])

    # Add coverage if requested
    if coverage:
        cmd.extend(
            [
                "--cov=app",
                "--cov=main",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )

    # Select test type
    if test_type == "unit":
        cmd.extend(["-m", "not integration and not performance"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type != "all":
        cmd.append(f"tests/test_{test_type}.py")

    # Add tests directory
    if test_type == "all":
        cmd.append("tests/")

    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    """Main function to handle command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Run FastAPI tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "integration",
            "performance",
            "main",
            "auth",
            "items",
            "users",
        ],
        help="Type of tests to run",
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Run tests without coverage"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run tests with verbose output"
    )

    args = parser.parse_args()

    result = run_tests(
        test_type=args.test_type, coverage=not args.no_coverage, verbose=args.verbose
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
