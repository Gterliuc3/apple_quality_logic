"""Tests for validation rules module."""

import pytest

from src.validation_rules import (
    CategoryConsistencyRule,
    PriceConsistencyRule,
    RequiredFieldsRule,
    UniqueIdRule,
    ValidationResult,
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
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert results[0].is_failure is True
        assert "price" in results[0].message or "category" in results[0].message
        assert results[0].affected_product == product

    def test_multiple_products(self):
        """Test validation handles multiple products."""
        rule = RequiredFieldsRule()
        product1 = {"id": "1", "name": "P1", "price": 10.0, "category": "C1"}
        product2 = {"id": "2", "name": "P2"}
        catalog = {"products": [product1, product2]}
        results = rule.validate(catalog)
        assert len(results) == 1  # Only product2 has missing fields
        assert results[0].affected_product == product2

    def test_all_fields_missing(self):
        """Test validation when all required fields are missing."""
        rule = RequiredFieldsRule()
        product = {"description": "Some product"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert all(field in results[0].message for field in ["id", "name", "price", "category"])


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
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert "negative" in results[0].message.lower()
        assert results[0].affected_product == product

    def test_zero_price(self):
        """Test validation warns for zero prices."""
        rule = PriceConsistencyRule()
        product = {"id": "1", "price": 0}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_WARNING
        assert "zero" in results[0].message.lower()

    def test_missing_price(self):
        """Test validation fails when price is missing."""
        rule = PriceConsistencyRule()
        product = {"id": "1"}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert "missing" in results[0].message.lower()
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
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert "Duplicate" in results[0].message
        assert "P1" in results[0].message or "P2" in results[0].message
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
        assert len(results) == 2  # One result per duplicate ID


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
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert results[0].affected_product == product

    def test_empty_category(self):
        """Test validation fails for empty category strings."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": ""}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert results[0].affected_product == product

    def test_whitespace_only_category(self):
        """Test validation warns for whitespace-only categories."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": "   "}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_WARNING
        assert "whitespace" in results[0].message.lower()

    def test_non_string_category(self):
        """Test validation fails for non-string categories."""
        rule = CategoryConsistencyRule()
        product = {"id": "1", "category": 123}
        catalog = {"products": [product]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].severity == ValidationResult.SEVERITY_ERROR
        assert "string" in results[0].message.lower()


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
