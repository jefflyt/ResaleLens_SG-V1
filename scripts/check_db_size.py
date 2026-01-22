#!/usr/bin/env python3
"""Script to check database table sizes and row counts."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from resalelens.database import SessionLocal

def check_database_size():
    """Check the size of each table and total database size."""
    db = SessionLocal()
    
    # Get table sizes
    query = text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_total_relation_size(schemaname||'.'||tablename) as bytes
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    print("\n=== DATABASE TABLE SIZES ===\n")
    print(f"{'Table':<30} {'Size':<15} {'Bytes':<15}")
    print("-" * 60)
    
    total_bytes = 0
    for row in rows:
        print(f"{row[1]:<30} {row[2]:<15} {row[3]:<15,}")
        total_bytes += row[3]
    
    print("-" * 60)
    print(f"{'TOTAL':<30} {format_bytes(total_bytes):<15} {total_bytes:<15,}")
    
    # Get row counts for each table
    print("\n\n=== TABLE ROW COUNTS ===\n")
    print(f"{'Table':<30} {'Row Count':<15}")
    print("-" * 45)
    
    tables = ['transactions', 'blocks', 'pois', 'block_pois', 'ingestion_runs', 'leads', 'users']
    for table in tables:
        count_query = text(f"SELECT COUNT(*) FROM {table}")
        count = db.execute(count_query).scalar()
        print(f"{table:<30} {count:<15,}")
    
    # Get index sizes
    print("\n\n=== INDEX SIZES ===\n")
    index_query = text("""
        SELECT 
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS size,
            pg_relation_size(schemaname||'.'||indexname) as bytes
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
        LIMIT 20;
    """)
    
    result = db.execute(index_query)
    rows = result.fetchall()
    
    print(f"{'Table':<25} {'Index':<40} {'Size':<15}")
    print("-" * 80)
    
    for row in rows:
        print(f"{row[0]:<25} {row[1]:<40} {row[2]:<15}")

def format_bytes(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

if __name__ == "__main__":
    check_database_size()
