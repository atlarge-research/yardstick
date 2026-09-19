"""Command-line entry point: ``yardstick <command>``.

    yardstick init experiment.toml       write a commented starter config
    yardstick validate experiment.toml   check it without deploying anything
    yardstick run experiment.toml        run the benchmark
    yardstick list                       show the built-in games and workloads

Also reachable as ``python -m yardstick_benchmark``.
"""

import argparse
import logging
import sys
from pathlib import Path

from yardstick_benchmark.config import (
    EXAMPLE_CONFIG,
    GAMES,
    WORKLOADS,
    BenchmarkConfig,
    ConfigError,
)


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "config",
        type=Path,
        help="path to a TOML benchmark configuration",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yardstick",
        description="Benchmark Minecraft-like game servers.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="log each deployment step",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run a benchmark")
    _add_config_arg(run_parser)
    run_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="results directory (default: <output.dir>/<workload>-<timestamp>)",
    )

    validate_parser = sub.add_parser(
        "validate", help="check a configuration without deploying anything"
    )
    _add_config_arg(validate_parser)

    init_parser = sub.add_parser("init", help="write a starter configuration")
    init_parser.add_argument("config", type=Path, help="file to create")
    init_parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite an existing file"
    )

    sub.add_parser("list", help="list the built-in games and workloads")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "list":
        print("games:")
        for name, cls in sorted(GAMES.items()):
            print(f"  {name:12s} {cls.__module__}.{cls.__qualname__}")
        print("workloads:")
        for name, cls in sorted(WORKLOADS.items()):
            print(f"  {name:12s} {cls.__module__}.{cls.__qualname__}")
        print(
            "\nAny of these can also be given as a dotted import path in a "
            "configuration file, so your own classes work the same way."
        )
        return 0

    if args.command == "init":
        if args.config.exists() and not args.force:
            print(
                f"{args.config} already exists; pass --force to overwrite",
                file=sys.stderr,
            )
            return 1
        args.config.parent.mkdir(parents=True, exist_ok=True)
        args.config.write_text(EXAMPLE_CONFIG)
        print(f"wrote {args.config}")
        print(f"run it with: yardstick run {args.config}")
        return 0

    try:
        config = BenchmarkConfig.from_toml(args.config)
        config.validate()
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(f"{args.config}: ok")
        print(f"  game:     {config.game} ({config.game_class.__name__})")
        print(f"  workload: {config.workload} ({config.workload_class.__name__})")
        print(f"  server:   {config.deployment.resolved_server_host()}")
        print(f"  players:  {', '.join(config.deployment.workload_hosts())}")
        return 0

    # Imported here so `validate`, `init` and `list` stay usable on a machine
    # without apptainer or a reachable database.
    from yardstick_benchmark.runner import run

    try:
        results = run(config, results_dir=args.output)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"results: {results}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
