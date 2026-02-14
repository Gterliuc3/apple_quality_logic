"""Catalog loader module for loading and parsing product catalog data."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CatalogLoadError(Exception):
    """Raised when catalog loading fails."""

    pass


class CatalogLoader:
    """Loads and validates basic structure of product catalog JSON files."""

    def __init__(self, catalog_path: Path):
        """
        Initialize catalog loader.

        Args:
            catalog_path: Path to the catalog JSON file
        """
        self.catalog_path = Path(catalog_path)
        self._catalog: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load catalog from JSON file.

        Returns:
            Parsed catalog dictionary

        Raises:
            CatalogLoadError: If file cannot be loaded or parsed
        """
        if not self.catalog_path.exists():
            raise CatalogLoadError(f"Catalog file not found: {self.catalog_path}")

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self._catalog = json.load(f)
        except json.JSONDecodeError as e:
            raise CatalogLoadError(f"Invalid JSON in catalog file: {e}") from e
        except IOError as e:
            raise CatalogLoadError(f"Error reading catalog file: {e}") from e

        if not isinstance(self._catalog, dict):
            raise CatalogLoadError("Catalog must be a JSON object")

        logger.info(f"Loaded catalog from {self.catalog_path}")
        return self._catalog

    def get_products(self) -> List[Dict[str, Any]]:
        """
        Extract products list from catalog.

        Returns:
            List of product dictionaries
        """
        if not self._catalog:
            self.load()

        products = self._catalog.get("products", [])
        if not isinstance(products, list):
            return []

        return products

    def get_catalog_metadata(self) -> Dict[str, Any]:
        """
        Extract catalog-level metadata.

        Returns:
            Dictionary of catalog metadata (excluding products)
        """
        if not self._catalog:
            self.load()

        metadata = {k: v for k, v in self._catalog.items() if k != "products"}
        return metadata
