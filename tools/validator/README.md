# ADRIA Domain Validator

A CLI tool to validate ADRIA Domain Data Packages.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) must be installed.

## Usage

Run the validator from this directory:

```bash
uv run src/main.py <path_to_domain_directory>
```

## Checks Performed

1.  **Schema Validation**: Verifies `datapackage.json` against the expected Pydantic schema.
2.  **Resource Existence**: Checks that all files listed in `resources` exist.
3.  **Naming Conventions**: Ensures the spatial GeoPackage matches the domain name (e.g., `spatial/MyDomain.gpkg`).
4.  **Directory Structure**: Checks for standard subdirectories (connectivity, cyclones, etc.).

## Development

Project is managed with `uv`.

- Install dependencies: `uv sync`
- Add dependencies: `uv add <package>`
