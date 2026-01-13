import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from pydantic import ValidationError

from schemas import DataPackage
from validators import DomainValidator
from utils import load_geopackage_ids

SPECS = {
    "dhw": {
        "variable": "dhw",
        "dimensions": ["timesteps", "locations", "scenarios"],
    },
    "waves": {
        "variable": "Ub",
        "dimensions": ["timesteps", "locations", "scenarios"],
    },
    "cyclone_mortality": {
        "variable": "cyclone_mortality",
        "dimensions": ["timesteps", "species", "locations", "scenarios"],
    },
    "coral_cover": {
        "variable": "coral_cover",
        "dimensions": ["species", "locations"]
    }
}

def validate_resource(res, res_path) -> bool:
    if not res_path.exists():
        print(f"  [ERROR] Missing Resource: '{res.name}' at path '{res.path}'")
        return False

    if res_path.is_dir():
        print(f"  [OK] Found directory resource: '{res.name}' ({res.path}/)")
    else:
        print(f"  [OK] Found file resource: '{res.name}' ({res.path})")

    return True

def collect_resource_files(res, res_path, validation_inputs):
    if res_path.is_dir():
        validation_inputs[res.name] = [str(file.resolve()) for file in res_path.iterdir()]
    else:
        validation_inputs[res.name] = str(res_path.resolve())

def validate_domain(domain_path: Path):
    global SPECS
    success = True

    print(f"Validating Domain at: {domain_path}")
    dpkg_path = domain_path / "datapackage.json"
    if not dpkg_path.exists():
        print(f"[ERROR] datapackage.json not found at {dpkg_path}")
        return False

    with open(dpkg_path, "r") as f:
        data = json.load(f)

    dpkg = DataPackage(**data)
    print("[OK] datapackage.json schema is valid.")

    print("\nChecking resources defined in datapackage.json...")
    validation_inputs = {
    }

    spatial_res = None

    for resource in dpkg.resources:
        resource_path = domain_path / resource.path
        if not validate_resource(resource, resource_path):
            success = False
            continue

        collect_resource_files(resource, resource_path, validation_inputs)
        if resource.name == "spatial_data":
            spatial_res = resource


    print("\nChecking naming conventions...")
    expected_gpkg_name = f"{dpkg.name}.gpkg"
    spatial_res = next((r for r in dpkg.resources if r.format.lower() == "geopackage"), None)

    if spatial_res:
        gpkg_filename = Path(spatial_res.path).name
        if gpkg_filename != expected_gpkg_name:
            print(f"  [ERROR] Naming Convention: Spatial GeoPackage should be named '{expected_gpkg_name}', found '{gpkg_filename}'")
            success = False
        else:
            print(f"  [OK] Spatial GeoPackage naming correct: {gpkg_filename}")
    else:
         print("  [INFO] No GeoPackage resource found; skipping naming convention check.")

    print("\nValidating Content (NetCDF & Connectivity)...")

    expected_ids = load_geopackage_ids(domain_path, dpkg)
    if expected_ids is None:
        print("  [WARNING] Could not load location IDs from GeoPackage. Skipping ID validation.")

    context = {
        "specs": SPECS,
        "expected_ids": expected_ids,
        "spatial_resource": spatial_res
    }

    clean_inputs = {k: v for k, v in validation_inputs.items() if v}

    try:
        DomainValidator.model_validate(clean_inputs, context=context)
        print("  [OK] All data files match specifications and GeoPackage IDs.")
    except ValidationError as e:
        print("  [ERROR] Content Validation Failed.")
        success = False
    except Exception as e:
        print(f"  [ERROR] Unexpected validation error: {e}")
        success = False

    return success

def main():
    parser = argparse.ArgumentParser(description="Validate an ADRIA Domain Data Package")
    parser.add_argument("domain_path", type=str, help="Path to the Domain directory")
    args = parser.parse_args()

    domain_path = Path(args.domain_path).resolve()

    if not domain_path.exists() or not domain_path.is_dir():
        print(f"[ERROR] Path '{domain_path}' does not exist or is not a directory.")
        sys.exit(1)

    is_valid = validate_domain(domain_path)

    if is_valid:
        print("\nDomain Status: VALID")
        sys.exit(0)
    else:
        print("\nDomain Status: INVALID")
        sys.exit(1)

if __name__ == "__main__":
    main()
