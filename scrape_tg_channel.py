import re
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

session_name = os.getenv("TG_SESSION")
channel_username = os.getenv("TG_CHANNEL_USERNAME")
api_id = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")


async def scrape_imdb_ids() -> list[str]:
    """
    Connects to Telegram via MTProto, scans a channel, and extracts unique IMDb IDs.
    """
    # Regex pattern: "tt" followed by exactly 7 or 8 digits
    imdb_pattern = re.compile(r"tt\d{7,8}")
    unique_ids = set()

    client = TelegramClient(StringSession(session_name), api_id, api_hash)

    async with client:
        # iter_messages pages through the history efficiently
        async for message in client.iter_messages(channel_username):
            if message.text:
                # Find all matches in this specific message
                matches = imdb_pattern.findall(message.text)

                # update() adds multiple items to a set at once
                unique_ids.update(matches)

    return list(unique_ids)
