"""Tests for validation rules module."""

import pytest

from src.validation_rules import (
    CategoryConsistencyRule,
    PriceConsistencyRule,
    PricingHierarchyRule,
    RequiredFieldsRule,
    UniqueIdRule,
    ValidationResult,
)
from tests.test_helpers import (
    assert_no_validation_errors,
    assert_validation_contains,
    assert_validation_count,
    format_validation_report,
)


class TestRequiredFieldsRule:
    """Test cases for RequiredFieldsRule."""

    def test_all_fields_present(self):
        """Test validation passes when all required fields are present."""
        rule = RequiredFieldsRule()
        catalog = {
            "products": [
                {"id": "1", "name": "Product", "price": 10.0, "category": "Test"}
            ]
        }
        results = rule.validate(catalog)
        assert len(results) == 0  # No failures when all fields present

    def test_missing_fields(self):
        """Test validation fails when required fields are missing."""
        rule = RequiredFieldsRule()
        product = {"id": "1", "name": "Product"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)

        assert_validation_contains(
            results,
            rule_name="required_fields",
            severity=ValidationResult.SEVERITY_ERROR,
            product_id="1",
        )
        # Verify message contains expected fields
        assert any(
            "price" in r.message.lower() or "category" in r.message.lower()
            for r in results
        ), f"Expected price or category in message. Report:\n{format_validation_report(results)}"
        assert results[0].affected_product == product

    def test_multiple_products(self):
        """Test validation handles multiple products."""
        rule = RequiredFieldsRule()
        product1 = {"id": "1", "name": "P1", "price": 10.0, "category": "C1"}
        product2 = {"id": "2", "name": "P2"}
        catalog = {"products": [product1, product2]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1)
        assert_validation_contains(
            results,
            rule_name="required_fields",
            product_id="2",
        )
        assert results[0].affected_product == product2

    def test_all_fields_missing(self):
        """Test validation when all required fields are missing."""
        rule = RequiredFieldsRule()
        product = {"description": "Some product"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        # Verify all required fields are mentioned
        message = results[0].message.lower()
        assert all(
            field in message for field in ["id", "name", "price", "category"]
        ), f"Expected all required fields in message. Report:\n{format_validation_report(results)}"


class TestPriceConsistencyRule:
    """Test cases for PriceConsistencyRule."""

    def test_valid_price(self):
        """Test validation passes for valid prices."""
        rule = PriceConsistencyRule()
        catalog = {"products": [{"id": "1", "price": 10.99}]}
        results = rule.validate(catalog)
        assert len(results) == 0  # No failures for valid prices

    def test_negative_price(self):
        """Test validation fails for negative prices."""
        rule = PriceConsistencyRule()
        product = {"id": "1", "price": -5.0}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="price_consistency",
            severity=ValidationResult.SEVERITY_ERROR,
            message_substring="negative",
            product_id="1",
        )
        assert results[0].affected_product == product

    def test_zero_price(self):
        """Test validation warns for zero prices."""
        rule = PriceConsistencyRule()
        product = {"id": "1", "price": 0}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_WARNING)
        assert_validation_contains(
            results,
            rule_name="price_consistency",
            severity=ValidationResult.SEVERITY_WARNING,
            message_substring="zero",
        )

    def test_missing_price(self):
        """Test validation fails when price is missing."""
        rule = PriceConsistencyRule()
        product = {"id": "1"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="price_consistency",
            severity=ValidationResult.SEVERITY_ERROR,
            message_substring="missing",
        )
        assert results[0].affected_product == product

    def test_invalid_price_type(self):
        """Test validation fails for non-numeric prices."""
        rule = PriceConsistencyRule()
        product = {"id": "1", "price": "not a number"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert "not a valid number" in results[0].message


class TestUniqueIdRule:
    """Test cases for UniqueIdRule."""

    def test_unique_ids(self):
        """Test validation passes when all IDs are unique."""
        rule = UniqueIdRule()
        catalog = {
            "products": [
                {"id": "1", "name": "P1"},
                {"id": "2", "name": "P2"},
            ]
        }
        results = rule.validate(catalog)
        assert len(results) == 0  # No failures when IDs are unique

    def test_duplicate_ids(self):
        """Test validation fails when duplicate IDs are found."""
        rule = UniqueIdRule()
        product1 = {"id": "1", "name": "P1"}
        product2 = {"id": "1", "name": "P2"}
        catalog = {"products": [product1, product2]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="unique_ids",
            severity=ValidationResult.SEVERITY_ERROR,
            message_substring="duplicate",
        )
        # Verify product names are in the message
        assert any(
            "P1" in r.message or "P2" in r.message for r in results
        ), f"Expected product names in duplicate message. Report:\n{format_validation_report(results)}"
        assert results[0].affected_product in [product1, product2]

    def test_multiple_duplicates(self):
        """Test validation handles multiple duplicate IDs."""
        rule = UniqueIdRule()
        catalog = {
            "products": [
                {"id": "1", "name": "P1"},
                {"id": "1", "name": "P2"},
                {"id": "2", "name": "P3"},
                {"id": "2", "name": "P4"},
            ]
        }
        results = rule.validate(catalog)
        assert_validation_count(results, expected_count=2, severity=ValidationResult.SEVERITY_ERROR)


class TestCategoryConsistencyRule:
    """Test cases for CategoryConsistencyRule."""

    def test_valid_category(self):
        """Test validation passes for valid category strings."""
        rule = CategoryConsistencyRule()
        catalog = {"products": [{"id": "1", "category": "Electronics"}]}
        results = rule.validate(catalog)
        assert len(results) == 0  # No failures for valid categories

    def test_missing_category(self):
        """Test validation fails when category is missing."""
        rule = CategoryConsistencyRule()
        product = {"id": "1"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="category_consistency",
            severity=ValidationResult.SEVERITY_ERROR,
            product_id="1",
        )
        assert results[0].affected_product == product

    def test_empty_category(self):
        """Test validation fails for empty category strings."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": ""}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="category_consistency",
            severity=ValidationResult.SEVERITY_ERROR,
            message_substring="missing or empty",
        )
        assert results[0].affected_product == product

    def test_whitespace_only_category(self):
        """Test validation warns for whitespace-only categories."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": "   "}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_WARNING)
        assert_validation_contains(
            results,
            rule_name="category_consistency",
            severity=ValidationResult.SEVERITY_WARNING,
            message_substring="whitespace",
        )

    def test_non_string_category(self):
        """Test validation fails for non-string categories."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": 123}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        
        assert_validation_count(results, expected_count=1, severity=ValidationResult.SEVERITY_ERROR)
        assert_validation_contains(
            results,
            rule_name="category_consistency",
            severity=ValidationResult.SEVERITY_ERROR,
            message_substring="string",
        )


class TestValidationResult:
    """Test cases for ValidationResult."""

    def test_result_creation(self):
        """Test creating validation result with severity."""
        product = {"id": "1", "name": "Test"}
        result = ValidationResult(
            "test_rule",
            ValidationResult.SEVERITY_ERROR,
            "Test message",
            product,
        )
        assert result.rule_name == "test_rule"
        assert result.severity == ValidationResult.SEVERITY_ERROR
        assert result.message == "Test message"
        assert result.affected_product == product
        assert result.is_failure is True

    def test_result_severity_levels(self):
        """Test different severity levels."""
        error_result = ValidationResult("rule", ValidationResult.SEVERITY_ERROR, "msg")
        warning_result = ValidationResult("rule", ValidationResult.SEVERITY_WARNING, "msg")
        info_result = ValidationResult("rule", ValidationResult.SEVERITY_INFO, "msg")

        assert error_result.is_failure is True
        assert warning_result.is_failure is True
        assert info_result.is_failure is False

    def test_result_invalid_severity(self):
        """Test that invalid severity raises error."""
        with pytest.raises(ValueError, match="Invalid severity"):
            ValidationResult("rule", "invalid", "msg")

    def test_result_repr(self):
        """Test string representation of validation result."""
        product = {"id": "PROD-001", "name": "Test Product"}
        result = ValidationResult(
            "test_rule",
            ValidationResult.SEVERITY_ERROR,
            "Test message",
            product,
        )
        repr_str = repr(result)
        assert "ERROR" in repr_str
        assert "test_rule" in repr_str
        assert "PROD-001" in repr_str

    def test_result_repr_no_product(self):
        """Test string representation without product."""
        result = ValidationResult(
            "test_rule", ValidationResult.SEVERITY_WARNING, "Test message"
        )
        repr_str = repr(result)
        assert "WARNING" in repr_str
        assert "test_rule" in repr_str

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        product = {"id": "1", "name": "Test Product", "price": 10.0}
        result = ValidationResult(
            "test_rule",
            ValidationResult.SEVERITY_ERROR,
            "Test message",
            product,
        )
        result_dict = result.to_dict()
        assert result_dict["rule_name"] == "test_rule"
        assert result_dict["severity"] == ValidationResult.SEVERITY_ERROR
        assert result_dict["message"] == "Test message"
        assert result_dict["affected_product"]["id"] == "1"
        assert result_dict["affected_product"]["name"] == "Test Product"

    def test_result_product_id_property(self):
        """Test product_id property extraction."""
        product = {"id": "PROD-123", "name": "Test"}
        result = ValidationResult("rule", ValidationResult.SEVERITY_ERROR, "msg", product)
        assert result.product_id == "PROD-123"

    def test_result_product_id_none(self):
        """Test product_id property when no product."""
        result = ValidationResult("rule", ValidationResult.SEVERITY_ERROR, "msg")
        assert result.product_id is None


class TestPricingHierarchyRule:
    """Test cases for PricingHierarchyRule."""

    def test_valid_hierarchy(self):
        """Test validation passes when hierarchy is correct."""
        rule = PricingHierarchyRule()
        catalog = {
            "products": [
                {"id": "1", "name": "iPhone 15", "price": 799.0, "category": "Electronics"},
                {"id": "2", "name": "iPhone 15 Plus", "price": 899.0, "category": "Electronics"},
                {"id": "3", "name": "iPhone 15 Pro", "price": 999.0, "category": "Electronics"},
                {"id": "4", "name": "iPhone 15 Pro Max", "price": 1099.0, "category": "Electronics"},
            ]
        }
        results = rule.validate(catalog)
        assert len(results) == 0  # No violations

    def test_equal_prices_violation(self):
        """Test that equal prices between tiers trigger violation."""
        rule = PricingHierarchyRule()
        base_product = {"id": "1", "name": "iPhone 15", "price": 999.0, "category": "Electronics"}
        plus_product = {"id": "2", "name": "iPhone 15 Plus", "price": 999.0, "category": "Electronics"}
        catalog = {"products": [base_product, plus_product]}
        results = rule.validate(catalog)
        
        assert len(results) > 0, f"Expected pricing violations for equal prices. Report:\n{format_validation_report(results)}"
        assert_validation_count(results, expected_count=2, severity=ValidationResult.SEVERITY_ERROR)
