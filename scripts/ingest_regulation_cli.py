"""CLI for manual regulatory document ingestion."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a regulatory PDF")
    parser.add_argument("file", type=Path, help="Path to regulatory PDF")
    parser.add_argument("--regulator", required=True, help="Regulator code (RBI, SEBI, etc.)")
    parser.add_argument("--title", required=True, help="Regulation title")
    parser.add_argument("--version", required=True, help="Version identifier")
    args = parser.parse_args()

    print(f"Ingesting {args.file} for {args.regulator}...")
    # TODO: call IngestionService directly or dispatch Celery task


if __name__ == "__main__":
    main()
