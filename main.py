"""Entry point for acis2llm."""

import argparse
import sys

from cli import run_cli
from config import reset_config
from acis2llm_setup import run_setup


def main():
    """Parse arguments and start the application."""
    parser = argparse.ArgumentParser(
        prog="acis2llm",
        description="Weather data analysis CLI powered by local LLM",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run setup wizard",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Override endpoint URL",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Override model name",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override API key",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output including raw traces",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run a single non-interactive query",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for LLM API calls in seconds (default: 60)",
    )

    args = parser.parse_args()

    if args.setup:
        run_setup()
        return

    if args.reset:
        reset_config()
        print("Configuration reset. Run 'acis2llm --setup' to configure.")
        return

    flag_overrides = {}
    if args.endpoint is not None:
        flag_overrides["endpoint_url"] = args.endpoint
    if args.model is not None:
        flag_overrides["model"] = args.model
    if args.api_key is not None:
        flag_overrides["api_key"] = args.api_key

    if args.query:
        from cli import run_single_query
        from config import load_config
        config = load_config(flag_overrides)
        if config is None:
            print("ERROR: No configuration found. Run 'acis2llm --setup' first.")
            sys.exit(1)
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=config["endpoint_url"],
                api_key=config["api_key"] if config["api_key"] else "not-needed",
                timeout=args.timeout,
            )
            run_single_query(args.query, config, client)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        return

    run_cli(flag_overrides, args.verbose, timeout=args.timeout)


if __name__ == "__main__":
    main()
