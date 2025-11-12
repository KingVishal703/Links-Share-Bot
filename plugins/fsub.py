import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, RPCError
from database.database import get_fsub_channels
from config import OWNER_ID

async def check_subscription_status(client: Client, user_id: int):
    """
    Returns (is_subscribed: bool, message: str, reply_markup: InlineKeyboardMarkup|None)
    """
    fsub_channels = await get_fsub_channels()
    if not fsub_channels:
        return True, None, None

    not_joined = []
    buttons = []
    for ch in fsub_channels:
        try:
            chat = await client.get_chat(ch)
            try:
                member = await client.get_chat_member(chat.id, user_id)
                if member.status in ["member", "administrator", "creator"]:
                    continue
            except UserNotParticipant:
                pass
            except RPCError:
                pass

            if getattr(chat, "username", None):
                join_url = f"https://t.me/{chat.username}"
                buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=join_url)])
            else:
                buttons.append([InlineKeyboardButton(f"Open {chat.title}", callback_data=f"fsub_open_{chat.id}")])

            not_joined.append(chat.title if getattr(chat, "title", None) else str(chat.id))
        except Exception:
            continue

    if not not_joined:
        return True, None, None

    msg = "<b>⚠️ You must join these channel(s) to use the bot:</b>\n\n"
    for n, title in enumerate(not_joined, 1):
        msg += f"{n}. {title}\n"
    msg += "\nAfter joining, press <b>✅ I Joined</b>."

    buttons.append([InlineKeyboardButton("✅ I Joined", callback_data=f"fsub_check_{user_id}")])
    return False, msg, InlineKeyboardMarkup(buttons)

@Client.on_callback_query(filters.regex(r"^fsub_check_(\d+)$"))
async def _fsub_check_cb(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    is_sub, _, _ = await check_subscription_status(client, user_id)
    if is_sub:
        await callback_query.message.edit_text("✅ Thanks — you’ve joined all required channels. You can now use the bot.")
        await callback_query.answer("Checked — you're good ✅", show_alert=False)
    else:
        await callback_query.answer("You still need to join required channels.", show_alert=True)

@Client.on_callback_query(filters.regex(r"^fsub_open_(\-?\d+)$"))
async def _fsub_open_cb(client, callback_query):
    chat_id = int(callback_query.data.split("_")[-1])
    try:
        link = await client.create_chat_invite_link(chat_id, member_limit=1, name="fsub_invite")
        await callback_query.message.reply_text(f"Join using this link: {link.invite_link}")
        await callback_query.answer("Invite link created.", show_alert=False)
    except Exception:
        await callback_query.answer("Unable to create invite. Ask channel admins.", show_alert=True)
