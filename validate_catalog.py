#!/usr/bin/env python3
"""Command-line script for validating product catalogs."""

import logging
import sys
from pathlib import Path

from src.catalog_loader import CatalogLoadError, CatalogLoader
from src.rule_engine import RuleEngine
from src.validation_rules import ValidationResult

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
        print(f"  Total issues: {summary['total_issues']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Warnings: {summary['warnings']}")
        print(f"  Info: {summary['info']}")
        print(f"  Total failures: {summary['failures']}")

        if summary["failures"] > 0:
            print(f"\nIssues by severity:")
            
            errors = [r for r in output["results"] if r.severity == ValidationResult.SEVERITY_ERROR]
            warnings = [r for r in output["results"] if r.severity == ValidationResult.SEVERITY_WARNING]
            
            if errors:
                print(f"\n  ERRORS ({len(errors)}):")
                for result in errors:
                    print(f"    {result}")
            
            if warnings:
                print(f"\n  WARNINGS ({len(warnings)}):")
                for result in warnings:
                    print(f"    {result}")

        if summary["rules"]:
            print(f"\nIssues by rule:")
            for rule_name, counts in summary["rules"].items():
                if counts["error"] > 0 or counts["warning"] > 0:
                    print(f"  {rule_name}: {counts['error']} errors, {counts['warning']} warnings")

        return 0 if summary["errors"] == 0 else 1

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
