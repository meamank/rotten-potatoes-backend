import os
import json
from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

redis = Redis(
    url=os.getenv("CACHE_KV_REST_API_URL"), 
    token=os.getenv("CACHE_KV_REST_API_TOKEN")
)

# Instead of a filename, we use a Redis key
CACHE_KEY = "rotten-potatoes-cache"

def load_rp_rec_cache() -> dict:
    """Reads the vault data from Vercel KV Redis."""
    default_schema = {"last_synced": 0.0, "data": {}}
    
    try:
        # Fetch the data from Redis
        data = redis.get(CACHE_KEY)
        
        # If the key exists, return it. Otherwise, return our default schema.
        if data:
            if isinstance(data, str):
                return json.loads(data)
            
            return data
        return default_schema
        
    except Exception as e:
        print(f"🚨 Redis Read Error: {e}")
        return default_schema

def save_rp_rec_cache(data: dict):
    """Writes the dictionary directly to Vercel KV Redis."""
    try:
        # Save the dictionary. Upstash handles the JSON conversion automatically!
        redis.set(CACHE_KEY, json.dumps(data))
        print("✅ Cache successfully saved to Vercel KV.")
    except Exception as e:
        print(f"🚨 Redis Write Error: {e}")