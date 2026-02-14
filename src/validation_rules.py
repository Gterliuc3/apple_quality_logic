"""Validation rules for product catalog consistency checks."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationResult:
    """Structured failure report for a validation rule check."""

    SEVERITY_ERROR = "error"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    def __init__(
        self,
        rule_name: str,
        severity: str,
        message: str,
        affected_product: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize validation result.

        Args:
            rule_name: Name of the validation rule
            severity: Severity level (error, warning, info)
            message: Descriptive message about the result
            affected_product: Optional product dictionary if rule applies to specific product
        """
        if severity not in [self.SEVERITY_ERROR, self.SEVERITY_WARNING, self.SEVERITY_INFO]:
            raise ValueError(f"Invalid severity: {severity}")

        self.rule_name = rule_name
        self.severity = severity
        self.message = message
        self.affected_product = affected_product

    @property
    def is_failure(self) -> bool:
        """Check if this result represents a failure (error or warning)."""
        return self.severity in [self.SEVERITY_ERROR, self.SEVERITY_WARNING]

    @property
    def product_id(self) -> Optional[str]:
        """Extract product ID from affected_product if available."""
        if self.affected_product:
            return str(self.affected_product.get("id", "unknown"))
        return None

    def __repr__(self) -> str:
        product_info = f" [Product: {self.product_id}]" if self.product_id else ""
        return f"[{self.severity.upper()}] {self.rule_name}{product_info}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for structured reporting."""
        result = {
            "rule_name": self.rule_name,
            "severity": self.severity,
            "message": self.message,
        }
        if self.affected_product:
            result["affected_product"] = {
                "id": self.affected_product.get("id"),
                "name": self.affected_product.get("name"),
            }
        return result


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
            missing_fields = [
                field for field in self.REQUIRED_FIELDS if field not in product
            ]

            if missing_fields:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message=f"Missing required fields: {', '.join(missing_fields)}",
                        affected_product=product,
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
            price = product.get("price")

            if price is None:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message="Price is missing",
                        affected_product=product,
                    )
                )
                continue

            try:
                price_float = float(price)
                if price_float < 0:
                    results.append(
                        ValidationResult(
                            rule_name=self.name,
                            severity=ValidationResult.SEVERITY_ERROR,
                            message=f"Price is negative: {price_float}",
                            affected_product=product,
                        )
                    )
                elif price_float == 0:
                    results.append(
                        ValidationResult(
                            rule_name=self.name,
                            severity=ValidationResult.SEVERITY_WARNING,
                            message="Price is zero - verify if this is intentional",
                            affected_product=product,
                        )
                    )
            except (ValueError, TypeError):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message=f"Price is not a valid number: {price} (type: {type(price).__name__})",
                        affected_product=product,
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
        seen_ids: Dict[str, List[Dict[str, Any]]] = {}

        for product in products:
            product_id = product.get("id")
            if product_id is None:
                continue

            product_id_str = str(product_id)
            if product_id_str in seen_ids:
                seen_ids[product_id_str].append(product)
            else:
                seen_ids[product_id_str] = [product]

        duplicates = {id: products_list for id, products_list in seen_ids.items() if len(products_list) > 1}

        if duplicates:
            for product_id, duplicate_products in duplicates.items():
                product_names = [p.get("name", "unnamed") for p in duplicate_products]
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message=f"Duplicate ID '{product_id}' found in {len(duplicate_products)} products: {', '.join(product_names)}",
                        affected_product=duplicate_products[0],  # Report first occurrence
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
            category = product.get("category")

            if not category:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message="Category is missing or empty",
                        affected_product=product,
                    )
                )
            elif not isinstance(category, str):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_ERROR,
                        message=f"Category must be a string, got {type(category).__name__}: {category}",
                        affected_product=product,
                    )
                )
            elif len(category.strip()) == 0:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationResult.SEVERITY_WARNING,
                        message="Category is whitespace-only",
                        affected_product=product,
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
