"""Tests for catalog loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from src.catalog_loader import CatalogLoadError, CatalogLoader


class TestCatalogLoader:
    """Test cases for CatalogLoader."""

    def test_load_valid_catalog(self):
        """Test loading a valid catalog file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            catalog_data = {"products": [{"id": "1", "name": "Test"}]}
            json.dump(catalog_data, f)
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            catalog = loader.load()
            assert catalog == catalog_data
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        loader = CatalogLoader(Path("nonexistent.json"))
        with pytest.raises(CatalogLoadError, match="not found"):
            loader.load()

    def test_load_invalid_json(self):
        """Test loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            with pytest.raises(CatalogLoadError, match="Invalid JSON"):
                loader.load()
        finally:
            temp_path.unlink()

    def test_load_non_object_json(self):
        """Test loading JSON that is not an object raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            with pytest.raises(CatalogLoadError, match="must be a JSON object"):
                loader.load()
        finally:
            temp_path.unlink()

    def test_get_products(self):
        """Test extracting products from catalog."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            catalog_data = {
                "products": [{"id": "1", "name": "Product 1"}, {"id": "2", "name": "Product 2"}]
            }
            json.dump(catalog_data, f)
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            products = loader.get_products()
            assert len(products) == 2
            assert products[0]["id"] == "1"
        finally:
            temp_path.unlink()

    def test_get_products_empty_catalog(self):
        """Test getting products from catalog without products key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            catalog_data = {"version": "1.0"}
            json.dump(catalog_data, f)
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            products = loader.get_products()
            assert products == []
        finally:
            temp_path.unlink()

    def test_get_catalog_metadata(self):
        """Test extracting catalog metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            catalog_data = {
                "version": "1.0",
                "last_updated": "2024-01-01",
                "products": [{"id": "1"}],
            }
            json.dump(catalog_data, f)
            temp_path = Path(f.name)

        try:
            loader = CatalogLoader(temp_path)
            metadata = loader.get_catalog_metadata()
            assert "version" in metadata
            assert "last_updated" in metadata
            assert "products" not in metadata
        finally:
            temp_path.unlink()
