"""Entry-point: python -m fledge <config.toml>"""

import argparse
import logging
import sys

from fledge.daemon import run_from_config_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fledge",
        description="Minimal periodic job queue daemon.",
    )
    parser.add_argument(
        "config",
        metavar="CONFIG",
        help="Path to the TOML configuration file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    try:
        run_from_config_file(args.config)
    except FileNotFoundError as exc:
        logging.error("Config file not found: %s", exc)
        return 1
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
