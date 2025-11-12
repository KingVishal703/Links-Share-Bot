from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from database.database import database
from config import OWNER_ID
from datetime import datetime

@Client.on_chat_join_request(filters.chat)
async def handle_join_request(client: Client, join_request: ChatJoinRequest):
    chat = join_request.chat
    user = join_request.from_user

    # Save to MongoDB collection "join_requests"
    try:
        await database["join_requests"].insert_one({
            "chat_id": chat.id,
            "chat_title": getattr(chat, "title", ""),
            "user_id": user.id,
            "user_name": getattr(user, "username", None),
            "first_name": getattr(user, "first_name", None),
            "date": datetime.utcnow()
        })
    except Exception as e:
        print("Failed to save join request:", e)

    # Notify owner
    try:
        text = (
            f"📨 <b>New Join Request</b>\n"
            f"Channel: {chat.title}\n"
            f"User: {user.first_name} (ID: <code>{user.id}</code>)\n"
            f"Approve manually in the channel settings."
        )
        await client.send_message(OWNER_ID, text, parse_mode="html")
    except Exception as e:
        print("Failed to notify owner:", e)




from pyrogram.types import Message
from config import ADMINS
from database.database import database

# ------------------ JOIN REQUEST FORCE SUB ADMIN COMMANDS ------------------ #

@Client.on_message(filters.command("addjrfsub") & filters.user(ADMINS))
async def add_jrfsub_channel(client, message: Message):
    """
    Add a channel to join-request force-subscribe list.
    """
    if len(message.command) != 2:
        return await message.reply_text("Usage:\n<code>/addjrfsub -1001234567890</code>")
    try:
        channel_id = int(message.command[1])
        existing = await database["jrfsub_channels"].find_one({"channel_id": channel_id})
        if existing:
            return await message.reply_text("⚠️ Channel already exists in Join Request FSUB list.")
        await database["jrfsub_channels"].insert_one({
            "channel_id": channel_id,
            "status": "active"
        })
        await message.reply_text(f"✅ Channel <code>{channel_id}</code> added to Join Request Force-Subscribe list.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@Client.on_message(filters.command("deljrfsub") & filters.user(ADMINS))
async def del_jrfsub_channel(client, message: Message):
    """
    Remove a channel from join-request force-subscribe list.
    """
    if len(message.command) != 2:
        return await message.reply_text("Usage:\n<code>/deljrfsub -1001234567890</code>")
    try:
        channel_id = int(message.command[1])
        result = await database["jrfsub_channels"].delete_one({"channel_id": channel_id})
        if result.deleted_count > 0:
            await message.reply_text(f"🗑️ Channel <code>{channel_id}</code> removed from Join Request Force-Subscribe list.")
        else:
            await message.reply_text("⚠️ Channel not found in list.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@Client.on_message(filters.command("listjrfsub") & filters.user(ADMINS))
async def list_jrfsub_channels(client, message: Message):
    """
    List all active join-request force-subscribe channels.
    """
    try:
        channels = await database["jrfsub_channels"].find({"status": "active"}).to_list(None)
        if not channels:
            return await message.reply_text("📭 No Join Request Force-Subscribe channels found.")
        msg = "<b>📋 Join Request Force-Subscribe Channels:</b>\n\n"
        for ch in channels:
            msg += f"• <code>{ch['channel_id']}</code>\n"
        await message.reply_text(msg, parse_mode="html")
    except Exception as e:
        await message.reply_text(f"❌ Error fetching list: {e}")
