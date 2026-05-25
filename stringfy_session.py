import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")


async def main():
    # Leaving the first argument blank forces a new login
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start()

    print(
        "\n✅ SUCCESS! Copy the string below and add it to your Vercel Environment Variables as TELEGRAM_SESSION_STRING:\n"
    )
    print(client.session.save())

    await client.disconnect()


asyncio.run(main())
