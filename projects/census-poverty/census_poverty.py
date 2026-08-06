"""
Automated Census Bureau poverty data fetching and processing.

This module provides an easy-to-use interface for downloading and processing
U.S. Census Bureau poverty data by county for any combination of states.
"""

import pandas as pd
import requests
import json
from typing import List, Dict, Optional, Union
from pathlib import Path


class CensusPovertyData:
    """
    Fetches and processes Census Bureau poverty data for states and counties.
    
    Uses the Census Bureau's API to automatically download American Community Survey
    5-Year estimates for poverty status data, eliminating manual CSV downloads.
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the Census poverty data fetcher.
        
        Args:
            cache_dir: Directory to store cached API responses
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.base_url = "https://api.census.gov/data"
        
        # State FIPS codes mapping
        self.state_fips = {
            'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05',
            'California': '06', 'Colorado': '08', 'Connecticut': '09', 'Delaware': '10',
            'Florida': '12', 'Georgia': '13', 'Hawaii': '15', 'Idaho': '16',
            'Illinois': '17', 'Indiana': '18', 'Iowa': '19', 'Kansas': '20',
            'Kentucky': '21', 'Louisiana': '22', 'Maine': '23', 'Maryland': '24',
            'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27', 'Mississippi': '28',
            'Missouri': '29', 'Montana': '30', 'Nebraska': '31', 'Nevada': '32',
            'New Hampshire': '33', 'New Jersey': '34', 'New Mexico': '35', 'New York': '36',
            'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39', 'Oklahoma': '40',
            'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45',
            'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49',
            'Vermont': '50', 'Virginia': '51', 'Washington': '53', 'West Virginia': '54',
            'Wisconsin': '55', 'Wyoming': '56'
        }
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve data from cache if it exists."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(cache_key)
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _resolve_state_fips(self, state: str) -> str:
        """Convert state name to FIPS code."""
        if state in self.state_fips:
            return self.state_fips[state]
        # Check if it's already a FIPS code
        if state.isdigit() and len(state) == 2:
            return state
        raise ValueError(f"Unknown state: {state}")
    
    def fetch_poverty_data(self, 
                          states: Union[str, List[str]], 
                          year: int = 2023,
                          poverty_threshold: int = 200) -> pd.DataFrame:
        """
        Fetch poverty data for specified states.
        
        Args:
            states: State name(s) or FIPS code(s)
            year: ACS data year (default 2022)
            poverty_threshold: Poverty threshold percentage (100, 150, 200, etc.)
        
        Returns:
            DataFrame with columns: Geography, Name, State, TotalPopulation, 
                                   BelowXPercent, PovertyRateX
        """
        if isinstance(states, str):
            states = [states]
        
        all_data = []
        
        for state in states:
            state_fips = self._resolve_state_fips(state)
            cache_key = f"poverty_{year}_{state_fips}_{poverty_threshold}"
            
            # Check cache first
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"Using cached data for {state}")
                all_data.extend(cached_data)
                continue
            
            # Fetch from API
            print(f"Fetching poverty data for {state}...")
            data = self._fetch_state_poverty_data(state_fips, year, poverty_threshold)
            
            # Cache the results
            self._save_to_cache(cache_key, data)
            all_data.extend(data)
        
        # Convert to DataFrame and process
        df = pd.DataFrame(all_data)
        return self._process_poverty_data(df, poverty_threshold)
    
    def _fetch_state_poverty_data(self, state_fips: str, year: int, threshold: int) -> List[Dict]:
        """Fetch poverty data for a single state from Census API."""
        
        # Census variable codes using C17002 (Ratio of Income to Poverty Level)
        # Variables for the requested poverty threshold
        if threshold == 100:
            # Below 100% poverty: C17002_002E + C17002_003E
            poverty_vars = ["C17002_002E", "C17002_003E"]
        elif threshold == 150:
            # Below 150% poverty: C17002_002E through C17002_005E
            poverty_vars = ["C17002_002E", "C17002_003E", "C17002_004E", "C17002_005E"]
        elif threshold == 200:
            # Below 200% poverty: C17002_002E through C17002_007E
            poverty_vars = ["C17002_002E", "C17002_003E", "C17002_004E", "C17002_005E", "C17002_006E", "C17002_007E"]
        else:
            raise ValueError(f"Unsupported poverty threshold: {threshold}%. Supported: 100, 150, 200")
        
        total_var = "C17002_001E"  # Total population for whom poverty status is determined
        
        url = f"{self.base_url}/{year}/acs/acs5"
        
        # Build the get parameter with all needed variables
        get_vars = ['NAME'] + poverty_vars + [total_var]
        params = {
            'get': ','.join(get_vars),
            'for': 'county:*',
            'in': f'state:{state_fips}'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        headers = data[0]
        rows = data[1:]
        
        results = []
        for row in rows:
            county_data = dict(zip(headers, row))
            
            # Sum up all the poverty variables for this threshold
            below_poverty = 0
            for var in poverty_vars:
                value = county_data.get(var, '0')
                if value and value != '-':
                    below_poverty += int(value)
            
            total_pop = county_data.get(total_var, '0')
            total_pop = int(total_pop) if total_pop and total_pop != '-' else 0
            
            results.append({
                'Geography': f"0500000US{county_data['state']}{county_data['county']}",
                'Name': county_data['NAME'],
                'State': county_data['state'],
                'County': county_data['county'],
                'TotalPopulation': total_pop,
                f'Below{threshold}Percent': below_poverty
            })
        
        return results
    
    def _process_poverty_data(self, df: pd.DataFrame, threshold: int) -> pd.DataFrame:
        """Process and clean the poverty data."""
        # Clean county names
        df['Name'] = df['Name'].str.replace(r' County, .*', '', regex=True)
        
        # Calculate poverty rate
        below_col = f'Below{threshold}Percent'
        rate_col = f'PovertyRate{threshold}'
        
        df[rate_col] = ((df[below_col] / df['TotalPopulation']) * 100).round(2)
        
        # Format Geography for GIS joins
        df['Geography'] = df['Geography'].str.replace('0500000US', 'USA-')
        
        # Sort by poverty rate descending
        df = df.sort_values(rate_col, ascending=False)
        
        return df
    
    def get_top_counties(self, df: pd.DataFrame, n: int = 5, threshold: int = 200) -> pd.DataFrame:
        """Get the top N counties with highest poverty rates."""
        rate_col = f'PovertyRate{threshold}'
        return df.nlargest(n, rate_col)[['Name', rate_col, 'TotalPopulation']]
    
    def export_for_gis(self, df: pd.DataFrame, output_path: str) -> None:
        """Export data in format ready for GIS joins."""
        df.to_csv(output_path, index=False)
        print(f"Data exported to {output_path}")


def fetch_poverty_comparison(states: Union[str, List[str]], 
                           year: int = 2023,
                           poverty_threshold: int = 200,
                           output_dir: str = "output") -> pd.DataFrame:
    """
    Convenience function to fetch and compare poverty data between states.
    
    Args:
        states: State name(s) to compare
        year: ACS data year
        poverty_threshold: Poverty threshold percentage (100, 150, 200)
        output_dir: Directory to save output files
    
    Returns:
        DataFrame with processed poverty data
    """
    fetcher = CensusPovertyData()
    df = fetcher.fetch_poverty_data(states, year, poverty_threshold)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate filename
    if isinstance(states, str):
        states_str = states.lower().replace(' ', '-')
    else:
        states_str = '-'.join([s.lower().replace(' ', '-') for s in states])
    
    filename = f"{poverty_threshold}-percent-poverty-{states_str}-{year}.csv"
    output_file = output_path / filename
    
    # Export data
    fetcher.export_for_gis(df, str(output_file))
    
    # Print summary
    print(f"\nPoverty Data Summary ({poverty_threshold}% threshold):")
    print(f"Total counties: {len(df)}")
    print(f"States: {', '.join(states) if isinstance(states, list) else states}")
    
    top_counties = fetcher.get_top_counties(df, 5, poverty_threshold)
    print(f"\nTop 5 Counties with Highest Poverty Rates:")
    print(top_counties.to_string(index=False))
    
    return df