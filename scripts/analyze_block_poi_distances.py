#!/usr/bin/env python3
"""Analyze block-POI distance distribution to determine optimal distance threshold."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from resalelens.database import SessionLocal

def analyze_distances():
    """Analyze distance distribution in block_pois table."""
    db = SessionLocal()
    
    # Get distance percentiles
    query = text("""
        SELECT 
            MIN(distance_m) as min_distance,
            percentile_cont(0.25) WITHIN GROUP (ORDER BY distance_m) as p25,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY distance_m) as median,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY distance_m) as p75,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY distance_m) as p90,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY distance_m) as p95,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY distance_m) as p99,
            MAX(distance_m) as max_distance,
            COUNT(*) as total_rows
        FROM block_pois;
    """)
    
    result = db.execute(query).fetchone()
    
    print("\n=== BLOCK-POI DISTANCE DISTRIBUTION ===\n")
    print(f"Total rows: {result[8]:,}")
    print(f"Min distance: {result[0]:.0f} m")
    print(f"25th percentile: {result[1]:.0f} m")
    print(f"Median: {result[2]:.0f} m")
    print(f"75th percentile: {result[3]:.0f} m")
    print(f"90th percentile: {result[4]:.0f} m")
    print(f"95th percentile: {result[5]:.0f} m")
    print(f"99th percentile: {result[6]:.0f} m")
    print(f"Max distance: {result[7]:.0f} m")
    
    # Check how many would be retained at different thresholds
    print("\n=== IMPACT OF DISTANCE THRESHOLDS ===\n")
    thresholds = [500, 1000, 2000, 3000, 5000, 10000]
    
    for threshold in thresholds:
        count_query = text(f"""
            SELECT COUNT(*) 
            FROM block_pois 
            WHERE distance_m <= {threshold}
        """)
        count = db.execute(count_query).scalar()
        percentage = (count / result[8]) * 100
        reduction = 100 - percentage
        
        print(f"Within {threshold:>5} m: {count:>10,} rows ({percentage:>5.1f}%) - {reduction:>5.1f}% reduction")
    
    # Size estimation
    print("\n=== ESTIMATED SIZE REDUCTION ===\n")
    print("Assuming proportional size reduction:")
    current_size_mb = 505
    
    for threshold in thresholds:
        count_query = text(f"""
            SELECT COUNT(*) 
            FROM block_pois 
            WHERE distance_m <= {threshold}
        """)
        count = db.execute(count_query).scalar()
        percentage = (count / result[8])
        estimated_size = current_size_mb * percentage
        saved_mb = current_size_mb - estimated_size
        
        print(f"{threshold:>5} m threshold: ~{estimated_size:>6.1f} MB (saves ~{saved_mb:>5.1f} MB)")
    
    db.close()

if __name__ == "__main__":
    analyze_distances()
