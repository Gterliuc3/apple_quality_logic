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
        assert len(results) > 0
        assert all(isinstance(r, ValidationResult) for r in results)

    def test_validate_with_custom_rules(self):
        """Test validation with custom rules."""
        class TestRule(ValidationRule):
            def validate(self, catalog):
                return [ValidationResult("test", True, "Test message")]

        custom_rules = [TestRule("custom")]
        engine = RuleEngine(rules=custom_rules)
        catalog = {"products": []}
        results = engine.validate(catalog)
        assert len(results) == 1
        assert results[0].rule_name == "test"

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
        assert "total_checks" in output["summary"]
        assert "passed" in output["summary"]
        assert "failed" in output["summary"]
        assert "rules" in output["summary"]

    def test_validate_handles_rule_errors(self):
        """Test that rule engine handles rule execution errors gracefully."""
        class FailingRule(ValidationRule):
            def validate(self, catalog):
                raise ValueError("Test error")

        engine = RuleEngine(rules=[FailingRule("failing")])
        catalog = {"products": []}
        results = engine.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False
        assert "error" in results[0].message.lower()
