from pathlib import Path
from typing import List, Optional
import geopandas as gpd
from schemas import DataPackage

def load_geopackage_ids(domain_path: Path, dpkg: DataPackage) -> Optional[List[str]]:
    """
    Finds the spatial GeoPackage in the DataPackage and extracts the location IDs.
    Returns None if no suitable spatial resource is found or if the file is missing.
    """
    
    # 1. Find the spatial resource
    spatial_res = next((r for r in dpkg.resources if r.format.lower() == "geopackage"), None)
    
    if not spatial_res:
        spatial_res = next((r for r in dpkg.resources if r.name == "spatial_data"), None)
        
    if not spatial_res:
        print("  [WARNING] No spatial resource found in datapackage.json. Cannot validate IDs.")
        return None

    # 2. Resolve Path
    gpkg_path = domain_path / spatial_res.path
    if not gpkg_path.exists():
        print(f"  [ERROR] Spatial file missing at {gpkg_path}")
        return None

    # 3. Determine ID Column
    id_col = spatial_res.location_id_col or "reef_siteid"
    
    print(f"  [INFO] Loading location IDs from {gpkg_path.name} (Column: '{id_col}')...")

    try:
        # 4. Load with GeoPandas
        gdf = gpd.read_file(gpkg_path)
        
        if id_col not in gdf.columns:
            if not spatial_res.location_id_col and "UNIQUE_ID" in gdf.columns:
                print(f"  [INFO] Column '{id_col}' not found. Falling back to 'UNIQUE_ID'.")
                id_col = "UNIQUE_ID"
            else:
                print(f"  [ERROR] ID Column '{id_col}' not found in GeoPackage. Available columns: {list(gdf.columns)}")
                return None
        
        ids = gdf[id_col].astype(str).tolist()
        print(f"  [OK] Loaded {len(ids)} location IDs.")
        return ids

    except Exception as e:
        print(f"  [ERROR] Failed to read GeoPackage: {e}")
        return None
