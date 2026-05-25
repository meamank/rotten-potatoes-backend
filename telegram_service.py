import time
import asyncio
from rp_recommended_cache import load_rp_rec_cache, save_rp_rec_cache
from scrape_tg_channel import scrape_imdb_ids
from tmdb_service import fetch_tmdb_from_imdb

CACHE_SYNC_INTERVAL_SECONDS = 86400  # 24 hours


async def sync_tg_fetch_tmdb(client):
    # load existing json data
    cache_db = load_rp_rec_cache()
    current_time = time.time()

    # check if interval time has passed or not
    # if passed get new data
    try:
        if current_time - cache_db["last_synced"] < CACHE_SYNC_INTERVAL_SECONDS:
            print("⏳ 24 hours haven't passed. Returning Vault from cache!")
            return list(cache_db["data"].values())[:10]

        print("🔄 24 hours have passed! Initiating Telegram sync...")

    

        print("🔄 24 hours have passed! Initiating Telegram sync...")

        imdb_ids = await scrape_imdb_ids()

        existing_imdb_ids = set(cache_db.get("data", {}).keys())
        new_imdb_ids = set(imdb_ids) - existing_imdb_ids

        if not new_imdb_ids:
            print("⚡ No new movies found. Updating timestamp only.")
            cache_db["last_synced"] = current_time
            save_rp_rec_cache(cache_db)
            return list(cache_db["data"].values())

        tasks = []

        for imdb_id in new_imdb_ids:
            tasks.append(fetch_tmdb_from_imdb(client, imdb_id))

        results = await asyncio.gather(*tasks)

        for imdb_id, parsed_media in zip(new_imdb_ids, results):
            if parsed_media:
                cache_db["data"][imdb_id] = parsed_media.model_dump()

        cache_db["last_synced"] = current_time
        save_rp_rec_cache(cache_db)
        return list(cache_db["data"].values())[:10] 

    except Exception as e:
        print(f"🚨 Critical Sync Error: {e}")
        # 🔧 THE SAFETY NET: If Telegram or TMDB crashes, return whatever we had in Redis.
        return list(cache_db.get("data", {}).values())[:10]
