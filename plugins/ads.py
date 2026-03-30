import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from database.database import db  # tumhare db ka import adjust kar lena

ADS_CACHE = {}

# 🧠 Time parser
def parse_time(time_str):
    if time_str.endswith("m"):
        return timedelta(minutes=int(time_str[:-1]))
    elif time_str.endswith("h"):
        return timedelta(hours=int(time_str[:-1]))
    elif time_str.endswith("d"):
        return timedelta(days=int(time_str[:-1]))
    return None


# 🚀 SEND AD COMMAND
@Client.on_message(filters.command("adsend") & filters.user(ADMINS))
async def adsend(client, message: Message):
    try:
        args = message.text.split()

        if len(args) < 3:
            return await message.reply("Usage: /adsend 10m all")

        time_arg = args[1]
        mode = args[2]

        duration = parse_time(time_arg)
        if not duration:
            return await message.reply("Invalid time format")

        end_time = datetime.utcnow() + duration

        await message.reply("📢 Send your ad message now")

        ad_msg: Message = await client.listen(message.chat.id)

        # 📡 Get all channels
        channels = await db.get_channels()

        # 🚫 Get disabled channels
        disabled = await db.get_disabled_channels()

        success = 0
        total_views = 0

        for ch in channels:
            if ch in disabled:
                continue

            try:
                sent = await ad_msg.copy(ch)

                # save ad
                await db.add_ad({
                    "chat_id": ch,
                    "message_id": sent.id,
                    "end_time": end_time,
                    "views": 0
                })

                success += 1

            except Exception as e:
                print(f"Failed in {ch}: {e}")

        await message.reply(f"✅ Ad sent in {success} channels")

    except Exception as e:
        await message.reply(f"Error: {e}")


# 🚫 Disable Ads
@Client.on_message(filters.command("adsoff") & filters.user(ADMINS))
async def adsoff(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.disable_channel(chat_id)
        await message.reply("🚫 Ads disabled for this channel")
    except:
        await message.reply("Usage: /adsoff -100xxxx")


# ✅ Enable Ads
@Client.on_message(filters.command("adson") & filters.user(ADMINS))
async def adson(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.enable_channel(chat_id)
        await message.reply("✅ Ads enabled for this channel")
    except:
        await message.reply("Usage: /adson -100xxxx")


# 📊 Report
@Client.on_message(filters.command("adsreport") & filters.user(ADMINS))
async def ads_report(client, message: Message):
    ads = await db.get_all_ads()

    total_views = 0
    text = "📊 Ad Report:\n\n"

    for ad in ads:
        try:
            msg = await client.get_messages(ad["chat_id"], ad["message_id"])
            views = msg.views or 0
            total_views += views

            text += f"{ad['chat_id']} → {views} views\n"
        except:
            continue

    text += f"\n👁 Total Views: {total_views}"
    await message.reply(text)
