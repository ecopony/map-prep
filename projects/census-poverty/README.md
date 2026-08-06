# Census Poverty Data Automation

Automated fetching and processing of U.S. Census Bureau poverty data by county for any combination of states.

## Features

- **Automated API calls**: No more manual CSV downloads from Census Bureau website
- **Flexible state selection**: Compare any states by name or FIPS code
- **Multiple poverty thresholds**: Support for 100%, 150%, and 200% of federal poverty level
- **Intelligent caching**: Avoids repeated API calls for the same data
- **GIS-ready output**: Properly formatted for ArcGIS Pro joins with Natural Earth data
- **Summary statistics**: Automatic top counties analysis

## Quick Start

```python
from census_poverty import fetch_poverty_comparison

# Simple two-state comparison
data = fetch_poverty_comparison(['New Mexico', 'Oregon'])

# Single state analysis
ca_data = fetch_poverty_comparison('California')

# Multiple states with custom threshold
data = fetch_poverty_comparison(['Oregon', 'Washington', 'Idaho'], 
                               poverty_threshold=150)
```

## Installation Requirements

```bash
pip install pandas requests
```

## Data Output

The system generates CSV files with these columns:

- `Geography`: Formatted for GIS joins (USA-SSFFF format)
- `Name`: Clean county name (without "County, State" suffix)
- `State`: State FIPS code
- `TotalPopulation`: Total population for poverty determination
- `BelowXPercent`: Number of individuals below X% poverty threshold
- `PovertyRateX`: Calculated poverty rate as percentage

## Usage Examples

### Basic State Comparison
```python
# Recreate the New Mexico vs Oregon analysis from the blog post
df = fetch_poverty_comparison(['New Mexico', 'Oregon'], poverty_threshold=200)
```

### Single State Analysis
```python
# Analyze California poverty data
df = fetch_poverty_comparison('California')
```

### Custom Poverty Threshold
```python
# Use 150% poverty threshold instead of default 200%
df = fetch_poverty_comparison(['Arizona', 'Nevada'], poverty_threshold=150)
```

### Advanced Usage
```python
from census_poverty import CensusPovertyData

fetcher = CensusPovertyData(cache_dir="my_cache")
df = fetcher.fetch_poverty_data(['Texas', 'Florida'], year=2021, poverty_threshold=100)

# Get top 10 counties with highest poverty rates
top_counties = fetcher.get_top_counties(df, n=10, threshold=100)
print(top_counties)
```

## Data Sources

- **Census Bureau API**: American Community Survey 5-Year Estimates
- **Default dataset**: 2022 ACS 5-Year estimates
- **Variables used**: 
  - B06012_001E (Total population for poverty status determination)
  - B06012_002E (Below 100% poverty)
  - B06012_003E (Below 150% poverty) 
  - B06012_004E (Below 200% poverty)

## Caching

The system automatically caches API responses in JSON format to avoid repeated calls:
- Cache location: `cache/` directory
- Cache key format: `poverty_{year}_{state_fips}_{threshold}.json`
- No automatic expiration - delete cache files to refresh data

## GIS Integration

Output CSV files are formatted for direct joining with Natural Earth county data:
- `Geography` field matches Natural Earth `ADM2_CODE` 
- Use "USA-" prefix format for proper joins
- Counties are pre-sorted by poverty rate (highest first)

## Error Handling

- Invalid state names raise `ValueError`
- API failures raise `requests.HTTPError`
- Missing data fields default to 0
- Unsupported poverty thresholds raise `ValueError`

## Supported States

All 50 U.S. states are supported. Use either:
- Full state names: "New Mexico", "North Carolina"
- FIPS codes: "35", "37"