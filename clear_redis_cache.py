#!/usr/bin/env python3
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Find and delete all smart_ingestion keys
keys = r.keys("smart_ingestion_*")
print(f"Found {len(keys)} keys to delete")

for key in keys:
    r.delete(key)
    print(f"Deleted: {key.decode()}")

# Verify
remaining = r.keys("smart_ingestion_*")
print(f"\nRemaining keys: {len(remaining)}")
print(f"Total keys in DB: {r.dbsize()}")
