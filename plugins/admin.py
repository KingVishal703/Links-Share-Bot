# +++ Modified By [telegram username: @Codeflix_Bots
import os
import asyncio
from config import *
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, ChatAdminRequired, RPCError
from database.database import set_approval_off, is_approval_off, add_admin, remove_admin, list_admins
from database.database import add_membership
from config import ADMINS


@Client.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("Usage: <code>/addadmin {user_id}</code>")
    user_id = int(message.command[1])
    success = await add_admin(user_id)
    if success:
        await message.reply_text(f"✅ User <code>{user_id}</code> added as admin.")
    else:
        await message.reply_text(f"❌ Failed to add admin <code>{user_id}</code>.")

@Client.on_message(filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("Usage: <code>/deladmin {user_id}</code>")
    user_id = int(message.command[1])
    success = await remove_admin(user_id)
    if success:
        await message.reply_text(f"✅ User <code>{user_id}</code> removed from admins.")
    else:
        await message.reply_text(f"❌ Failed to remove admin <code>{user_id}</code>.")

@Client.on_message(filters.command("admins") & filters.user(OWNER_ID))
async def list_admins_command(client, message: Message):
    admins = await list_admins()
    if not admins:
        return await message.reply_text("No admins found.")
    text = "<b>Admin User IDs:</b>\n" + "\n".join([f"<code>{uid}</code>" for uid in admins])
    await message.reply_text(text)


@Client.on_message(filters.command("addmember") & filters.user(ADMINS))
async def add_member_cmd(client, message):

    if len(message.command) != 3:
        return await message.reply_text(
            "Usage:\n/addmember user_id days"
        )

    user_id = int(message.command[1])
    days = int(message.command[2])

    await add_membership(user_id, days)

    await message.reply_text(
        f"✅ Membership Added\n\n"
        f"👤 User: {user_id}\n"
        f"⏳ Days: {days}"
    )
