Example ADRIA data package specifications

- Example_domain : see "Domain" section
- Example_domain_RCPs45_2022-09 ... : see "Result Set" section
- example_scenarios.csv : See "Scenario file" section
- example_model_spec.csv : See "Model details" section
- README.md : this file

Data packages are a simple, flexible, container format for collections of data.
The specification outlined here is used to ensure consistency in filenames, locations, and formats.

See [here](https://specs.frictionlessdata.io/data-package/) for an overview of what a `data package` is.


# Domain

The `Domain` data package contains the necessary data/information to run simulations with
ADRIA.

```
Example_domain    # Unique name for Input Set / study domain
├───connectivity  # (Sub-)directories holding CSVs of connectivity data (grouped by year)
│   └───2000
├───DHWs          # netCDF-based data cubes holding DHW data (one for each RCP/SSP scenario)
├───site_data     # Spatial data (currently a geopackage defining sites and a netCDF holding initial coral covers)
└───waves         # netCDF holding wave stress data
datapackage.json
README.md
```

With the exception of connectivity data, all filenames are expected to follow the same naming conventions
as indicated by the files found in their respective folders. For example, DHW data are expected to follow
`dhwRCP[RCP scenario ID].nc` (e.g., `dhwRCP45.nc`), geopackage file must have the same name as the domain, etc.

A future improvement is to store relevant metadata mapping filenames to their locations within the
data package, their dimensions and format, and other ancillary information in the `datapackage.json`
file instead. Locations of external data (e.g., an S3 bucket or other cloud-based store) could
then also be specified (and loaded from those locations).

Pertinent part of the datapackage spec is shown below (with comments):

```json
"name": "Example_domain",
  "title": "Example reef cluster data package",
  "description": "Example data package for ADRIA",
  "version": "v0.2.1",                             // Used to ensure compatibility with current ADRIA version 
  "sources": [],
  "simulation_metadata": {
    "timeframe": [2025, 2099]
  }
```


# Result Set

```
Example_domain__RCPs45__2022-09-01_17_05_28_067
├───inputs                        # Post-processed scenario (model run) inputs in Zarr format
├───logs                          # Logs relevant to the decision making process represented inside ADRIA
│   ├───fog
│   ├───rankings
│   ├───seed
│   └───shade
├───results                       # Store of calculated metric outcomes (the number of these will increase)
│   ├───absolute_shelter_volume
│   ├───relative_cover
│   └───relative_shelter_volume
└───site_data                     # Copy of geopackage representing study area/domain
```

Result Set is not currently defined as a datapackage (but it should be, eventually).
All data, with the exception of spatial data, are stored in Zarr format.

ADRIA now only stores outcomes for each metric to reduce storage size.

Result Set directory name follows the convention of:

`[Input Set name]__RCPs[RCPs represented]__[Datetime of run]`

Note that each element are separated by double underscores (__).

A limitation with the current version is that model scenarios can only be run for a single RCP at a time.
The workaround is to run model scenarios for individual RCPs separately, and combine the results after the fact.

An example of the combined ResultSet holding runs under RCP 4.5, 2.6 and 8.0 would be:

`Example_domain__RCPs45_26_80__2022-09-01_17_41_00_001`

where the datetime indicates when the time at which the ResultSets were combined.


# Scenario file

```
example_scenarios.csv
```

CSV file defining a set of scenarios to run (see example use further below)

# ADRIA configuration file

Operational configuration can be defined in a `.toml` file

```toml
[operation]
num_cores = 2     # No. of cores to use. Values <= 0 will use all available cores.
threshold = 1e-6  # Result values below this will be set to 0.0 (saves space for large number of runs)

[results]
output_dir = "./outputs"  # save to current working directory
```

# Example programmatic workflow


## Usage

```julia
using ADRIA

# Load and apply configuration options (the toml file)
ADRIA.setup()

@info "Load a domain"
RCP_scenario = "45"
path_to_input_set = "some location"
dom = ADRIA.load_domain(path_to_input_set, RCP_scenario)

@info "Load example scenarios to run"
p_df = ADRIA.load_scenarios(dom, "example_scenarios.csv")

# Batch run scenarios. Returns an updated domain object with the 
# run ID/result set location used to gather results later.
@info "Set up and run scenarios"
dom = ADRIA.run_scenarios(p_df, dom)

# Can also run a single scenario directly, but not shown in its entirety here.
# result = ADRIA.run_scenario(param_df::DataFrameRow, domain::Domain)

@info "Load ResultSet for analyses"
rs = ADRIA.load_results(dom)
```


Printing out `rs` displays an overview:

```
Domain: Example_domain
Run with ADRIA v0.4.1 on 2022-09-01_17_05_28_067
Results stored at: C:/ ... some output location... /Example_domain__RCPs45__2022-09-01_17_05_28_067

RCP(s) represented: 45
Intervention scenarios run: 5
Number of sites: 32
Timesteps: 74

Input layers
------------
site_data_fn : C:\ ... some location ... \Example_domain\site_data\Example_domain.gpkg
site_id_col : site_id
unique_site_id_col : reef_siteid
init_coral_cov_fn : C:\ ... some location ... \Example_domain\site_data\coral_cover.mat
connectivity_fn : C:\ ... some location ... \Example_domain\connectivity/
DHW_fn : C:\ ... some location ... \Example_domain\DHWs\dhwRCP45.mat
wave_fn : C:\ ... some location ... \Example_domain\waves/wave_RCP45.mat
timeframe : 2026 - 2099
```

... and results can be obtained for visualization/analysis

```julia
TAC = ADRIA.metrics.total_absolute_cover(rs)
RSV = ADRIA.metrics.relative_shelter_volume(rs)
# ... etc ...
```

## Model details

```julia
@info "Load domain"
RCP_scenario = "45"
path_to_input_set = "some location"
dom = ADRIA.load_domain(path_to_input_set, RCP_scenario)

# Get default parameter table (fieldnames and their values)
param_df = ADRIA.param_table(dom)

# Get model specification with lower/upper bounds separated
model_spec = ADRIA.model_spec(dom)

# Export model specification to CSV
ADRIA.model_spec(dom, "example_model_spec.csv")

# Update a domain with new values from row of DataFrame
update_params!(dom, param_df[1, :])

# Get parameter details

## Parameter names
p_names = dom.model[:fieldname]

## Current values
p_vals = dom.model[:val]

## ADRIA parameter types
p_types = dom.model[:ptype]

## Parameter bounds (for e.g., to pass into a sampler or optimizer)
## Note: ADRIA integer parameter bounds are set such that ℓ ≤ x ≤ u+1,
## where ℓ is the lower bound and u is the upper bound.
## This is because `floor(x)` is assigned with `update_params!()`.
## Instances where ℓ := x := u indicate uncertain parameters that 
## are nevertheless assumed to be constant.
p_bounds = dom.model[:bounds]

## Component groups
p_groups = dom.model[:component]

## All of above as a DataFrame
model_spec = DataFrame(dom.model)

# Get DataFrame of parameter information for a specific sub-component (Intervention, Criteria, Coral)
ADRIA.component_params(dom.model, Intervention)
```