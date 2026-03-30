import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from database.database import db
from config import OWNER_ID

# 🧠 Time parser
def parse_time(time_str):
    if time_str.endswith("m"):
        return timedelta(minutes=int(time_str[:-1]))
    elif time_str.endswith("h"):
        return timedelta(hours=int(time_str[:-1]))
    elif time_str.endswith("d"):
        return timedelta(days=int(time_str[:-1]))
    return None


# 🚀 SEND AD
@Client.on_message(filters.command("adsend") & filters.user(OWNER_ID))
async def adsend(client, message: Message):
    args = message.text.split()

    if len(args) < 2:
        return await message.reply("Usage: /adsend 10m")

    duration = parse_time(args[1])
    if not duration:
        return await message.reply("Invalid time format")

    end_time = datetime.utcnow() + duration

    await message.reply("📢 Send your ad message")

    ad_msg: Message = await client.listen(message.chat.id)

    channels = await db.channels.find().to_list(None)
    disabled = await db.disabled.find().to_list(None)
    disabled_ids = [x["chat_id"] for x in disabled]

    success = 0

    for ch in channels:
        chat_id = ch.get("channel_id")

        if chat_id in disabled_ids:
            continue

        try:
            sent = await ad_msg.copy(chat_id)

            await db.ads.insert_one({
                "chat_id": chat_id,
                "message_id": sent.id,
                "end_time": end_time,
                "views": 0
            })

            success += 1
        except Exception as e:
            print(f"Error in {chat_id}: {e}")

    await message.reply(f"✅ Ad sent in {success} channels")


# 🚫 OFF
@Client.on_message(filters.command("adsoff") & filters.user(OWNER_ID))
async def adsoff(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.disabled.insert_one({"chat_id": chat_id})
        await message.reply("🚫 Ads OFF")
    except:
        await message.reply("Usage: /adsoff -100xxx")


# ✅ ON
@Client.on_message(filters.command("adson") & filters.user(OWNER_ID))
async def adson(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])
        await db.disabled.delete_one({"chat_id": chat_id})
        await message.reply("✅ Ads ON")
    except:
        await message.reply("Usage: /adson -100xxx")


# 📊 REPORT
@Client.on_message(filters.command("adsreport") & filters.user(OWNER_ID))
async def report(client, message: Message):
    ads = await db.ads.find().to_list(None)

    total = 0
    text = "📊 Report:\n\n"

    for ad in ads:
        try:
            msg = await client.get_messages(ad["chat_id"], ad["message_id"])
            views = msg.views or 0
            total += views

            text += f"{ad['chat_id']} → {views}\n"
        except:
            pass

    text += f"\n👁 Total: {total}"
    await message.reply(text)


# TEST
@Client.on_message(filters.command("test"))
async def test(client, message):
    await message.reply("Ads working ✅")
