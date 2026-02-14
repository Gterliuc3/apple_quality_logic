# Product Catalog Validation Tool

Internal quality validation tool for validating product catalog consistency.

## Overview

This tool validates product catalog data for consistency, completeness, and correctness. It provides a modular architecture with clear separation of concerns:

- **Catalog Loader**: Loads and parses JSON catalog files
- **Validation Rules**: Defines validation logic for catalog consistency
- **Rule Engine**: Executes validation rules and aggregates results

## Project Structure

```
apple_quality_logic/
├── src/
│   ├── catalog_loader.py    # Catalog loading and parsing
│   ├── validation_rules.py  # Validation rule definitions
│   └── rule_engine.py       # Rule execution engine
├── tests/                   # Test suite
├── data/
│   └── sample_catalog.json  # Sample catalog data
└── requirements.txt         # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from pathlib import Path
from src.catalog_loader import CatalogLoader
from src.rule_engine import RuleEngine

# Load catalog
loader = CatalogLoader(Path("data/sample_catalog.json"))
catalog = loader.load()

# Validate
engine = RuleEngine()
results = engine.validate_with_summary(catalog)

# Check results
print(f"Passed: {results['summary']['passed']}")
print(f"Failed: {results['summary']['failed']}")
```

## Validation Rules

The tool includes the following validation rules:

- **Required Fields**: Ensures all products have required fields (id, name, price, category)
- **Price Consistency**: Validates price format and ensures non-negative values
- **Unique IDs**: Ensures all product IDs are unique
- **Category Consistency**: Validates category field format and presence

## Testing

Run the test suite:

```bash
pytest tests/
```

## Development

The codebase follows production-style practices:
- Type hints for better code clarity
- Comprehensive error handling
- Logging for debugging and monitoring
- Modular design for extensibility
