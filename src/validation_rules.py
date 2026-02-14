"""Validation rules for product catalog consistency checks."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a single validation rule check."""

    def __init__(
        self,
        rule_name: str,
        passed: bool,
        message: str,
        product_id: Optional[str] = None,
    ):
        """
        Initialize validation result.

        Args:
            rule_name: Name of the validation rule
            passed: Whether the validation passed
            message: Descriptive message about the result
            product_id: Optional product identifier if rule applies to specific product
        """
        self.rule_name = rule_name
        self.passed = passed
        self.message = message
        self.product_id = product_id

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        product_info = f" [{self.product_id}]" if self.product_id else ""
        return f"{status}: {self.rule_name}{product_info} - {self.message}"


class ValidationRule:
    """Base class for validation rules."""

    def __init__(self, name: str):
        """
        Initialize validation rule.

        Args:
            name: Name of the rule
        """
        self.name = name

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate catalog against this rule.

        Args:
            catalog: Catalog dictionary to validate

        Returns:
            List of validation results
        """
        raise NotImplementedError


class RequiredFieldsRule(ValidationRule):
    """Validates that all products have required fields."""

    REQUIRED_FIELDS = ["id", "name", "price", "category"]

    def __init__(self):
        super().__init__("required_fields")

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """Check that all products have required fields."""
        results = []
        products = catalog.get("products", [])

        for product in products:
            product_id = product.get("id", "unknown")
            missing_fields = [
                field for field in self.REQUIRED_FIELDS if field not in product
            ]

            if missing_fields:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message=f"Missing required fields: {', '.join(missing_fields)}",
                        product_id=str(product_id),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=True,
                        message="All required fields present",
                        product_id=str(product_id),
                    )
                )

        return results


class PriceConsistencyRule(ValidationRule):
    """Validates price format and consistency."""

    def __init__(self):
        super().__init__("price_consistency")

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """Check that prices are valid numbers and non-negative."""
        results = []
        products = catalog.get("products", [])

        for product in products:
            product_id = product.get("id", "unknown")
            price = product.get("price")

            if price is None:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message="Price is missing",
                        product_id=str(product_id),
                    )
                )
                continue

            try:
                price_float = float(price)
                if price_float < 0:
                    results.append(
                        ValidationResult(
                            rule_name=self.name,
                            passed=False,
                            message=f"Price is negative: {price_float}",
                            product_id=str(product_id),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            rule_name=self.name,
                            passed=True,
                            message=f"Price is valid: {price_float}",
                            product_id=str(product_id),
                        )
                    )
            except (ValueError, TypeError):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message=f"Price is not a valid number: {price}",
                        product_id=str(product_id),
                    )
                )

        return results


class UniqueIdRule(ValidationRule):
    """Validates that all product IDs are unique."""

    def __init__(self):
        super().__init__("unique_ids")

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """Check that all product IDs are unique."""
        results = []
        products = catalog.get("products", [])
        seen_ids: Dict[str, List[int]] = {}

        for idx, product in enumerate(products):
            product_id = product.get("id")
            if product_id is None:
                continue

            product_id_str = str(product_id)
            if product_id_str in seen_ids:
                seen_ids[product_id_str].append(idx)
            else:
                seen_ids[product_id_str] = [idx]

        duplicates = {id: indices for id, indices in seen_ids.items() if len(indices) > 1}

        if duplicates:
            for product_id, indices in duplicates.items():
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message=f"Duplicate ID found at indices: {indices}",
                        product_id=product_id,
                    )
                )
        else:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    passed=True,
                    message="All product IDs are unique",
                )
            )

        return results


class CategoryConsistencyRule(ValidationRule):
    """Validates category field consistency."""

    def __init__(self):
        super().__init__("category_consistency")

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """Check that categories are non-empty strings."""
        results = []
        products = catalog.get("products", [])

        for product in products:
            product_id = product.get("id", "unknown")
            category = product.get("category")

            if not category:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message="Category is missing or empty",
                        product_id=str(product_id),
                    )
                )
            elif not isinstance(category, str):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=False,
                        message=f"Category must be a string, got {type(category).__name__}",
                        product_id=str(product_id),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        passed=True,
                        message=f"Category is valid: {category}",
                        product_id=str(product_id),
                    )
                )

        return results


def get_default_rules() -> List[ValidationRule]:
    """
    Get list of default validation rules.

    Returns:
        List of validation rule instances
    """
    return [
        RequiredFieldsRule(),
        PriceConsistencyRule(),
        UniqueIdRule(),
        CategoryConsistencyRule(),
    ]
