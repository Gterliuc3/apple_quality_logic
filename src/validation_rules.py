"""Validation rules for product catalog consistency checks."""

import logging
from typing import Any, Dict, List, Optional, Tuple

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


class PricingHierarchyRule(ValidationRule):
    """Validates pricing hierarchy within product families."""

    # Hierarchy levels in order (lower index = lower price expected)
    HIERARCHY_LEVELS = ["base", "plus", "pro", "pro max"]
    HIERARCHY_ORDER = {level: idx for idx, level in enumerate(HIERARCHY_LEVELS)}

    def __init__(self):
        super().__init__("pricing_hierarchy")

    def _extract_family_name(self, product_name: str) -> str:
        """
        Extract product family name by removing hierarchy suffixes.

        Args:
            product_name: Full product name

        Returns:
            Base family name (e.g., "iPhone 15" from "iPhone 15 Pro Max")
        """
        name_lower = product_name.lower().strip()
        
        # Remove hierarchy suffixes in reverse order (longest first)
        for level in reversed(self.HIERARCHY_LEVELS):
            # Handle variations: "Pro Max", "ProMax", "Pro-Max", etc.
            patterns = [
                f" {level}",
                level,
                level.replace(" ", "-"),
                level.replace(" ", ""),
            ]
            for pattern in patterns:
                if name_lower.endswith(pattern):
                    name_lower = name_lower[: -len(pattern)].strip()
                    break
        
        return name_lower

    def _detect_hierarchy_level(self, product_name: str) -> Optional[str]:
        """
        Detect hierarchy level from product name.

        Args:
            product_name: Full product name

        Returns:
            Hierarchy level name or None if not detected
        """
        name_lower = product_name.lower().strip()
        
        # Check for hierarchy levels, longest first to avoid partial matches
        for level in reversed(self.HIERARCHY_LEVELS):
            # Handle variations: "Pro Max", "ProMax", "Pro-Max", etc.
            # Check end of string first (most specific)
            if name_lower.endswith(level):
                return level
            if name_lower.endswith(level.replace(" ", "-")):
                return level
            if name_lower.endswith(level.replace(" ", "")):
                return level
            # Check for space-separated version in the name
            if f" {level}" in name_lower:
                return level
            if f"-{level}" in name_lower:
                return level
        
        # If no hierarchy level found, assume "base"
        return "base"

    def _group_by_family(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group products by family name.

        Args:
            products: List of product dictionaries

        Returns:
            Dictionary mapping family names to product lists
        """
        families: Dict[str, List[Dict[str, Any]]] = {}
        
        for product in products:
            name = product.get("name", "")
            if not name:
                continue
            
            family_name = self._extract_family_name(name)
            if family_name not in families:
                families[family_name] = []
            families[family_name].append(product)
        
        # Only return families with multiple hierarchy levels
        return {
            family: products
            for family, products in families.items()
            if len(products) > 1
        }

    def validate(self, catalog: Dict[str, Any]) -> List[ValidationResult]:
        """Check pricing hierarchy within product families."""
        results = []
        products = catalog.get("products", [])

        # Filter products with valid prices
        valid_products = []
        for product in products:
            price = product.get("price")
            if price is None:
                continue
            try:
                float(price)
                valid_products.append(product)
            except (ValueError, TypeError):
                continue

        if len(valid_products) < 2:
            return results  # Need at least 2 products to compare

        # Group products by family
        families = self._group_by_family(valid_products)

        for family_name, family_products in families.items():
            # Build hierarchy map: level -> list of (product, price) tuples
            hierarchy_map: Dict[str, List[Tuple[Dict[str, Any], float]]] = {}
            
            for product in family_products:
                name = product.get("name", "")
                price = float(product.get("price", 0))
                level = self._detect_hierarchy_level(name)
                
                if level not in hierarchy_map:
                    hierarchy_map[level] = []
                hierarchy_map[level].append((product, price))

            # Check pricing order within family
            levels_present = sorted(
                hierarchy_map.keys(),
                key=lambda l: self.HIERARCHY_ORDER.get(l, 999)
            )

            # Compare each level with higher levels
            for i, lower_level in enumerate(levels_present):
                lower_products = hierarchy_map[lower_level]
                lower_max_price = max(price for _, price in lower_products)

                for higher_level in levels_present[i + 1:]:
                    higher_products = hierarchy_map[higher_level]
                    higher_min_price = min(price for _, price in higher_products)

                    # Violation: lower tier price >= higher tier price
                    if lower_max_price >= higher_min_price:
                        # Find the violating products
                        violating_lower = [
                            (p, price)
                            for p, price in lower_products
                            if price >= higher_min_price
                        ]
                        violating_higher = [
                            (p, price)
                            for p, price in higher_products
                            if price <= lower_max_price
                        ]

                        # Report violations
                        for product, price in violating_lower:
                            results.append(
                                ValidationResult(
                                    rule_name=self.name,
                                    severity=ValidationResult.SEVERITY_ERROR,
                                    message=(
                                        f"Pricing violation in '{family_name}' family: "
                                        f"{lower_level.upper()} tier (${price:.2f}) should be "
                                        f"less than {higher_level.upper()} tier "
                                        f"(min: ${higher_min_price:.2f})"
                                    ),
                                    affected_product=product,
                                )
                            )

                        for product, price in violating_higher:
                            results.append(
                                ValidationResult(
                                    rule_name=self.name,
                                    severity=ValidationResult.SEVERITY_ERROR,
                                    message=(
                                        f"Pricing violation in '{family_name}' family: "
                                        f"{higher_level.upper()} tier (${price:.2f}) should be "
                                        f"greater than {lower_level.upper()} tier "
                                        f"(max: ${lower_max_price:.2f})"
                                    ),
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
        PricingHierarchyRule(),
    ]
