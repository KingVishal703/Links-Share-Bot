# +++ Modified By [telegram username: @Codeflix_Bots

import asyncio
from datetime import datetime

from pyrogram import Client
from pyrogram.enums import ParseMode

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, MEMBERSHIP_CHANNEL, PORT, OWNER_ID
from plugins import web_server
import pyrogram.utils
from aiohttp import web

from database.database import (
    get_expired_memberships,
    delete_membership
)

from database.database import db

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

name = """
Links Sharing Started
"""

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
        usr_bot_me = await self.get_me()
        self.uptime = datetime.utcnow()

        try:
            await self.send_message(
                chat_id=OWNER_ID,
                text="<b><blockquote>🤖 Bot Restarted ♻️</blockquote></b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            self.LOGGER(__name__).warning(f"Owner notify failed: {e}")

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running..!\n\nCreated by \nhttps://t.me/ProObito")
        self.LOGGER(__name__).info(f"{name}")
        self.username = usr_bot_me.username

        # 🌐 Web Server
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            self.LOGGER(__name__).info(f"Web server started on 0.0.0.0:{PORT}")
        except Exception as e:
            self.LOGGER(__name__).error(f"Web server error: {e}")

        # 🔥 AUTO DELETE START
        self.loop.create_task(self.ad_cleaner())
        self.loop.create_task(
            self.membership_cleaner()
        )

    async def membership_cleaner(self):

        await asyncio.sleep(10)

        while True:

            try:

                expired = await get_expired_memberships()

                for member in expired:

                    user_id = member["user_id"]

                    try:

                        await self.ban_chat_member(
                            MEMBERSHIP_CHANNEL,
                            user_id
                        )

                        await self.unban_chat_member(
                            MEMBERSHIP_CHANNEL,
                            user_id
                        )

                        await delete_membership(user_id)

                        print(
                            f"Removed {user_id}"
                        )

                    except Exception as e:
                        print(e)

            except Exception as e:
                print(e)

            await asyncio.sleep(300)

    # 🔥 AUTO DELETE + VIEW TRACKER
    async def ad_cleaner(self):
        await asyncio.sleep(10)  # startup delay

        while True:
            try:
                ads = await db.ads.find().to_list(None)
                now = datetime.utcnow()

                for ad in ads:
                    try:
                        end_time = ad.get("end_time")

                        # 🛠️ FIX: ensure datetime
                        if isinstance(end_time, str):
                            end_time = datetime.fromisoformat(end_time)

                        if not isinstance(end_time, datetime):
                            continue

                        # ⛔ DELETE
                        if end_time <= now:
                            try:
                                await self.delete_messages(
                                    chat_id=ad["chat_id"],
                                    message_ids=ad["message_id"]
                                )
                            except Exception as e:
                                print(f"Delete failed: {e}")

                            await db.ads.delete_one({
                                "_id": ad["_id"]
                            })

                            print(f"✅ Deleted Ad: {ad['message_id']}")

                        # 👁 UPDATE VIEWS
                        else:
                            try:
                                msg = await self.get_messages(
                                    ad["chat_id"],
                                    ad["message_id"]
                                )

                                views = msg.views or 0

                                await db.ads.update_one(
                                    {"_id": ad["_id"]},
                                    {"$set": {"views": views}}
                                )
                            except:
                                pass

                    except Exception as e:
                        print(f"Ad error: {e}")

            except Exception as e:
                print(f"Cleaner main error: {e}")

            await asyncio.sleep(30)  # 🔥 faster check (30 sec)

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")


# Global cancel flag
is_canceled = False
cancel_lock = asyncio.Lock()

if __name__ == "__main__":
    Bot().run()
