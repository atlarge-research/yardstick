"""Command-line entry point: ``yardstick <command>``.

    yardstick init experiment.toml       write a commented starter config
    yardstick validate experiment.toml   check it without deploying anything
    yardstick run experiment.toml        run the benchmark
    yardstick list                       show the built-in games and workloads
    yardstick machines list              show machines Yardstick provisioned
    yardstick machines release           give them all back

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

    cloud_parser = sub.add_parser(
        "machines",
        help="inspect or release machines Yardstick provisioned",
    )
    cloud_parser.add_argument(
        "action",
        choices=["list", "release"],
        help="'list' shows what is on record; 'release' gives it all back",
    )
    cloud_parser.add_argument(
        "-p",
        "--provider",
        default="ubicloud",
        help="provider whose ledger to act on (default: ubicloud)",
    )
    return parser


def _warn_if_not_ready_to_provision(config) -> None:
    """Report anything about *this machine* that would stop a run starting."""
    from yardstick_benchmark.config import build_kwargs
    from yardstick_benchmark.provisioning import ProvisioningError

    provider = config.provider_class
    try:
        pool = provider(
            **build_kwargs(
                provider, config.provisioning.options_for("server"), where=""
            )
        )
    except Exception:
        return
    resolve = getattr(pool, "resolve_ssh_public_key", None)
    if callable(resolve):
        try:
            resolve()
        except ProvisioningError as exc:
            print(f"\nwarning: {exc}", file=sys.stderr)
            print(
                "         The configuration is valid; this machine just "
                "cannot provision yet.",
                file=sys.stderr,
            )


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

    if args.command == "machines":
        from yardstick_benchmark.config import PROVIDERS, resolve

        try:
            provider = resolve(args.provider, PROVIDERS, "provider")()
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        records = provider.acquired()
        if args.action == "list":
            if not records:
                print(f"no machines on record ({provider.ledger.path})")
                return 0
            print(f"machines on record in {provider.ledger.path}:")
            for record in records:
                print(f"  {record['ref']:48s} {record.get('host') or '(no address)'}")
            return 0
        if not records:
            print("nothing to release")
            return 0
        # Identifier-driven, like every other release path: this walks the
        # ledger Yardstick wrote, never the provider's inventory.
        released = provider.release_all()
        print(f"released {len(released)} machine(s)")
        for ref in released:
            print(f"  {ref}")
        remaining = provider.acquired()
        if remaining:
            print(
                f"warning: {len(remaining)} still on record; "
                f"see {provider.ledger.path}",
                file=sys.stderr,
            )
            return 1
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
        print(f"  mode:     {config.deployment.mode}")
        print(f"  game:     {config.game} ({config.game_class.__name__})")
        print(f"  workload: {config.workload} ({config.workload_class.__name__})")
        if config.deployment.mode == "local":
            print(f"  server:   {config.deployment.resolved_server_host()}")
            print(f"  players:  {', '.join(config.deployment.workload_hosts())}")
        else:
            # The machines don't exist yet, so report what will be acquired
            # rather than the local-mode host lists, which mean nothing here.
            provisioning = config.provisioning
            print(f"  provider: {provisioning.provider}")
            server_opts = provisioning.options_for("server")
            workload_opts = provisioning.options_for("workload")
            print(
                f"  server:   1 machine ({server_opts.get('size', 'provider default')})"
            )
            print(
                f"  players:  {provisioning.workload_nodes} machine(s) "
                f"({workload_opts.get('size', 'provider default')})"
            )
            # The configuration can be perfectly valid while this machine is
            # not yet able to act on it, so this is a warning rather than an
            # error -- a config is often checked somewhere other than where
            # it will run.
            _warn_if_not_ready_to_provision(config)
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
