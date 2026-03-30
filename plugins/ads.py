import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from database.database import db
from config import OWNER_ID
import pyromod.listen  # IMPORTANT

print("🔥 ADS LOADED 🔥")

# 🧠 Time parser
def parse_time(time_str):
    try:
        if time_str.endswith("m"):
            return timedelta(minutes=int(time_str[:-1]))
        elif time_str.endswith("h"):
            return timedelta(hours=int(time_str[:-1]))
        elif time_str.endswith("d"):
            return timedelta(days=int(time_str[:-1]))
    except:
        return None
    return None


# 🚀 SEND AD COMMAND
@Client.on_message(filters.command("adsend") & filters.user(OWNER_ID) & filters.private)
async def adsend(client, message: Message):
    try:
        args = message.text.split()

        if len(args) < 3:
            return await message.reply("❌ Usage: /adsend 10m all")

        time_arg = args[1]
        mode = args[2]

        duration = parse_time(time_arg)
        if not duration:
            return await message.reply("❌ Invalid time format (use 10m / 1h / 1d)")

        end_time = datetime.utcnow() + duration

        await message.reply("📢 Send your ad message now (text/photo/video)")

        ad_msg: Message = await client.listen(message.chat.id)

        # 📡 Get all channels
        channels = await db.get_channels()

        if not channels:
            return await message.reply("❌ No channels found in DB")

        # 🚫 Get disabled channels
        disabled = await db.get_disabled_channels()

        success = 0
        failed = 0

        for ch in channels:
            if ch in disabled:
                continue

            try:
                sent = await ad_msg.copy(ch)

                # 💾 Save ad
                await db.add_ad({
                    "chat_id": ch,
                    "message_id": sent.id,
                    "end_time": end_time,
                    "views": 0
                })

                success += 1

            except Exception as e:
                print(f"❌ Failed in {ch}: {e}")
                failed += 1

        await message.reply(
            f"✅ Ad sent successfully!\n\n"
            f"📡 Channels: {success}\n"
            f"❌ Failed: {failed}"
        )

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# 🚫 Disable Ads
@Client.on_message(filters.command("adsoff") & filters.user(OWNER_ID) & filters.private)
async def adsoff(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.disable_channel(chat_id)
        await message.reply("🚫 Ads disabled for this channel")
    except:
        await message.reply("❌ Usage: /adsoff -100xxxx")


# ✅ Enable Ads
@Client.on_message(filters.command("adson") & filters.user(OWNER_ID) & filters.private)
async def adson(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.enable_channel(chat_id)
        await message.reply("✅ Ads enabled for this channel")
    except:
        await message.reply("❌ Usage: /adson -100xxxx")


# 📊 Report
@Client.on_message(filters.command("adsreport") & filters.user(OWNER_ID) & filters.private)
async def ads_report(client, message: Message):
    try:
        ads = await db.get_all_ads()

        if not ads:
            return await message.reply("❌ No active ads found")

        total_views = 0
        text = "📊 <b>Ad Report:</b>\n\n"

        for ad in ads:
            try:
                msg = await client.get_messages(ad["chat_id"], ad["message_id"])
                views = msg.views or 0
                total_views += views

                text += f"<code>{ad['chat_id']}</code> → {views} views\n"
            except:
                continue

        text += f"\n👁 <b>Total Views:</b> {total_views}"
        await message.reply(text)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")
