# +++ Fixed Version

import asyncio
from datetime import datetime

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
from aiohttp import web

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, PORT, OWNER_ID
from plugins import web_server
from database.database import db

import pyrogram.utils

# Fix for channel IDs
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

name = "Links Sharing Started"


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):
        await super().start()

        me = await self.get_me()
        self.username = me.username
        self.uptime = datetime.now()

        # Notify owner
        try:
            await self.send_message(
                chat_id=OWNER_ID,
                text="<b>🤖 Bot Restarted ♻️</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Owner notify error: {e}")

        self.set_parse_mode(ParseMode.HTML)

        print("✅ Bot Running...")
        print(name)

        # 🌐 Web server
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            print(f"🌐 Web server running on port {PORT}")
        except Exception as e:
            print(f"Web server error: {e}")

        # 🔥 Ad cleaner loop
        self.loop.create_task(self.ad_cleaner())

    async def ad_cleaner(self):
        while True:
            try:
                ads = await db.get_all_ads()
                now = datetime.utcnow()

                for ad in ads:
                    try:
                        if ad["end_time"] <= now:
                            await self.delete_messages(ad["chat_id"], ad["message_id"])
                            await db.ads.delete_one({"message_id": ad["message_id"]})
                        else:
                            msg = await self.get_messages(ad["chat_id"], ad["message_id"])
                            views = msg.views or 0
                            await db.ads.update_one(
                                {"message_id": ad["message_id"]},
                                {"$set": {"views": views}}
                            )
                    except Exception as e:
                        print(f"Cleaner error: {e}")

            except Exception as e:
                print(f"Main cleaner error: {e}")

            await asyncio.sleep(60)

    async def stop(self, *args):
        await super().stop()
        print("❌ Bot stopped")


if __name__ == "__main__":
    Bot().run()
