"""Test helpers for formatting validation results in human-readable reports."""

from typing import List

from src.validation_rules import ValidationResult


def format_validation_report(results: List[ValidationResult]) -> str:
    """
    Format validation results as a human-readable report.

    Args:
        results: List of validation results to format

    Returns:
        Formatted report string
    """
    if not results:
        return "No validation issues found."

    # Group by severity
    errors = [r for r in results if r.severity == ValidationResult.SEVERITY_ERROR]
    warnings = [r for r in results if r.severity == ValidationResult.SEVERITY_WARNING]
    info = [r for r in results if r.severity == ValidationResult.SEVERITY_INFO]

    lines = []
    lines.append("=" * 80)
    lines.append("VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  Total Issues: {len(results)}")
    lines.append(f"  Errors: {len(errors)}")
    lines.append(f"  Warnings: {len(warnings)}")
    lines.append(f"  Info: {len(info)}")
    lines.append("")

    # Errors section
    if errors:
        lines.append("─" * 80)
        lines.append(f"ERRORS ({len(errors)})")
        lines.append("─" * 80)
        for idx, result in enumerate(errors, 1):
            lines.append("")
            lines.append(f"  [{idx}] Rule: {result.rule_name.upper()}")
            if result.affected_product:
                product_id = result.affected_product.get("id", "unknown")
                product_name = result.affected_product.get("name", "unnamed")
                lines.append(f"      Product ID: {product_id}")
                lines.append(f"      Product Name: {product_name}")
            lines.append(f"      Message: {result.message}")
        lines.append("")

    # Warnings section
    if warnings:
        lines.append("─" * 80)
        lines.append(f"WARNINGS ({len(warnings)})")
        lines.append("─" * 80)
        for idx, result in enumerate(warnings, 1):
            lines.append("")
            lines.append(f"  [{idx}] Rule: {result.rule_name.upper()}")
            if result.affected_product:
                product_id = result.affected_product.get("id", "unknown")
                product_name = result.affected_product.get("name", "unnamed")
                lines.append(f"      Product ID: {product_id}")
                lines.append(f"      Product Name: {product_name}")
            lines.append(f"      Message: {result.message}")
        lines.append("")

    # Info section (usually empty, but included for completeness)
    if info:
        lines.append("─" * 80)
        lines.append(f"INFO ({len(info)})")
        lines.append("─" * 80)
        for idx, result in enumerate(info, 1):
            lines.append("")
            lines.append(f"  [{idx}] Rule: {result.rule_name.upper()}")
            if result.affected_product:
                product_id = result.affected_product.get("id", "unknown")
                product_name = result.affected_product.get("name", "unnamed")
                lines.append(f"      Product ID: {product_id}")
                lines.append(f"      Product Name: {product_name}")
            lines.append(f"      Message: {result.message}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def assert_no_validation_errors(
    results: List[ValidationResult],
    message: str = "Validation errors found",
) -> None:
    """
    Assert that no validation errors exist, with formatted output on failure.

    Args:
        results: List of validation results
        message: Custom message prefix

    Raises:
        AssertionError: If any errors are found
    """
    errors = [r for r in results if r.severity == ValidationResult.SEVERITY_ERROR]
    if errors:
        report = format_validation_report(results)
        raise AssertionError(f"{message}:\n\n{report}")


def assert_validation_count(
    results: List[ValidationResult],
    expected_count: int,
    severity: str = None,
    message: str = None,
) -> None:
    """
    Assert validation result count with formatted output on failure.

    Args:
        results: List of validation results
        expected_count: Expected number of results
        severity: Optional severity filter (error, warning, info)
        message: Custom message prefix

    Raises:
        AssertionError: If count doesn't match
    """
    if severity:
        filtered = [r for r in results if r.severity == severity]
        actual_count = len(filtered)
        severity_label = severity.upper()
    else:
        actual_count = len(results)
        severity_label = "TOTAL"

    if actual_count != expected_count:
        default_message = (
            f"Expected {expected_count} {severity_label} validation result(s), "
            f"got {actual_count}"
        )
        error_message = message or default_message
        report = format_validation_report(results)
        raise AssertionError(f"{error_message}:\n\n{report}")


def assert_validation_contains(
    results: List[ValidationResult],
    rule_name: str = None,
    severity: str = None,
    message_substring: str = None,
    product_id: str = None,
) -> None:
    """
    Assert that validation results contain expected criteria.

    Args:
        results: List of validation results
        rule_name: Expected rule name
        severity: Expected severity level
        message_substring: Expected substring in message
        product_id: Expected product ID

    Raises:
        AssertionError: If no matching result found
    """
    matches = results

    if rule_name:
        matches = [r for r in matches if r.rule_name == rule_name]
    if severity:
        matches = [r for r in matches if r.severity == severity]
    if message_substring:
        matches = [
            r for r in matches if message_substring.lower() in r.message.lower()
        ]
    if product_id:
        matches = [
            r
            for r in matches
            if r.affected_product
            and str(r.affected_product.get("id")) == str(product_id)
        ]

    if not matches:
        criteria = []
        if rule_name:
            criteria.append(f"rule_name='{rule_name}'")
        if severity:
            criteria.append(f"severity='{severity}'")
        if message_substring:
            criteria.append(f"message contains '{message_substring}'")
        if product_id:
            criteria.append(f"product_id='{product_id}'")

        criteria_str = ", ".join(criteria) if criteria else "any criteria"
        error_message = f"No validation result found matching {criteria_str}"
        report = format_validation_report(results)
        raise AssertionError(f"{error_message}:\n\n{report}")
