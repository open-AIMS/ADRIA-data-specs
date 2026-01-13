from typing import List, Optional, Union
from pydantic import BaseModel, Field

# Import validators from the separate module
from validators import ADRIANetCDF, DomainValidator

class Source(BaseModel):
    title: str
    description: Optional[str] = ""
    path: Optional[str] = None
    handle: Optional[str] = ""

class SimulationMetadata(BaseModel):
    timeframe: List[int]

class Contributor(BaseModel):
    title: str
    email: Optional[str] = None
    role: Optional[str] = "author"
    description: Optional[str] = None

class Resource(BaseModel):
    name: str
    description: Optional[str] = ""
    path: str
    format: str = "unknown"

    # Spatial specific optional fields
    location_id_col: Optional[str] = None
    cluster_id_col: Optional[str] = None
    k_col: Optional[str] = None
    area_col: Optional[str] = None
    data: Optional[List[str]] = None  # For identifying column names or variables

class DataPackage(BaseModel):
    name: str
    title: str
    description: str = "Generated ADRIA Domain"
    version: str
    sources: List[Source] = Field(default_factory=list)
    simulation_metadata: SimulationMetadata
    contributors: List[Contributor] = Field(default_factory=list)
    resources: List[Resource] = Field(default_factory=list)