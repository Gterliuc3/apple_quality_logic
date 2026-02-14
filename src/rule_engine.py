"""Rule engine for executing validation rules against product catalogs."""

import logging
from typing import Any, Dict, List, Optional

from .validation_rules import ValidationResult, ValidationRule

# Re-export for convenience
__all__ = ["RuleEngine", "ValidationResult"]

logger = logging.getLogger(__name__)


class RuleEngine:
    """Engine for executing validation rules against catalogs."""

    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        """
        Initialize rule engine.

        Args:
            rules: Optional list of validation rules. If None, uses default rules.
        """
        from .validation_rules import get_default_rules

        self.rules = rules if rules is not None else get_default_rules()
        logger.info(f"Initialized rule engine with {len(self.rules)} rules")

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """
        Execute all rules against the catalog.

        Args:
            catalog: Catalog dictionary to validate

        Returns:
            List of all validation results from all rules
        """
        all_results: List[ValidationResult] = []

        for rule in self.rules:
            try:
                results = rule.validate(catalog)
                all_results.extend(results)
                logger.debug(f"Rule '{rule.name}' produced {len(results)} results")
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")
                all_results.append(
                    ValidationResult(
                        rule_name=rule.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message=f"Rule execution error: {str(e)}",
                    )
                )

        return all_results

    def validate_with_summary(
        self, catalog: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate catalog and return results with summary statistics.

        Args:
            catalog: Catalog dictionary to validate

        Returns:
            Dictionary containing results and summary statistics
        """
        results = self.validate(catalog)

        error_count = sum(1 for r in results if r.severity == ValidationResult.SEVERITY_ERROR)
        warning_count = sum(1 for r in results if r.severity == ValidationResult.SEVERITY_WARNING)
        info_count = sum(1 for r in results if r.severity == ValidationResult.SEVERITY_INFO)
        failure_count = error_count + warning_count

        rule_summary: Dict[str, Dict[str, int]] = {}
        for result in results:
            if result.rule_name not in rule_summary:
                rule_summary[result.rule_name] = {
                    "error": 0,
                    "warning": 0,
                    "info": 0,
                }
            rule_summary[result.rule_name][result.severity] += 1

        return {
            "results": results,
            "summary": {
                "total_issues": len(results),
                "errors": error_count,
                "warnings": warning_count,
                "info": info_count,
                "failures": failure_count,
                "rules": rule_summary,
            },
        }
