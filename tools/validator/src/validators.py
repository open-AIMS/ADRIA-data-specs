from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator, AfterValidator, ValidationInfo

import xarray as xr
import pandas as pd
import geopandas as gpd

def load_nc(path: str) -> xr.Dataset:
    print(f"  [INFO] Validating NetCDF file: {path}")
    try:
        ds = xr.open_dataset(path)
        ds.load()
        return ds
    except Exception as e:
        msg = f"Failed to open NetCDF: {e}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

def check_variable_existence(ds: xr.Dataset, expected_var: str, field_name: str):
    if expected_var and expected_var not in ds.data_vars:
        msg = f"Resource '{field_name}' must contain variable: '{expected_var}'"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    return

def check_dimensions(ds: xr.DataArray, expected_dims: List[str], field_name: str):
    actual_dims = list(ds.dims)
    missing = [d for d in expected_dims if d not in actual_dims]
    if missing:
        msg = f"Resource '{field_name}' missing dimensions: {missing}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    indices = [actual_dims.index(d) for d in expected_dims]
    if indices != sorted(indices):
        msg = f"Resource '{field_name}' dimension order incorrect. Expected: {expected_dims}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    return ds

def check_location_ids(ds: xr.DataArray, expected_ids: List[str], var: str, field_name: str):
    if "locations" not in ds.dims:
        msg = f"Resource '{field_name}' missing 'locations' dimension."
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    # Access the coordinate values directly
    actual_ids = set(ds.coords["locations"].values.astype(str))
    missing_ids = set(expected_ids) - actual_ids

    if missing_ids:
        # Show a sample of missing IDs
        sample = list(missing_ids)[:3]
        msg = f"Resource '{field_name}' missing {len(missing_ids)} IDs from GeoPackage (e.g. {sample})."
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    return

def validate_netcdf_resource(ds: xr.Dataset, info: ValidationInfo) -> xr.Dataset:
    context = info.context

    field_name = info.field_name
    specs = context.get("specs", {}).get(field_name)

    if not specs:
        return ds # No spec for this resource, skip detailed checks

    expected_variable = specs.get("variable")
    check_variable_existence(ds, expected_variable, field_name)

    data_v = ds.data_vars[expected_variable]

    expected_dimsions = specs.get("dimensions")
    check_dimensions(data_v, expected_dimsions, field_name)

    expected_ids = context.get("expected_ids")
    check_location_ids(data_v, expected_ids, expected_variable, field_name)

    return ds

def load_csv(path: str) -> pd.DataFrame:
    print(f"  [INFO] Validating CSV file: {path}")
    try:
        df = pd.read_csv(path, index_col=0)
        return df
    except Exception as e:
        msg = f"Failed to read CSV: {e}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

def validate_connectivity_matrix(df: pd.DataFrame, info: ValidationInfo) -> pd.DataFrame:
    context = info.context
    expected_ids = context.get("expected_ids")

    if not expected_ids:
        return df

    expected_set = set(expected_ids)

    row_ids = set(df.index.astype(str))
    missing_rows = expected_set - row_ids
    if missing_rows:
         sample = list(missing_rows)[:3]
         msg = f"Connectivity matrix missing {len(missing_rows)} row IDs (e.g., {sample})"
         print(f"      [ERROR] {msg}")
         raise ValueError(msg)

    col_ids = set(df.columns.astype(str))
    missing_cols = expected_set - col_ids
    if missing_cols:
         sample = list(missing_cols)[:3]
         msg = f"Connectivity matrix missing {len(missing_cols)} column IDs (e.g., {sample})"
         print(f"      [ERROR] {msg}")
         raise ValueError(msg)

    return df

def load_geopackage(path: str) -> gpd.GeoDataFrame:
    print(f"  [INFO] Validating GeoPackage file: {path}")
    try:
        gdf = gpd.read_file(path)
        return gdf
    except Exception as e:
        msg = f"Failed to read GeoPackage: {e}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

def validate_geopackage(gdf: gpd.GeoDataFrame, info: ValidationInfo) -> gpd.GeoDataFrame:
    context = info.context
    resource = context.get("spatial_resource")

    # Check for geometry column
    if "geometry" not in gdf.columns and "geom" not in gdf.columns:
         msg = "GeoPackage must contain a geometry column ('geometry' or 'geom')"
         print(f"      [ERROR] {msg}")
         raise ValueError(msg)

    # Determine expected column names with defaults
    location_id_col = getattr(resource, "location_id_col", None) or "reef_siteid"
    cluster_id_col = getattr(resource, "cluster_id_col", None) or "cluster_id"
    k_col = getattr(resource, "k_col", None) or "k"
    area_col = getattr(resource, "area_col", None) or "area"

    required_cols = {
        "Location ID": location_id_col,
        "Cluster ID": cluster_id_col,
        "Carrying Capacity (k)": k_col,
        "Area": area_col
    }

    missing_cols = []
    for label, col_name in required_cols.items():
        if col_name not in gdf.columns:
            missing_cols.append(f"{label} ('{col_name}')")

    if missing_cols:
        msg = f"GeoPackage missing required columns: {', '.join(missing_cols)}"
        print(f"      [ERROR] {msg}")
        raise ValueError(msg)

    return gdf

ADRIANetCDF = Annotated[
    xr.Dataset,
    BeforeValidator(load_nc),
    AfterValidator(validate_netcdf_resource)
]

ConnectivityCSV = Annotated[
    pd.DataFrame,
    BeforeValidator(load_csv),
    AfterValidator(validate_connectivity_matrix)
]

SpatialGeoPackage = Annotated[
    gpd.GeoDataFrame,
    BeforeValidator(load_geopackage),
    AfterValidator(validate_geopackage)
]

class DomainValidator(BaseModel):
    dhw: List[ADRIANetCDF]
    waves: Optional[ADRIANetCDF] = None
    cyclone_mortality: Optional[ADRIANetCDF] = None
    coral_cover: ADRIANetCDF
    connectivity: List[ConnectivityCSV]
    spatial_data: Optional[SpatialGeoPackage] = None

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }
