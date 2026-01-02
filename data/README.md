# Data Directory

## Required Files

Place the following files in this directory:

1. **Parquet Files** (not committed to git):
   - `fhvhv_tripdata_2023-01.parquet`
   - `fhvhv_tripdata_2023-02.parquet`
   - `fhvhv_tripdata_2023-03.parquet`

2. **Lookup Files** (committed):
   - `taxi_zone_lookup.csv` - Taxi zone information
   - `fhv_base_lookup.csv` - Base number to company mapping

## Downloading Data

NYC TLC FHVHV data can be downloaded from:
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

## Base Lookup File Format

The `fhv_base_lookup.csv` file should have columns:
- `base_number`: Base number identifier (e.g., "B03406")
- `base_name`: Human-readable base name
- `company`: Company name (Uber, Lyft, Via, Other)

You can maintain this file manually or generate it from the data by extracting unique base numbers.

