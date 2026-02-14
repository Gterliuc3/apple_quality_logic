"""Tests for rule engine module."""

from src.rule_engine import RuleEngine
from src.validation_rules import ValidationRule, ValidationResult


class TestRuleEngine:
    """Test cases for RuleEngine."""

    def test_validate_with_default_rules(self):
        """Test validation with default rules."""
        engine = RuleEngine()
        catalog = {
            "products": [
                {"id": "1", "name": "Product", "price": 10.0, "category": "Test"}
            ]
        }
        results = engine.validate(catalog)
        assert all(isinstance(r, ValidationResult) for r in results)

    def test_validate_with_custom_rules(self):
        """Test validation with custom rules."""
        class TestRule(ValidationRule):
            def validate(self, catalog):
                return [
                    ValidationResult(
                        "test",
                        ValidationResult.SEVERITY_WARNING,
                        "Test message",
                    )
                ]

        custom_rules = [TestRule("custom")]
        engine = RuleEngine(rules=custom_rules)
        catalog = {"products": []}
        results = engine.validate(catalog)
        assert len(results) == 1
        assert results[0].rule_name == "test"
        assert results[0].severity == ValidationResult.SEVERITY_WARNING

    def test_validate_with_summary(self):
        """Test validation with summary statistics."""
        engine = RuleEngine()
        catalog = {
            "products": [
                {"id": "1", "name": "Product", "price": 10.0, "category": "Test"}
            ]
        }
        output = engine.validate_with_summary(catalog)
        assert "results" in output
        assert "summary" in output
        assert "total_issues" in output["summary"]
        assert "errors" in output["summary"]
        assert "warnings" in output["summary"]
        assert "info" in output["summary"]
        assert "failures" in output["summary"]
        assert "rules" in output["summary"]

    def test_validate_with_summary_counts(self):
        """Test that summary correctly counts severity levels."""
        class ErrorRule(ValidationRule):
            def validate(self, catalog):
                return [
                    ValidationResult(
                        "error_rule",
                        ValidationResult.SEVERITY_ERROR,
                        "Error message",
                    )
                ]

        class WarningRule(ValidationRule):
            def validate(self, catalog):
                return [
                    ValidationResult(
                        "warning_rule",
                        ValidationResult.SEVERITY_WARNING,
                        "Warning message",
                    )
                ]

        engine = RuleEngine(rules=[ErrorRule("error"), WarningRule("warning")])
        catalog = {"products": []}
        output = engine.validate_with_summary(catalog)
        summary = output["summary"]
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["failures"] == 2
        assert summary["total_issues"] == 2

    def test_validate_handles_rule_errors(self):
        """Test that rule engine handles rule execution errors gracefully."""
        class FailingRule(ValidationRule):
            def validate(self, catalog):
                raise ValueError("Test error")

        engine = RuleEngine(rules=[FailingRule("failing")])
        catalog = {"products": []}
        results = engine.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert results[0].is_failure is True
        assert "error" in results[0].message.lower()

    def test_validate_summary_by_rule(self):
        """Test that summary groups results by rule name."""
        engine = RuleEngine()
        catalog = {
            "products": [
                {"id": "1", "name": "Product", "price": -5.0, "category": "Test"}
            ]
        }
        output = engine.validate_with_summary(catalog)
        rule_summary = output["summary"]["rules"]
        assert "price_consistency" in rule_summary
        assert rule_summary["price_consistency"]["error"] > 0
