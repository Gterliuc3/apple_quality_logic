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
        assert len(results) == 1
        assert results[0].passed is True

    def test_missing_fields(self):
        """Test validation fails when required fields are missing."""
        rule = RequiredFieldsRule()
        catalog = {"products": [{"id": "1", "name": "Product"}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False
        assert "price" in results[0].message or "category" in results[0].message

    def test_multiple_products(self):
        """Test validation handles multiple products."""
        rule = RequiredFieldsRule()
        catalog = {
            "products": [
                {"id": "1", "name": "P1", "price": 10.0, "category": "C1"},
                {"id": "2", "name": "P2"},
            ]
        }
        results = rule.validate(catalog)
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False


class TestPriceConsistencyRule:
    """Test cases for PriceConsistencyRule."""

    def test_valid_price(self):
        """Test validation passes for valid prices."""
        rule = PriceConsistencyRule()
        catalog = {"products": [{"id": "1", "price": 10.99}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is True

    def test_negative_price(self):
        """Test validation fails for negative prices."""
        rule = PriceConsistencyRule()
        catalog = {"products": [{"id": "1", "price": -5.0}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False
        assert "negative" in results[0].message.lower()

    def test_missing_price(self):
        """Test validation fails when price is missing."""
        rule = PriceConsistencyRule()
        catalog = {"products": [{"id": "1"}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False
        assert "missing" in results[0].message.lower()

    def test_invalid_price_type(self):
        """Test validation fails for non-numeric prices."""
        rule = PriceConsistencyRule()
        catalog = {"products": [{"id": "1", "price": "not a number"}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False


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
        assert any(r.passed for r in results)
        assert not any(not r.passed for r in results)

    def test_duplicate_ids(self):
        """Test validation fails when duplicate IDs are found."""
        rule = UniqueIdRule()
        catalog = {
            "products": [
                {"id": "1", "name": "P1"},
                {"id": "1", "name": "P2"},
            ]
        }
        results = rule.validate(catalog)
        assert any(not r.passed for r in results)
        assert "Duplicate" in results[0].message


class TestCategoryConsistencyRule:
    """Test cases for CategoryConsistencyRule."""

    def test_valid_category(self):
        """Test validation passes for valid category strings."""
        rule = CategoryConsistencyRule()
        catalog = {"products": [{"id": "1", "category": "Electronics"}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is True

    def test_missing_category(self):
        """Test validation fails when category is missing."""
        rule = CategoryConsistencyRule()
        catalog = {"products": [{"id": "1"}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False

    def test_empty_category(self):
        """Test validation fails for empty category strings."""
        rule = CategoryConsistencyRule()
        catalog = {"products": [{"id": "1", "category": ""}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False

    def test_non_string_category(self):
        """Test validation fails for non-string categories."""
        rule = CategoryConsistencyRule()
        catalog = {"products": [{"id": "1", "category": 123}]}
        results = rule.validate(catalog)
        assert len(results) == 1
        assert results[0].passed is False


class TestValidationResult:
    """Test cases for ValidationResult."""

    def test_result_repr(self):
        """Test string representation of validation result."""
        result = ValidationResult("test_rule", True, "Test message", "PROD-001")
        repr_str = repr(result)
        assert "PASS" in repr_str
        assert "test_rule" in repr_str
        assert "PROD-001" in repr_str

    def test_result_repr_no_product_id(self):
        """Test string representation without product ID."""
        result = ValidationResult("test_rule", False, "Test message")
        repr_str = repr(result)
        assert "FAIL" in repr_str
        assert "test_rule" in repr_str
