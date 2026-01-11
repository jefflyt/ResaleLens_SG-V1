#!/usr/bin/env python3
"""Diagnose blocks table issues."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv('.env.local')

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

print("🔍 Diagnosing blocks table issues...\n")

with engine.connect() as conn:
    # 1. Check row count
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM blocks"))
        count = result.scalar()
        print(f"📊 Row count: {count:,}")

        if count > 100000:
            print("   ⚠️  VERY LARGE TABLE - This explains the timeout!")
        elif count > 50000:
            print("   ⚠️  Large table - May cause timeouts")
        else:
            print("   ✅ Manageable size")
    except Exception as e:
        print(f"   ❌ Error counting rows: {e}")

    print()

    # 2. Check table size
    try:
        result = conn.execute(text("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('blocks')) as total_size,
                pg_size_pretty(pg_relation_size('blocks')) as table_size,
                pg_size_pretty(pg_indexes_size('blocks')) as indexes_size
        """))
        row = result.fetchone()
        print("💾 Table size:")
        print(f"   Total: {row[0]}")
        print(f"   Table: {row[1]}")
        print(f"   Indexes: {row[2]}")
    except Exception as e:
        print(f"   ❌ Error checking size: {e}")

    print()

    # 3. Check active connections
    try:
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
              AND state = 'active'
        """))
        active = result.scalar()
        print(f"🔌 Active connections: {active}")
    except Exception as e:
        print(f"   ❌ Error checking connections: {e}")

    print()

    # 4. Check locks
    try:
        result = conn.execute(text("""
            SELECT 
                locktype,
                relation::regclass,
                mode,
                granted
            FROM pg_locks
            WHERE relation = 'blocks'::regclass
        """))
        locks = result.fetchall()
        if locks:
            print("🔒 Locks on blocks table:")
            for lock in locks:
                print(f"   {lock[0]} - {lock[2]} - Granted: {lock[3]}")
        else:
            print("🔒 No locks on blocks table")
    except Exception as e:
        print(f"   ❌ Error checking locks: {e}")

    print()

    # 5. Check foreign keys
    try:
        result = conn.execute(text("""
            SELECT
                conname AS constraint_name,
                conrelid::regclass AS table_name,
                confrelid::regclass AS referenced_table
            FROM pg_constraint
            WHERE confrelid = 'blocks'::regclass
              AND contype = 'f'
        """))
        fks = result.fetchall()
        if fks:
            print("🔗 Tables referencing blocks:")
            for fk in fks:
                print(f"   {fk[1]} -> blocks (constraint: {fk[0]})")
        else:
            print("🔗 No foreign keys referencing blocks")
    except Exception as e:
        print(f"   ❌ Error checking foreign keys: {e}")

print("\n" + "="*60)
print("💡 Recommendations:")
print("="*60)
