import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from database.database import db
from config import OWNER_ID

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_selection = {}

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
        return await message.reply(
            "⚠️ <b>Invalid Usage</b>\n\n"
            "📌 <b>Format:</b> <code>/adsend 10m</code>\n"
            "⏳ Example: 10m / 2h / 1d"
        )

    duration = parse_time(args[1])
    if not duration:
        return await message.reply(
            "❌ <b>Invalid Time Format</b>\n\n"
            "Use: <code>10m</code>, <code>2h</code>, <code>1d</code>"
        )

    end_time = datetime.utcnow() + duration

    await message.reply(
        "📢 <b>Send Your Advertisement Message</b>\n\n"
        "⏳ Waiting for your content..."
    )

    ad_msg: Message = await client.listen(message.chat.id)

    channels = await db.channels.find().to_list(None)
    disabled = await db.disabled.find().to_list(None)
    disabled_ids = [x["chat_id"] for x in disabled]

    success = 0
    failed = 0

    status_msg = await message.reply("🚀 <b>Sending Ads...</b>")

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
            failed += 1

    await status_msg.edit(
        "✅ <b>Advertisement Broadcast Completed</b>\n\n"
        f"📡 <b>Total Channels:</b> {len(channels)}\n"
        f"✔️ <b>Success:</b> {success}\n"
        f"❌ <b>Failed:</b> {failed}\n"
        f"⏳ <b>Duration:</b> {args[1]}"
    )


# 🚫 OFF
@Client.on_message(filters.command("adsoff") & filters.user(OWNER_ID))
async def adsoff(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])

        await db.disabled.insert_one({"chat_id": chat_id})

        await message.reply(
            "🚫 <b>Ads Disabled</b>\n\n"
            f"📍 Channel: <code>{chat_id}</code>"
        )
    except:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/adsoff -100xxxx</code>"
        )


# ✅ ON
@Client.on_message(filters.command("adson") & filters.user(OWNER_ID))
async def adson(client, message: Message):
    try:
        chat_id = int(message.text.split()[1])

        await db.disabled.delete_one({"chat_id": chat_id})

        await message.reply(
            "✅ <b>Ads Enabled</b>\n\n"
            f"📍 Channel: <code>{chat_id}</code>"
        )
    except:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/adson -100xxxx</code>"
        )


# 📊 REPORT
@Client.on_message(filters.command("adsreport") & filters.user(OWNER_ID))
async def report(client, message: Message):
    ads = await db.ads.find().to_list(None)

    total = 0

    text = "📊 <b>Advertisement Analytics Report</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"

    for ad in ads:
        try:
            msg = await client.get_messages(ad["chat_id"], ad["message_id"])
            views = msg.views or 0
            total += views

            text += (
                f"📍 <code>{ad['chat_id']}</code>\n"
                f"👁 Views: <b>{views}</b>\n\n"
            )
        except:
            pass

    text += "━━━━━━━━━━━━━━━━━━━\n"
    text += f"🔥 <b>Total Views:</b> {total}"

    await message.reply(text)


# TEST
@Client.on_message(filters.command("test"))
async def test(client, message):
    await message.reply(
        "✅ <b>Ads System Working Perfectly</b>\n\n"
        "🚀 Ready for broadcasting!"
    )


# 🗑 DELETE ALL ADS
@Client.on_message(filters.command("adsdelete") & filters.user(OWNER_ID))
async def adsdelete(client, message: Message):
    ads = await db.ads.find().to_list(None)

    deleted = 0
    failed = 0

    status = await message.reply("🗑 <b>Deleting Ads...</b>")

    for ad in ads:
        try:
            await client.delete_messages(
                ad["chat_id"],
                ad["message_id"]
            )
            deleted += 1
        except Exception as e:
            print(f"Delete error {ad['chat_id']}: {e}")
            failed += 1

    # optional: clear DB
    await db.ads.delete_many({})

    await status.edit(
        "✅ <b>Ads Deleted</b>\n\n"
        f"🗑 Deleted: {deleted}\n"
        f"❌ Failed: {failed}"
    )



# 🎯 START SELECT
@Client.on_message(filters.command("adsend_select") & filters.user(OWNER_ID))
async def adsend_select(client, message: Message):
    args = message.text.split()

    if len(args) < 2:
        return await message.reply("Usage: /adsend_select 10m")

    duration = parse_time(args[1])
    if not duration:
        return await message.reply("Invalid time format!")

    channels = await db.channels.find().to_list(None)

    buttons = []
    for ch in channels:
        chat_id = ch["channel_id"]
        buttons.append(
            [InlineKeyboardButton(f"❌ {chat_id}", callback_data=f"select_{chat_id}")]
        )

    buttons.append([InlineKeyboardButton("✅ DONE", callback_data="done_select")])

    user_selection[message.from_user.id] = {
        "channels": [],
        "duration": duration
    }

    await message.reply(
        "🎯 <b>Select Channels:</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# 🔘 BUTTON HANDLER
@Client.on_callback_query(filters.regex("^select_"))
async def select_channel(client, query):
    user_id = query.from_user.id
    chat_id = int(query.data.split("_")[1])

    data = user_selection.get(user_id)

    if not data:
        return await query.answer("Session expired!", show_alert=True)

    if chat_id in data["channels"]:
        data["channels"].remove(chat_id)
        text = f"❌ {chat_id}"
    else:
        data["channels"].append(chat_id)
        text = f"✅ {chat_id}"

    await query.answer("Toggled")
    await query.message.edit_reply_markup(
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅' if int(btn.callback_data.split('_')[1]) in data['channels'] else '❌'} {btn.callback_data.split('_')[1]}",
                    callback_data=btn.callback_data
                )
            ]
            for row in query.message.reply_markup.inline_keyboard[:-1]
            for btn in row
        ] + [[InlineKeyboardButton("✅ DONE", callback_data="done_select")]])
    )


# ✅ DONE
@Client.on_callback_query(filters.regex("done_select"))
async def done_select(client, query):
    user_id = query.from_user.id
    data = user_selection.get(user_id)

    if not data or not data["channels"]:
        return await query.answer("No channels selected!", show_alert=True)

    await query.message.reply("📢 Send your ad message now...")

    ad_msg: Message = await client.listen(query.message.chat.id)

    success = 0
    failed = 0

    for chat_id in data["channels"]:
        try:
            sent = await ad_msg.copy(chat_id)

            await db.ads.insert_one({
                "chat_id": chat_id,
                "message_id": sent.id,
                "end_time": datetime.utcnow() + data["duration"],
                "views": 0
            })

            success += 1
        except Exception as e:
            print(e)
            failed += 1

    await query.message.reply(
        "✅ <b>Ads Sent</b>\n\n"
        f"✔️ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

    user_selection.pop(user_id, None)
