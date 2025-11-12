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




from pyrogram.types import Message
from database.database import add_fsub_channel, remove_fsub_channel, get_fsub_channels
from config import ADMINS

# ------------------ ADMIN COMMANDS ------------------ #

@Client.on_message(filters.command("addfsub") & filters.user(ADMINS))
async def add_fsub_command(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Usage:\n<code>/addfsub -1001234567890</code>")
    try:
        channel_id = int(message.command[1])
        success = await add_fsub_channel(channel_id)
        if success:
            await message.reply_text(f"✅ Channel <code>{channel_id}</code> added to Force Subscribe list.")
        else:
            await message.reply_text("⚠️ Channel already exists or failed to add.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command("delfsub") & filters.user(ADMINS))
async def del_fsub_command(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Usage:\n<code>/delfsub -1001234567890</code>")
    try:
        channel_id = int(message.command[1])
        success = await remove_fsub_channel(channel_id)
        if success:
            await message.reply_text(f"🗑️ Channel <code>{channel_id}</code> removed from Force Subscribe list.")
        else:
            await message.reply_text("⚠️ Channel not found or failed to remove.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command("listfsub") & filters.user(ADMINS))
async def list_fsub_command(client, message: Message):
    try:
        channels = await get_fsub_channels()
        if not channels:
            return await message.reply_text("📭 No Force Subscribe channels found.")
        msg = "<b>📋 Force Subscribe Channels:</b>\n\n"
        for ch_id in channels:
            msg += f"• <code>{ch_id}</code>\n"
        await message.reply_text(msg, parse_mode="HTML")
    except Exception as e:
        await message.reply_text(f"❌ Error fetching list: {e}")
