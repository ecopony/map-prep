"""
Example usage of the Census poverty data fetcher.

This script demonstrates how to use the automated Census data fetching
to recreate and extend the analysis from the original blog post.
"""

from census_poverty import fetch_poverty_comparison

if __name__ == "__main__":
    # Recreate the original New Mexico vs Oregon comparison
    print("=== New Mexico vs Oregon Poverty Comparison ===")
    df_original = fetch_poverty_comparison(['New Mexico', 'Oregon'], 
                                         poverty_threshold=200)
    
    print("\n" + "="*60 + "\n")
    
    # Example: Single state analysis
    print("=== California Poverty Analysis ===")
    df_ca = fetch_poverty_comparison('California', 
                                   poverty_threshold=200)
    
    print("\n" + "="*60 + "\n")
    
    # Example: Multi-state comparison with different threshold
    print("=== Western States at 150% Poverty Level ===")
    df_west = fetch_poverty_comparison(['Oregon', 'Washington', 'Idaho'], 
                                     poverty_threshold=150)
    
    print("\n" + "="*60 + "\n")
    
    # Example: Compare different poverty thresholds for same state
    print("=== New Mexico: 100% vs 200% Poverty Comparison ===")
    df_nm_100 = fetch_poverty_comparison('New Mexico', poverty_threshold=100)
    df_nm_200 = fetch_poverty_comparison('New Mexico', poverty_threshold=200)
    
    print(f"\nAverage poverty rate at 100% threshold: {df_nm_100['PovertyRate100'].mean():.1f}%")
    print(f"Average poverty rate at 200% threshold: {df_nm_200['PovertyRate200'].mean():.1f}%")