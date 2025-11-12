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
