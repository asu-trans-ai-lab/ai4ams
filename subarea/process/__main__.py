"""CLI: python -m subarea.process {prepare|run} subarea_run.yml"""
import argparse
import json
import sys

from .config import load_config
from .prepare import prepare


def main():
    ap = argparse.ArgumentParser(prog="subarea.process",
                                 description="FR-19 v2 config-driven subarea trajectory pipeline")
    ap.add_argument("command", choices=["prepare", "run"])
    ap.add_argument("config", help="path to subarea_run.yml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    manifest = prepare(cfg)
    print(json.dumps(manifest, indent=2))

    if args.command == "run":
        print("\n[subarea.process] prepare complete. kernel_run stage: NOT YET IMPLEMENTED "
              "(FR-19 implementation-order step 3 — kernel DTAT streamer pending review gate). "
              "Prepared artifacts are kernel-ready in:", cfg["output_folder"])
        sys.exit(0)


if __name__ == "__main__":
    main()
