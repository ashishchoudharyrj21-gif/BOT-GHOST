from telethon import TelegramClient

api_id = 31376570
api_hash = "6b869ab57239d9b73a0ac1964f03e9b7"

print("📱 Creating session for user bot...")
client = TelegramClient("telebot", api_id, api_hash)

async def main():
    await client.start()
    print("✅ Session created successfully!")
    print("📁 File saved: telebot.session")
    await client.disconnect()

with client:
    client.loop.run_until_complete(main())