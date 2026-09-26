#!/usr/bin/env python3
"""CLI Script: Package model and artifacts for deployment."""

import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Package Kent-AI model artifacts.")
    parser.add_argument("--output-dir", type=str, default="dist/model_bundle")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Exporting model bundle to {args.output_dir}...")
    print("Export pipeline ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
