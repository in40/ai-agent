#!/usr/bin/env python3
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Find all job keys
job_keys = redis_client.keys("smart_ingestion*")
print(f"Found {len(job_keys)} keys matching 'smart_ingestion*':")

for key in job_keys[:10]:
    key_type = redis_client.type(key)
    print(f"\n{key} (type: {key_type}):")
    
    if key_type == b'string' or key_type == 'string':
        value = redis_client.get(key)
        print(f"  Value: {value[:200] if value else 'None'}...")
    elif key_type == b'hash' or key_type == 'hash':
        job_data = redis_client.hgetall(key)
        for k, v in job_data.items():
            print(f"  {k}: {v}")
    elif key_type == b'list' or key_type == 'list':
        items = redis_client.lrange(key, 0, 5)
        print(f"  List items: {items}")
    elif key_type == b'set' or key_type == 'set':
        items = redis_client.smembers(key)
        print(f"  Set items: {items}")
    elif key_type == b'zset' or key_type == 'zset':
        items = redis_client.zrange(key, 0, 5)
        print(f"  ZSet items: {items}")
