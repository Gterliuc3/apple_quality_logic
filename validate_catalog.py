#!/usr/bin/env python3
"""Command-line script for validating product catalogs."""

import logging
import sys
from pathlib import Path

from src.catalog_loader import CatalogLoadError, CatalogLoader
from src.rule_engine import RuleEngine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main(catalog_path: Path) -> int:
    """
    Validate a product catalog.

    Args:
        catalog_path: Path to catalog JSON file

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        loader = CatalogLoader(catalog_path)
        catalog = loader.load()

        engine = RuleEngine()
        output = engine.validate_with_summary(catalog)

        summary = output["summary"]
        print(f"\nValidation Summary:")
        print(f"  Total checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")

        if summary["failed"] > 0:
            print(f"\nFailed validations:")
            for result in output["results"]:
                if not result.passed:
                    print(f"  {result}")

        return 0 if summary["failed"] == 0 else 1

    except CatalogLoadError as e:
        print(f"Error loading catalog: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <catalog.json>", file=sys.stderr)
        sys.exit(1)

    catalog_path = Path(sys.argv[1])
    sys.exit(main(catalog_path))
