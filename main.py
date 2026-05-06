import os
import json
import threading
import colorsys
import qrcode
import sys
import io
import asyncio
import logging
import aiohttp
from datetime import datetime
import random
import re
import base64
import tempfile
import gtts
from gtts import gTTS
import wave
import numpy as np
import time 
from io import BytesIO
from pathlib import Path
from aiohttp import web
from PIL import Image, ImageDraw, ImageFont
from telethon.tl import functions
from telethon.tl.functions.messages import ReportRequest
# Army features ke liye imports
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import FloodWaitError
from telethon.tl.types import InputReportReasonSpam, InputReportReasonViolence, InputReportReasonPornography, InputReportReasonOther
from telethon.tl.functions.phone import (
    JoinGroupCallRequest,
    LeaveGroupCallRequest,
    GetGroupCallRequest,
    CreateGroupCallRequest
)
from telethon.errors import ChatAdminRequiredError
from telethon.tl.types import MessageEntityMention
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from datetime import datetime, timedelta
from telethon.tl.functions.users import GetFullUserRequest
from telethon import Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights
from telethon import events, functions, types
from telethon.tl.types import User
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonSpam
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon import events
from telethon.tl.functions.contacts import BlockRequest
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.types import InputPhoto
from telethon.tl.types import MessageEntityMentionName
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality, update
import yt_dlp
import ffmpeg
import edge_tts
#fixed
asyncio.set_event_loop(asyncio.new_event_loop())

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------- CONFIG -----------------s

API_ID = 31461295
API_HASH = "0f151c9b78b4b067c24d30b3160cf14d"
OWNER_ID =8355551382      
SESSION_STRING="1BVtsOLcBu71sWJamaW4e1e_T5TA9fJCB_HfExphwjMqkt92qfHuaXJ1-hQEUxC9w_47xQ7kRCAD_toIzB5Y-kr_ct_PAL46uLl3afgkmnxKzWPwBPr9xUAHv2KUEVYitLvm6qUQ6RfXwwxh2IEJa8ibjm2DVvuRn-O_Mah1gsAWiv5dql5PweTjI_QYQ_b7yfQYa791vfRRew69iWJaHjmy1Ie_3Q8sQjwtYcx1X5dInL72CM_d4YUG32hDF8oXhxHvcuQwdj7XaDetWEHAleiNm9YQ5eEv69keBiJvi7IeZFXMUx4ly0E2BZxcqm2fSeK0YI1rmnfD-nkIei7TOnvRmwMhTJr8="
MUTED_FILE = "muted.json"
STATE_FILE = "state.json"
GBAN_FILE = "gban_list.json"
STORAGE_FILE = "user_replies.json" 
PORT = 10000  # port for web server (if needed)
os.environ["PATH"] += r";C:\ffmpeg\bin"
os.environ["PATH"] += r";C:\ffprobe\bin"
# ------------------------------------------

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ----------------- VC MUSIC CLASS -----------------
class VCMusicPlayer:
    def __init__(self, client):
        self.client = client
        self.call = PyTgCalls(client)
        self.started = False

        self.queue = []
        self.loop = False
        self.current = None
        self.play_task = None

    async def start(self):
        if not self.started:
            await self.call.start()
            self.started = True

    # ───── EXTRACT AUDIO (NO DOWNLOAD) ─────
    async def extract_audio(self, query):
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if query.startswith(("http://", "https://")):
                    info = ydl.extract_info(query, download=False)
                else:
                    results = ydl.extract_info(f"ytsearch:{query}", download=False)
                    info = results["entries"][0]

                return (
                    info.get("url"),
                    info.get("title", "Unknown"),
                    info.get("duration", 0),
                    info.get("thumbnail"),
                )
        except:
            return None, None, None, None

    # ───── EXTRACT VIDEO (NO DOWNLOAD) ─────
    async def extract_video(self, query):
        ydl_opts = {
            "format": "best[height<=720]/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if query.startswith(("http://", "https://")):
                    info = ydl.extract_info(query, download=False)
                else:
                    results = ydl.extract_info(f"ytsearch:{query}", download=False)
                    info = results["entries"][0]

                return (
                    info.get("url"),
                    info.get("title", "Unknown"),
                    info.get("duration", 0),
                    info.get("thumbnail"),
                )
        except:
            return None, None, None, None

    # ───── PLAY FUNCTION (AUDIO OR VIDEO) ─────
    async def play_song(self, chat_id, url, title, duration, thumb, is_video=False):

        if is_video:
            media = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p,
            )
        else:
            media = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
            )

        await self.call.play(chat_id, media)

        self.current = (url, title, duration, thumb, is_video)
                              
        caption = f"""
```╭━━━━⟬ ➲ Started Streaming ⟭━━━━╮
┃
┃⟡➣ Title : {title}
┃⟡➣ Duration : {duration}
┃⟡➣ Loop : {'ON' if self.loop else 'OFF'}
┃⟡➣ Queue : {len(self.queue)} songs
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""

        if thumb:
            try:
                await self.client.send_file(chat_id, thumb, caption=caption)
            except:
                await self.client.send_message(chat_id, caption)
        else:
            await self.client.send_message(chat_id, caption)

        if self.play_task:
            self.play_task.cancel()

        if duration:
            self.play_task = asyncio.create_task(
                self.auto_next(chat_id, duration)
            )

    async def auto_next(self, chat_id, duration):
        await asyncio.sleep(duration)

        if self.loop and self.current:
            await self.play_song(chat_id, *self.current)
            return

        if not self.queue:
            await self.call.leave(chat_id)
            self.current = None
            return

        next_song = self.queue.pop(0)
        await self.play_song(chat_id, *next_song)


vc_player = None

# ================= COMMANDS =================

@client.on(events.NewMessage(pattern=r"\.vply(?:\s+(.*))?"))
async def vplay_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    global vc_player

    if vc_player is None:
        vc_player = VCMusicPlayer(client)

    await vc_player.start()

    query = event.pattern_match.group(1)
    if not query:
        await event.reply("❌ Usage: .vply <video name or link>")
        return

    await event.delete()
    chat_id = event.chat_id
    msg = await event.respond("🎬 Searching Video...")

    url, title, duration, thumb = await vc_player.extract_video(query.strip())

    if not url:
        await msg.edit("❌ Video not found!")
        return

    if vc_player.current:
        vc_player.queue.append((url, title, duration, thumb, True))
        await msg.edit(f"➲ Video Added To Queue:\n{title}")
        return

    await vc_player.play_song(chat_id, url, title, duration, thumb, True)
    await msg.delete()


@client.on(events.NewMessage(pattern=r"\.ply(?:\s+(.*))?"))
async def play_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    global vc_player

    if vc_player is None:
        vc_player = VCMusicPlayer(client)

    await vc_player.start()
    await delete_command_message(event)

    if not event.pattern_match.group(1):
        await event.reply("🎵 Please provide song name or link.\nExample: `.play Believer`")
        return

    query = event.pattern_match.group(1).strip()
    chat_id = event.chat_id
    msg = await event.reply("**🎶 Searching ✨...**")

    # 🔹 Direct extract (no download)
    url, title, duration, thumb = await vc_player.extract_audio(query)

    if not url:
        await msg.edit("❌ Song not found!")
        return

    if vc_player.current:
        vc_player.queue.append((url, title, duration, thumb, False))
        await msg.edit(f"➲ Aᴅᴅᴇᴅ Tᴏ Qᴜᴇᴜᴇ:\n\n ‣ Tɪᴛʟᴇ : **{title}**")
        return

    await vc_player.play_song(chat_id, url, title, duration, thumb, False)
    await msg.delete()
 

@client.on(events.NewMessage(pattern=r"\.skip"))
async def skip_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    
    global vc_player

    if not vc_player or not vc_player.current:
        await event.reply("**❌ Nothing to skip!**")
        return

    if vc_player.play_task:
        vc_player.play_task.cancel()

    if not vc_player.queue:
        await vc_player.call.leave_call(chat_id=event.chat_id)
        vc_player.current = None
        await event.reply("**⏹ No more songs in queue.**")
        return

    next_song = vc_player.queue.pop(0)
    await vc_player.play_song(event.chat_id, *next_song)


@client.on(events.NewMessage(pattern=r"\.loop"))
async def loop_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    global vc_player
    if not vc_player:
        return
    vc_player.loop = not vc_player.loop
    await event.reply(f"**🔁 Loop {'Enabled 🔄' if vc_player.loop else 'Disabled ❌**'}")


@client.on(events.NewMessage(pattern=r"\.queue"))
async def queue_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    global vc_player
    if not vc_player or not vc_player.queue:
        await event.reply("*📭 Queue is empty!**")
        return

    text = "**‣ ǫᴜᴇᴜᴇ ʟɪsᴛ:**\n\n"
    for i, (_, title, _, _) in enumerate(vc_player.queue, 1):
        text += f"{i}. 🎶 {title}\n"

    await event.reply(text)


@client.on(events.NewMessage(pattern=r"\.clear"))
async def clear_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    global vc_player
    if not vc_player:
        return
    vc_player.queue.clear()
    await event.reply("*🗑 Queue cleared!**")


@client.on(events.NewMessage(pattern=r"\.end"))
async def end_cmd(event):
    if event.sender_id != OWNER_ID:
        return
    global vc_player
    await delete_command_message(event)
    if vc_player is None:
        await event.reply("❌ VC player not started.")
        return

    if vc_player.play_task:
        vc_player.play_task.cancel()

    try:
        await vc_player.call.leave_call(chat_id=event.chat_id) 
    except Exception as e:
        await event.reply(f"Error: {e}")
        return

    vc_player.queue.clear()
    vc_player.current = None

    await event.reply("**⏹ Voice chat ended.**")


# load/save muted list (set of user ids)
def load_muted():
    if not os.path.exists(MUTED_FILE):
        return set()
    with open(MUTED_FILE, "r") as f:
        try:
            arr = json.load(f)
            return set(int(x) for x in arr)
        except Exception:
            return set()

def save_muted(muted_set):
    with open(MUTED_FILE, "w") as f:
        json.dump(list(muted_set), f)

muted = load_muted()


# Store event handlers to register after client starts
event_handlers = []

def register_handler(pattern, func, **kwargs):
    event_handlers.append((pattern, func, kwargs))

# helper: resolve target user from reply / mention / username / id
async def resolve_target(event):
    # 1) if reply
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id, (await client.get_entity(reply.sender_id))
    # 2) check entities for mention with user id (MessageEntityMentionName)
    if event.message.entities:
        for ent in event.message.entities:
            if isinstance(ent, MessageEntityMentionName):
                uid = ent.user_id
                try:
                    user = await client.get_entity(uid)
                    return uid, user
                except Exception:
                    pass
    # 3) check text args: .gmute @username or .gmute 123456
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) > 1:
        target_text = parts[1].strip()
        # sometimes people include extra text; take first token
        target_text = target_text.split()[0]
        # numeric id?
        if target_text.isdigit():
            try:
                uid = int(target_text)
                user = await client.get_entity(uid)
                return uid, user
            except Exception:
                return None, None
        # username form like @username or username
        if target_text.startswith("@"):
            target_text = target_text[1:]
        try:
            entity = await client.get_entity(target_text)
            return getattr(entity, "id", None), entity
        except Exception:
            return None, None
    return None, None

# send temporary feedback message and return it
async def reply_and_pin(event, text):
    msg = await event.reply(text)
    return msg

# Command: .gmute
@client.on(events.NewMessage(pattern=r'^\.gmute(?:\s|$)', func=lambda e: True))
async def gmute_handler(event):
    try:
        # only owner can use
        if event.sender_id != OWNER_ID:
            return
        
        # Delete command message after 1 second
        await asyncio.sleep(0.5)
        await event.delete()
        
        target_id, user_entity = await resolve_target(event)
        if not target_id or not user_entity:
            response = await event.reply("**Use reply or provide @username / user_id to gmute.**")
            await asyncio.sleep(1)
            await response.delete()
            return
            
        if target_id == OWNER_ID:
            response = await event.reply("**You can't gmute yourself.**")
            await asyncio.sleep(1)
            await response.delete()
            return
            
        if target_id in muted:
            response = await event.reply(f"**{user_entity.first_name} is already globally muted.**")
            await asyncio.sleep(1)
            await response.delete()
            return
            
        muted.add(int(target_id))
        save_muted(muted)
        
        # Get username for mention or use user ID
        username = getattr(user_entity, "username", None)
        if username:
            display = f"@{username}"
        else:
            display = f"[{user_entity.first_name}](tg://user?id={target_id})"
        
        response = await event.reply(f"**{display}😶 has been globally muted 🔇🔕**")
        
    except Exception as ex:
        response = await event.reply(f"**Error in .gmute: {ex}**")
        await asyncio.sleep(1)
        await response.delete()

@client.on(events.NewMessage(pattern=r'^\.gunmute(?:\s|$)', func=lambda e: True))
async def gunmute_handler(event):
    try:
        # only owner can use
        if event.sender_id != OWNER_ID:
            return
        
        # Delete command message after 1 second
        await asyncio.sleep(0.5)
        await event.delete()
        
        target_id, user_entity = await resolve_target(event)
        if not target_id or not user_entity:
            response = await event.reply("**Use reply or provide @username / user_id to gunmute.**")
            await asyncio.sleep(1)
            await response.delete()
            return
            
        if int(target_id) not in muted:
            response = await event.reply(f"**{user_entity.first_name} is not muted**")
            await asyncio.sleep(1)
            await response.delete()
            return
            
        muted.discard(int(target_id))
        save_muted(muted)
        
        # Get username for mention or use user ID
        username = getattr(user_entity, "username", None)
        if username:
            display = f"@{username}"
        else:
            display = f"[{user_entity.first_name}](tg://user?id={target_id})"
        
        response = await event.reply(f"**{display} 🎁 has been globally unmuted 🔊🔔**")
        
    except Exception as ex:
        response = await event.reply(f"**Error in .gunmute: {ex}**")
        await asyncio.sleep(1)
        await response.delete()


# Optional: .gmutedlist to show current list (owner only)
@client.on(events.NewMessage(pattern=r'^\.gmutedlist(?:\s|$)', func=lambda e: True))
async def gmuted_list(event):
    if event.sender_id != OWNER_ID:
        return
        
    if not muted:
        await event.reply("No one is globally muted.")
        await asyncio.sleep(1)
        await event.delete()
        return
    text = "Globally muted:\n"
    for uid in list(muted):
        try:
            ent = await client.get_entity(int(uid))
            name = ent.first_name or getattr(ent, "username", str(uid))
        except Exception:
            name = str(uid)
        text += f" - {name} [{uid}]\n"
    await event.reply(text)

# Listener: delete incoming messages from muted users
@client.on(events.NewMessage(incoming=True))
async def delete_from_muted(event):
    try:
        sender = event.sender_id
        if sender and int(sender) in muted:
            # Try to delete the message. This will succeed only if:
            # - you're admin with delete rights in the chat (for groups/channels), OR
            # - it's a private chat and you delete for yourself
            try:
                # event.delete() deletes current message
                await event.delete()
            except errors.rpcerrorlist.MessageDeleteForbiddenError:
                # No permission to delete other's messages in this chat
                # You can try client.delete_messages(chat, event.message.id) as another approach
                try:
                    await client.delete_messages(event.chat_id, [event.message.id])
                except Exception:
                    # optionally inform owner (but to avoid spam, we skip)
                    pass
            except Exception:
                # ignore other failures
                pass
    except Exception:
        pass

    # Global variables for reaction and tag tasks
react_task = None
tag_task = None

@client.on(events.NewMessage(pattern=r'\.extract'))
async def extract_handler(event):
    """Extract phone number from target bot"""
    try:
        # Delete the command message immediately
        await event.delete()
        
        # Check if user replied to someone
        if not event.is_reply:
            error_msg = await event.reply("❌ Please reply to a user to extract their info!")
            await asyncio.sleep(3)
            await error_msg.delete()
            return
        
        replied_msg = await event.get_reply_message()
        target_user = replied_msg.sender_id
        
        # Send fetching message
        fetching_msg = await event.reply("⚡ 𝐅𝐞𝐭𝐜𝐡𝐢𝐧𝐠 𝐃𝐞𝐭𝐚𝐢𝐥𝐬...")
        
        # Target bot username
        TARGET_BOT = '@mzjugabot'
        
        # Send target user ID to bot
        await client.send_message(TARGET_BOT, f"{target_user}")
        
        # Wait for bot's response
        await asyncio.sleep(3)
        
        # Get bot's response
        phone_found = False
        extracted_phone = "Not Found"
        extracted_id = str(target_user)
        
        async for msg in client.iter_messages(TARGET_BOT, limit=1):
            bot_response = msg
            
            # Check if bot replied with inline button
            if bot_response and bot_response.reply_markup and bot_response.reply_markup.rows:
                
                # Look for button with text "telegram"
                for row in bot_response.reply_markup.rows:
                    for button in row.buttons:
                        if 'telegram' in button.text.lower():
                            
                            # Click the telegram button
                            await bot_response.click(data=button.data)
                            await asyncio.sleep(2)
                            
                            # Get the final response
                            async for final_msg in client.iter_messages(TARGET_BOT, limit=1):
                                final_response = final_msg
                                
                                # Parse the bot's response - UPDATED REGEX
                                response_text = final_response.text
                                
                                # Extract ID (with markdown formatting)
                                id_match = re.search(r'\*\*ID:\*\*\s*`(\d+)`', response_text) or \
                                          re.search(r'💬\s*\*\*ID:\*\*\s*`(\d+)`', response_text)
                                
                                # Extract phone number (with markdown formatting)
                                phone_match = re.search(r'\*\*Телефон:\*\*\s*`(\+?\d+)`', response_text) or \
                                            re.search(r'📞\s*\*\*Телефон:\*\*\s*`(\+?\d+)`', response_text)
                                
                                if id_match:
                                    extracted_id = id_match.group(1)
                                
                                if phone_match:
                                    extracted_phone = phone_match.group(1)
                                    phone_found = True
                                else:
                                    # Try alternate format without backticks
                                    phone_match2 = re.search(r'Телефон:\s*(\+?\d+)', response_text)
                                    if phone_match2:
                                        extracted_phone = phone_match2.group(1)
                                        phone_found = True
                                
                            break
                            
        # Delete fetching message
        await fetching_msg.delete()
        
        # Final stylish response
        final_output = f"""
```╭━━━━⟬📱 PHONE LOOKUP⟭━━━━╮
┃                           
┃    ✦➣ 🎯 Target: {target_user}
┃                           
┃    ✦➣ 📞 Phone: +{extracted_phone}
┃                           
┃    ✦➣ 🏷️ Found by BLAZY_XSOUL
┃                           
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
        
        await event.reply(final_output)
        
    except Exception as e:
        # Agar koi error aaye toh bhi Not Found response bhejo
        try:
            target_user = replied_msg.sender_id if 'replied_msg' in locals() else "Unknown"
            error_output = f"""
```╭━━━━⟬📱 PHONE LOOKUP⟭━━━━╮
┃                           
┃    ✦➣ 🎯 Target: {target_user}
┃                           
┃    ✦➣ 📞 Phone: Not Found 
┃                           
┃    ✦➣ 🏷️ Found by BLAZY_XSOUL
┃                           
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
            await event.reply(error_output)
        except:
            await event.reply(f"❌ Error: {str(e)}")
        
# Command: .all <message> - tag members one by one
@client.on(events.NewMessage(pattern=r'^\.all\s+(.+)$', func=lambda e: True))
async def tag_all_handler(event):
    global tag_task
    
    if event.sender_id != OWNER_ID:
        return
    
    await delete_command_message(event)
    
    if tag_task:
        await event.reply("**Tagging already in progress. Use .cancel to stop.**")
        await asyncio.sleep(0.6)
        await event.delete()
        return
    
    message_text = event.pattern_match.group(1)
    
    reply = await event.reply("**Starting to tag members......**")
    await asyncio.sleep(0.8)
    await reply.delete()
    
    # Start tagging task
    tag_task = asyncio.create_task(tag_members_one_by_one(event.chat_id, message_text))

async def tag_members_one_by_one(chat_id, message_text):
    global tag_task
    try:
        participants = await client.get_participants(chat_id)
        for user in participants:
            if not user.bot and user.id != OWNER_ID:
                try:
                    await client.send_message(chat_id, f"[{user.first_name}](tg://user?id={user.id}) {message_text}")
                    await asyncio.sleep(0.1)  # Avoid flood
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        tag_task = None

# Command: .cancel - cancel tagging
@client.on(events.NewMessage(pattern=r'^\.cancel(?:\s|$)', func=lambda e: True))
async def cancel_handler(event):
    global tag_task
    
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    if tag_task:
        tag_task.cancel()
        tag_task = None
        tag = await event.reply("**Tagging cancelled.**")
        await asyncio.sleep(0.6)
        await tag.delete()
    else:
        wow = await event.reply("No tagging in progress.")
        await asyncio.sleep(0.6)
        await wow.delete()

        # Global variable for spam task
spam_task = None

# Command: .spam <delay> <message> - auto spam message with custom delay
@client.on(events.NewMessage(pattern=r'^\.spam\s+(\d+\.?\d*)\s+(.+)$', func=lambda e: True))
async def spam_handler(event):
    global spam_task
    
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    if spam_task:
        spam = await event.reply("⚠️ Spam already running. Use `.stopspam` to stop.")
        await asyncio.sleep(0.6)
        await spam.delete()
        return
    
    # Extract delay time and message
    delay_time = float(event.pattern_match.group(1))
    message_text = event.pattern_match.group(2)
    
    # Validate delay time
    if delay_time < 0.1:
        ok = await event.reply("❌ Minimum delay is 0.1 seconds")
        await asyncio.sleep(0.6)
        await ok.delete()
        return
    
    delay = await event.reply(f"🚀 Spam started (delay: {delay_time}s)... Use `.stopspam` to stop")
    await asyncio.sleep(0.6)
    await delay.delete()
    
    # Start spam task
    spam_task = asyncio.create_task(auto_spam(event.chat_id, message_text, delay_time))

async def auto_spam(chat_id, message_text, delay_time):
    global spam_task
    try:
        while True:
            await client.send_message(chat_id, message_text)
            await asyncio.sleep(delay_time)  # Custom delay time
    except Exception:
        pass
    finally:
        spam_task = None

# Command: .stopspam - stop spam
@client.on(events.NewMessage(pattern=r'^\.stopspam(?:\s|$)', func=lambda e: True))
async def stop_spam_handler(event):
    global spam_task
    
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    if spam_task:
        spam_task.cancel()
        spam_task = None
        stop = await event.reply("🛑 Spam stopped.")
        await asyncio.sleep(0.6)
        await stop.delete()
    else:
        no = await event.reply("❌ No spam running.")
        await asyncio.sleep(0.6)
        await no.delete()

@client.on(events.NewMessage(pattern=r'^\.ban(?:\s+(@?\w+))?', outgoing=True))
async def ban_cmd(event):
    """Ban a user from the group"""
    reply = await event.get_reply_message()
    
    # Get user from reply or from command
    if reply:
        user = await reply.get_sender()
    else:
        username = event.pattern_match.group(1)
        if not username:
            await event.edit("❌ **Usage:** `.ban <username>` or reply to user")
            await asyncio.sleep(3)
            await event.delete()
            return
        
        try:
            user = await client.get_entity(username)
        except:
            await event.edit("❌ **User not found!**")
            await asyncio.sleep(3)
            await event.delete()
            return
    
    # Check if group
    if not event.is_group:
        await event.edit("❌ **This command works only in groups!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    try:
        # Ban rights - can't send messages, media, etc.
        banned_rights = ChatBannedRights(
            until_date=None,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True
        )
        
        await client(EditBannedRequest(event.chat_id, user.id, banned_rights))
        
        # Get chat title
        chat = await event.get_chat()
        chat_title = chat.title or "Unknown Chat"
        
        # Create fancy response
        response = f"""
```╭━━━━⟬ 🔨 USER BANNED ⟭━━━━╮
┃⟡➣ User: @{user.username if user.username else user.first_name}
┃
┃⟡➣ Chat: {chat_title}
┃
┃⟡➣ Status: Banned permanently
╰━━━━━━━━━━━━━━━╯```
        """
        
        await event.edit(response)
        
    except Exception as e:
        await event.edit(f"❌ **Ban Error:** `{str(e)}`")
        await asyncio.sleep(3)
        await event.delete()

# ============================================
# UNBAN COMMAND
# ============================================
@client.on(events.NewMessage(pattern=r'^\.unban(?:\s+(@?\w+))?', outgoing=True))
async def unban_cmd(event):
    """Unban a user from the group"""
    reply = await event.get_reply_message()
    
    # Get user from reply or from command
    if reply:
        user = await reply.get_sender()
    else:
        username = event.pattern_match.group(1)
        if not username:
            await event.edit("❌ **Usage:** `.unban <username>` or reply to user")
            await asyncio.sleep(3)
            await event.delete()
            return
        
        try:
            user = await client.get_entity(username)
        except:
            await event.edit("❌ **User not found!**")
            await asyncio.sleep(3)
            await event.delete()
            return
    
    if not event.is_group:
        await event.edit("❌ **This command works only in groups!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    try:
        # Unban rights - remove all restrictions
        unban_rights = ChatBannedRights(
            until_date=None,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False
        )
        
        await client(EditBannedRequest(event.chat_id, user.id, unban_rights))
        
        # Get chat title
        chat = await event.get_chat()
        chat_title = chat.title or "Unknown Chat"
        
        response = f"""
```╭━━━━⟬ ✅ USER UNBANNED ⟭━━━━╮
┃⟡➣ User: @{user.username if user.username else user.first_name}
┃
┃⟡➣ Chat: {chat_title}
┃        
┃⟡➣ Status: Can send messages now
╰━━━━━━━━━━━━━━━╯```
        """
        
        await event.edit(response)
        
    except Exception as e:
        await event.edit(f"❌ **Unban Error:** `{str(e)}`")
        await asyncio.sleep(3)
        await event.delete()

# ============================================
# MUTE COMMAND (with time)
# ============================================
@client.on(events.NewMessage(pattern=r'^\.mute(?:\s+(@?\w+))?(?:\s+(\d+))?', outgoing=True))
async def mute_cmd(event):
    """Mute a user in the group (optional time in minutes)"""
    reply = await event.get_reply_message()
    
    # Parse arguments
    args = event.pattern_match.group(1)
    minutes = event.pattern_match.group(2)
    
    # Get user
    if reply:
        user = await reply.get_sender()
        mute_time = int(minutes) if minutes else None
    else:
        if not args:
            await event.edit("❌ **Usage:** `.mute @user [minutes]` or reply to user")
            await asyncio.sleep(3)
            await event.delete()
            return
        
        parts = args.split()
        username = parts[0]
        mute_time = int(parts[1]) if len(parts) > 1 else None
        
        try:
            user = await client.get_entity(username)
        except:
            await event.edit("❌ **User not found!**")
            await asyncio.sleep(3)
            await event.delete()
            return
    
    if not event.is_group:
        await event.edit("❌ **This command works only in groups!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    try:
        # Set mute duration
        if mute_time:
            until_date = datetime.now() + timedelta(minutes=mute_time)
            status = f"Muted for {mute_time} minute(s)"
        else:
            until_date = None
            status = "Muted permanently (until unmute)"
        
        # Mute rights - can't send messages
        muted_rights = ChatBannedRights(
            until_date=until_date,
            send_messages=True
        )
        
        await client(EditBannedRequest(event.chat_id, user.id, muted_rights))
        
        # Get chat title
        chat = await event.get_chat()
        chat_title = chat.title or "Unknown Chat"
        
        response = f"""
```╭━━━━⟬ 🔇 USER MUTED ⟭━━━━╮
┃⟡➣ User: @{user.username if user.username else user.first_name}
┃
┃⟡➣ Chat: {chat_title}
┃
┃⟡➣ Status: {status}
╰━━━━━━━━━━━━━━━╯```
        """
        
        await event.edit(response)
        
    except Exception as e:
        await event.edit(f"❌ **Mute Error:** `{str(e)}`")
        await asyncio.sleep(3)
        await event.delete()

# ============================================
# UNMUTE COMMAND
# ============================================
@client.on(events.NewMessage(pattern=r'^\.unmute(?:\s+(@?\w+))?', outgoing=True))
async def unmute_cmd(event):
    """Unmute a user in the group"""
    reply = await event.get_reply_message()
    
    # Get user
    if reply:
        user = await reply.get_sender()
    else:
        username = event.pattern_match.group(1)
        if not username:
            await event.edit("❌ **Usage:** `.unmute @user` or reply to user")
            await asyncio.sleep(3)
            await event.delete()
            return
        
        try:
            user = await client.get_entity(username)
        except:
            await event.edit("❌ **User not found!**")
            await asyncio.sleep(3)
            await event.delete()
            return
    
    if not event.is_group:
        await event.edit("❌ **This command works only in groups!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    try:
        # Unmute rights
        unmute_rights = ChatBannedRights(
            until_date=None,
            send_messages=False
        )
        
        await client(EditBannedRequest(event.chat_id, user.id, unmute_rights))
        
        # Get chat title
        chat = await event.get_chat()
        chat_title = chat.title or "Unknown Chat"
        
        response = f"""
```╭━━━━⟬ 🔊 USER UNMUTED ⟭━━━━╮
┃⟡➣ User: @{user.username if user.username else user.first_name}
┃
┃⟡➣ Chat: {chat_title}
┃
┃⟡➣ Status: Can send messages now
╰━━━━━━━━━━━━━━━╯```
        """
        
        await event.edit(response)
        
    except Exception as e:
        await event.edit(f"❌ **Unmute Error:** `{str(e)}`")
        await asyncio.sleep(3)
        await event.delete()

# ============================================
# KICK COMMAND
# ============================================
@client.on(events.NewMessage(pattern=r'^\.kick(?:\s+(@?\w+))?', outgoing=True))
async def kick_cmd(event):
    """Kick a user from the group"""
    reply = await event.get_reply_message()
    
    # Get user
    if reply:
        user = await reply.get_sender()
    else:
        username = event.pattern_match.group(1)
        if not username:
            await event.edit("❌ **Usage:** `.kick @user` or reply to user")
            await asyncio.sleep(3)
            await event.delete()
            return
        
        try:
            user = await client.get_entity(username)
        except:
            await event.edit("❌ **User not found!**")
            await asyncio.sleep(3)
            await event.delete()
            return
    
    if not event.is_group:
        await event.edit("❌ **This command works only in groups!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    try:
        # Kick user
        await client.kick_participant(event.chat_id, user.id)
        
        # Get chat title
        chat = await event.get_chat()
        chat_title = chat.title or "Unknown Chat"
        
        response = f"""
```╭━━━━⟬ 👢 USER KICKED ⟭━━━━╮
┃⟡➣ User: @{user.username if user.username else user.first_name}
┃
┃⟡➣ Chat: {chat_title}
┃
┃⟡➣ Status: Removed from group
╰━━━━━━━━━━━━━━━╯```
        """
        
        await event.edit(response)
        
    except Exception as e:
        await event.edit(f"❌ **Kick Error:** `{str(e)}`")
        await asyncio.sleep(3)
        await event.delete()
        
        # Command: .purge - delete messages from replied message to current
@client.on(events.NewMessage(pattern=r'^\.purge(?:\s|$)', func=lambda e: True))
async def purge_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    if not event.is_reply:
        await event.edit("❌ Reply to a message to start purge from there.")
        await asyncio.sleep(0.6)
        await event.delete()
        return
    
    try:
        start_message = await event.get_reply_message()
        start_id = start_message.id
        end_id = event.message.id
        
        await event.delete()  # Delete the purge command message
        
        message_ids = []
        current_id = start_id
        
        while current_id <= end_id:
            message_ids.append(current_id)
            current_id += 1
            # Telegram allows max 100 messages per delete request
            if len(message_ids) >= 100:
                await client.delete_messages(event.chat_id, message_ids)
                message_ids = []
                await asyncio.sleep(0.5)  # Avoid flood
        
        # Delete any remaining messages
        if message_ids:
            await client.delete_messages(event.chat_id, message_ids)
        
        # Send confirmation (it will be the last message)
        confirm_msg = await event.respond(f"✅ Purged {end_id - start_id + 1} messages")
        await asyncio.sleep(3)
        await confirm_msg.delete()
        
    except Exception as e:
        await event.reply(f"❌ Error during purge: {str(e)}")
        
import os
import re
import aiohttp
import asyncio
import yt_dlp
from datetime import datetime
from telethon import events

# Required installations:
# pip install yt-dlp aiohttp

@client.on(events.NewMessage(pattern=r"\.dl(?: |$)(.*)"))
async def media_downloader(event):
    """Universal media downloader for Instagram, YouTube, Terabox"""
    if event.sender_id != OWNER_ID:
        return
    
    await delete_command_message(event)
    
    url = event.pattern_match.group(1).strip()
    
    if not url:
        await event.reply("**Usage:** `.dl <url>`\n\n**Supported:**\n• YouTube\n• Instagram\n• Terabox")
        return
    
    # Check URL type
    if "youtube.com" in url or "youtu.be" in url:
        await download_youtube(event, url)
    elif "instagram.com" in url or "instagr.am" in url:
        await download_instagram(event, url)
    elif "terabox" in url or "4funbox" in url or "1024tera" in url:
        await download_terabox(event, url)
    else:
        await event.reply("❌ Unsupported URL. Only YouTube, Instagram, and Terabox are supported.")

async def download_youtube(event, url):
    """Download YouTube videos"""
    msg = await event.reply("📥 **Downloading YouTube video...**")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
        'progress_hooks': [lambda d: progress_hook(d, msg)],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get video info
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
            
            # Send info first
            info_msg = f"🎬 **YouTube Video**\n"
            info_msg += f"📌 **Title:** {title}\n"
            info_msg += f"⏱️ **Duration:** {duration//60}:{duration%60:02d}\n"
            info_msg += f"👤 **Channel:** {uploader}\n"
            info_msg += f"⬇️ **Downloading...**"
            
            await msg.edit(info_msg)
            
            # Download video
            ydl.download([url])
            
            # Find downloaded file
            filename = ydl.prepare_filename(info)
            
            # Check if file exists
            if os.path.exists(filename):
                # Check file size (Telegram limit: 2GB for premium, 2GB for normal)
                file_size = os.path.getsize(filename)
                
                if file_size > 2000 * 1024 * 1024:  # 2GB limit
                    await msg.edit("❌ File size exceeds 2GB limit. Trying to download lower quality...")
                    
                    # Try lower quality
                    ydl_opts['format'] = 'best[filesize<2G]'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        ydl2.download([url])
                        filename = ydl2.prepare_filename(info)
                
                # Send video
                await event.client.send_file(
                    event.chat_id,
                    filename,
                    caption=f"🎬 **{title}**\n **✨ POWERED BY NEXUS USERBOT**\n **🌟 OWNER - @swaha01 & @shdxmr**",
                    supports_streaming=True,
                    progress_callback=lambda current, total: upload_progress(current, total, msg, title)
                )
                
                await msg.delete()
                
                # Clean up
                try:
                    os.remove(filename)
                except:
                    pass
            else:
                await msg.edit("❌ Failed to download video.")
                
    except Exception as e:
        await msg.edit(f"❌ YouTube Error: {str(e)}")

async def download_instagram(event, url):
    """Download Instagram posts, reels, stories"""
    msg = await event.reply("📸 **Downloading Instagram media...**")
    
    # Check if it's a story
    is_story = "/stories/" in url
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:  # Multiple items (carousel)
                entries = list(info['entries'])
                total = len(entries)
                
                await msg.edit(f"📸 **Instagram Carousel**\n📊 **Posts:** {total}\n⬇️ **Downloading...**")
                
                for i, entry in enumerate(entries, 1):
                    if entry.get('url'):
                        media_url = entry['url']
                        # Download and send each media
                        async with aiohttp.ClientSession() as session:
                            async with session.get(media_url) as resp:
                                if resp.status == 200:
                                    content = await resp.read()
                                    
                                    # Determine file type
                                    content_type = resp.headers.get('Content-Type', '')
                                    ext = '.mp4' if 'video' in content_type else '.jpg'
                                    filename = f"downloads/insta_{i}{ext}"
                                    
                                    with open(filename, 'wb') as f:
                                        f.write(content)
                                    
                                    # Send file
                                    await event.client.send_file(
                                        event.chat_id,
                                        filename,
                                        caption=f"📸 Instagram Post {i}/{total}",
                                        reply_to=event.message if i == 1 else None
                                    )
                                    
                                    # Clean up
                                    try:
                                        os.remove(filename)
                                    except:
                                        pass
                                    
                                    await asyncio.sleep(1)
                
                await msg.delete()
                
            else:  # Single media
                title = info.get('title', 'Instagram Media')
                uploader = info.get('uploader', 'Unknown')
                
                await msg.edit(f"📸 **Instagram Post**\n📌 **By:** {uploader}\n⬇️ **Downloading...**")
                
                # Download the media
                ydl.download([url])
                
                # Find downloaded file
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    # Check if it's video or image
                    is_video = filename.endswith(('.mp4', '.mkv', '.webm'))
                    
                    await event.client.send_file(
                        event.chat_id,
                        filename,
                        caption=f"📸 **Instagram {'Reel' if is_video else 'Post'}\n **✨ POWERED BY NEXUS USERBOT**\n **🌟 OWNER - @swaha01 & @shdxmr**",
                        supports_streaming=True if is_video else False,
                        progress_callback=lambda current, total: upload_progress(current, total, msg, title)
                    )
                    
                    await msg.delete()
                    
                    # Clean up
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    await msg.edit("❌ Failed to download Instagram media.")
    
    except Exception as e:
        await msg.edit(f"❌ Instagram Error: {str(e)}")

async def download_terabox(event, url):
    """Download from Terabox"""
    msg = await event.reply("📦 **Processing Terabox link...**")
    
    try:
        # Extract file ID from URL
        pattern = r'terabox\.(?:app|com)/(?:s/|sharing/)?([a-zA-Z0-9_-]+)'
        match = re.search(pattern, url)
        
        if not match:
            await msg.edit("❌ Invalid Terabox URL.")
            return
        
        file_id = match.group(1)
        
        # Terabox API endpoint (Note: This might change)
        api_url = f"https://www.terabox.com/api/shorturlinfo?shorturl={file_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        async with aiohttp.ClientSession() as session:
            # Get file info
            async with session.get(api_url, headers=headers) as resp:
                if resp.status != 200:
                    await msg.edit("❌ Failed to fetch Terabox info.")
                    return
                
                data = await resp.json()
                
                if data.get('errno') != 0:
                    await msg.edit("❌ Invalid or expired link.")
                    return
                
                file_info = data.get('list', [{}])[0]
                file_name = file_info.get('server_filename', 'Unknown')
                file_size = file_info.get('size', 0)
                direct_link = file_info.get('dlink', '')
                
                if not direct_link:
                    await msg.edit("❌ No download link found.")
                    return
                
                # Convert size to readable format
                size_mb = file_size / (1024 * 1024)
                
                info_msg = f"📦 **Terabox File**\n"
                info_msg += f"📄 **Name:** {file_name}\n"
                info_msg += f"📊 **Size:** {size_mb:.2f} MB\n"
                info_msg += f"⬇️ **Downloading...**"
                
                await msg.edit(info_msg)
                
                # Download file
                download_path = f"downloads/{file_name}"
                
                async with session.get(direct_link, headers=headers) as download_resp:
                    if download_resp.status == 200:
                        total_size = int(download_resp.headers.get('Content-Length', 0))
                        
                        with open(download_path, 'wb') as f:
                            downloaded = 0
                            async for chunk in download_resp.content.iter_chunked(1024*1024):  # 1MB chunks
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Update progress every 5MB
                                    if downloaded % (5*1024*1024) < 1024*1024:
                                        percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                                        await msg.edit(f"{info_msg}\n📥 **Progress:** {percent:.1f}%")
                        
                        # Send file
                        await event.client.send_file(
                            event.chat_id,
                            download_path,
                            caption=f"📦 **{file_name}**\n💾 {size_mb:.2f} MB",
                            progress_callback=lambda current, total: upload_progress(current, total, msg, file_name)
                        )
                        
                        await msg.delete()
                        
                        # Clean up
                        try:
                            os.remove(download_path)
                        except:
                            pass
                    else:
                        await msg.edit("❌ Failed to download file.")
    
    except Exception as e:
        await msg.edit(f"❌ Terabox Error: {str(e)}")

def progress_hook(d, msg):
    """Progress hook for yt-dlp"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        
        asyncio.create_task(
            msg.edit(f"📥 **Downloading...**\n📊 **Progress:** {percent}\n🚀 **Speed:** {speed}\n⏳ **ETA:** {eta}")
        )

async def upload_progress(current, total, msg, filename):
    """Upload progress callback"""
    percent = (current / total) * 100 if total > 0 else 0
    
    # Update every 5% progress
    if int(percent) % 5 == 0:
        try:
            await msg.edit(
                f"📤 **Uploading...**\n"
                f"📄 **File:** {filename[:30]}...\n"
                f"📊 **Progress:** {percent:.1f}%\n"
                f"💾 **Size:** {current/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB"
            )
        except:
            pass
        
@client.on(events.NewMessage(pattern=r'\.delall(?:\s+(.+))?'))
async def delete_all_messages(event):
    """Delete all messages of a user in group"""
    
    if event.sender_id != OWNER_ID:
        return
    
    # Check if in group
    if not event.is_group:
        await event.delete()  # Delete command
        await event.reply("❌ This command works only in groups!", reply_to=event.id)
        return
    
    # Check admin permissions
    try:
        participant = await event.client.get_permissions(event.chat_id, event.sender_id)
        if not (participant.is_admin or participant.is_creator):
            await event.delete()  # Delete command
            await event.reply("❌ You need to be admin to use this command!", reply_to=event.id)
            return
    except:
        await event.delete()  # Delete command
        await event.reply("❌ Could not check admin permissions!", reply_to=event.id)
        return
    
    # Get target user
    target_user = None
    args = event.pattern_match.group(1)
    
    if event.is_reply:
        # Case 1: Reply to user's message
        reply_msg = await event.get_reply_message()
        target_user = reply_msg.sender_id
        
    elif args and args.startswith('@'):
        # Case 2: @username provided
        try:
            username = args[1:]  # Remove @
            user = await event.client.get_entity(username)
            target_user = user.id
        except:
            await event.delete()  # Delete command
            await event.reply(f"❌ User @{username} not found!", reply_to=event.id)
            return
    
    elif args and args.isdigit():
        # Case 3: User ID provided
        target_user = int(args)
    
    else:
        await event.delete()  # Delete command
        await event.reply(
            "**Usage:**\n"
            "1. `.delall` - Reply to user's message\n"
            "2. `.delall @username` - Delete messages of @username\n"
            "3. `.delall 123456789` - Delete messages by user ID",
            reply_to=event.id
        )
        return
    
    # Get user info
    try:
        user_entity = await event.client.get_entity(target_user)
        username = f"@{user_entity.username}" if user_entity.username else user_entity.first_name
    except:
        username = f"User {target_user}"
    
    # Delete the command message first
    await event.delete()
    
    # Send initial reply
    response_msg = await event.reply(f"🗑️ **Deleting all messages from {username}...**")
    
    deleted_count = 0
    failed_count = 0
    
    try:
        # Get all messages from user
        async for message in event.client.iter_messages(
            event.chat_id,
            from_user=target_user
        ):
            try:
                await message.delete()
                deleted_count += 1
                
                # Delay to avoid flood
                await asyncio.sleep(0.2)
                
            except:
                failed_count += 1
                continue
            
        await response_msg.delete()
        
        # Update final result
        await response_msg.reply(
            f"```✅ Deletion Complete!\n\n"
            f"👤 User: {username}\n"
            f"✅ Deleted: {deleted_count}\n"
            f"❌ Failed: {failed_count}```"
        )
        
    except Exception as e:
        await response_msg.edit(f"❌ Error: {str(e)[:200]}")
        
STYLES = [
    ("𓂃❛ ⟶", "❜ 🌙⤹🌸"), ("❍⏤●", "●───♫▷"),
    ("🤍 ⍣⃪ ᶦ ᵃᵐ⛦⃕", "❛𝆺𝅥⤹࿗𓆪ꪾ™"),
    ("𓆰𝅃🔥", "⃪⍣꯭꯭𓆪꯭🝐"),
    ("◄❥❥⃝⃪⃕🦚⟵᷽᷍", "˚◡⃝🐬𔘓❁❍•:➛"),
    ("➺꯭꯭꯭𝅥𝆬🦋─⃛┼", "🥵⃝⃝ᬽ⃪꯭➺꯭⎯⎯᪵᪳"),
    ("◄⏤🝛꯭𝐈𝛕ᷟ𝚣⃪ꙴ🥀⃝⃪", "⃝☠️⎯꯭𓆩♡꧂"),
    ("🦋⃟≛⃝⋆⋆≛⃞", "𝄟🦋⃟≛⃝≛"),
    ("𐏓𓆩❤️🔥𓆪𝆺꯭𝅥༎ࠫ⛧", "ࠫ༎𝆺𝅥𓆩⍣꯭⃟🍷༎᪵⛧"),
    ("𓄂𝆺𝅥⃝🥀𖥫꯭꯭𝆺꯭꯭𝅥", "𝆺꯭𝅥🎭🌹"),
    ("𓄂─⃛𓆩🫧𝆺𝅥⃝𐏓", "㋛𓆪꯭⵿٭🍃"),
    ("◄⏤⃪⃝⃪𐏓🝛꯭", "⸙ꠋꠋ⛦⃪⃪🝛꯭••➤"),
    ("🎡𓆩᪵🌸⃝۫𝞄⃕𝖋𝖋꯭ᜊ𝆺𝅥⃝", "┼⃖ꭗ🦋¦🌺--🎋"),
    ("⛦⃕𝄟•๋๋🦋⃟⃟⃟≛⃝💖", "🦋•๋๋𝄟"),
    ("••ᯓ❥๋๋ꗝ༎꯭ࠫ🤍𝆺꯭𝅥", "𝆺꯭𝅥༎ࠫ◡⃝𑲭"),
    ("𝐈𝛕ᷟ𝚣⃪ꙴ⋆†།┼⃖•🔥⃞⃪⃜", "🔥⃞⃪⃜𓆪🦋✿"),
    ("❍─⃜𓆩〭〬🤍𓆪˹", ".⍣⃪ꭗ𝆺𝅥𔘓🪽"),
    ("𝆺𝅥اـ꯭ـ꯭𝞂⃕𝝲𝝴꯭•⚚•𝆺꯭𝅥", "𝆺꯭𝅥ꀭ‧₊𝁾⟶🍃˚"),
    ("◄⏤🔥⃝⃪🐼𓆩꯭❛", "❜꯭𓆪⎯⟶"),
    ("❍─⃜𓆩〭〬👒𓆪⃪꯭", "🤍𝆺꯭𝅥⎯⎯"),
    ("◄⏤❥≛⃝", "🍁⃝➤🕊⃝🝐"),
    ("◄⏤🫧⃝⃪🦋", "◡⃝ا۬🌸𝆺꯭𝅥⎯꯭"),
    ("◄ᯓ❥≛⃝🌸", "💗⃝꯭꯭❥꯭꯭✿꯭꯭࿐"),
    ("𓆩💀⃝🖤☠️", "☠️🖤⃝💀𓆪"),
    ("⛧⃝🔥𓆩👑", "👑𓆪⃪🔥⃝⛧"),
    ("𓂀⃝🦋⛦⃕💫", "💫⛦⃪🦋⃝𓂀"),
    ("𓆩⚡️⃝🔥💥", "💥🔥⃝⚡️𓆪"),
    ("✦⃝💫𓆩🌌", "🌌𓆪⃪💫⃝✦"),
    ("𓆩🍷⃝✨⛧", "⛧⃪✨⃝🍷𓆪"),
    ("❛⃝🌑𓆩☠️", "☠️𓆪⃪🌑⃝❜"),
    ("𓆩🎀⃝💖⛦", "⛦⃪💖⃝🎀𓆪"),
    ("✧⃝🌺𓆩🦋", "🦋𓆪⃪🌺⃝✧"),
    ("𓆩🔥⃝⚔️👑", "👑⚔️⃝🔥𓆪"),
    ("◄⏤🌪⃝⃪💫", "💫⃝🌪⏤►"),
    ("𓆩🕯⃝🌑☠️", "☠️🌑⃝🕯𓆪"),
    ("⛦⃕⃝🔥𓆩💎", "💎𓆪⃪🔥⃝⛦⃕"),
]


def split_text(text, limit=3900):
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:]
    parts.append(text)
    return parts

@client.on(events.NewMessage(pattern=r"\.name(?: |$)(.*)"))
async def name_handler(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    name = event.pattern_match.group(1).strip()

    if not name:
        name = await event.reply("❌ Use: `.name YourName`")
        await asyncio.sleep(0.6)
        await name.delete()
        return

    text = "✨ **Stylish Name Results** ✨\n\n"
    for i, (l, r) in enumerate(STYLES, 1):
        text += f"{i}. `{l} {name} {r}`\n"

    for chunk in split_text(text):
        await event.reply(chunk)

        
        #banned users set

def load_gban_list():
    """Load GBan list from JSON file"""
    if os.path.exists(GBAN_FILE):
        try:
            with open(GBAN_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_gban_list(gban_list):
    """Save GBan list to JSON file"""
    with open(GBAN_FILE, 'w') as f:
        json.dump(gban_list, f, indent=4, default=str)
        

def get_ban_rights(until_date=None):
    """Get ban rights for a user"""
    return ChatBannedRights(
        until_date=until_date,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

def get_unban_rights():
    """Get unban rights for a user"""
    return ChatBannedRights(
        until_date=None,
        view_messages=False,
        send_messages=False,
        send_media=False,
        send_stickers=False,
        send_gifs=False,
        send_games=False,
        send_inline=False,
        embed_links=False,
    )

def is_gbanned(user_id):
    """Check if user is globally banned"""
    gban_list = load_gban_list()
    return str(user_id) in gban_list

# ==================== HELPER FUNCTION ====================
async def check_owner_only(event):
    """Check if the command is used by OWNER_ID only"""
    sender = await event.get_sender()
    if sender.id != OWNER_ID:
        await event.edit("🚫 **ACCESS DENIED**\n\nThis command can only be used by the **BOT OWNER**!")
        return False
    return True

# ==================== AUTO-BAN HANDLER ====================
async def auto_gban_check(event):
    """Automatically ban GBanned users when they join/send messages"""
    # Don't check if event is from private chat
    if not event.is_group and not event.is_channel:
        return
    
    # Don't check if sender is owner
    sender = await event.get_sender()
    if sender.id == OWNER_ID:
        return
    
    # Check if sender is GBanned
    if is_gbanned(sender.id):
        try:
            chat = await event.get_chat()
            
            # Ban the user
            ban_rights = get_ban_rights(until_date=None)
            
            await event.client(EditBannedRequest(
                chat.id,
                sender.id,
                ban_rights
            ))
            
            # Delete the message
            await event.delete()
            
            # Send notification to owner
            try:
                await event.client.send_message(
                    OWNER_ID,
                    f"🚨 **Auto-Banned GBanned User**\n\n"
                    f"👤 User: {sender.first_name or 'Unknown'}\n"
                    f"🆔 ID: `{sender.id}`\n"
                    f"💬 Chat: {chat.title or 'Unknown'}\n"
                    f"🆔 Chat ID: `{chat.id}`"
                )
            except:
                pass
            
            logger.info(f"Auto-banned GBanned user {sender.id} from chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Failed to auto-ban user {sender.id}: {str(e)}")

# Auto-ban handler
@client.on(events.NewMessage())
async def auto_ban_handler(event):
    await auto_gban_check(event)

# ==================== .GBAN COMMAND ====================
@client.on(events.NewMessage(pattern=r'^\.gban(?:\s+(\d+)(?:d|h|m)?)?(?:\s+(.*))?$', outgoing=True))
async def global_ban_command(event):
    """Globally ban a user from all groups (OWNER ONLY)"""
    
    # STRICT OWNER CHECK
    if not await check_owner_only(event):
        return
    
    # Check usage
    if not event.is_reply and not event.pattern_match.group(2):
        await event.edit("""
**🌍 GLOBAL BAN COMMAND (OWNER ONLY)**

**Usage:**
`.gban` - Reply to user (permanent)
`.gban [duration] [reason]` - Reply to user with duration
`.gban [user_id] [duration] [reason]` - Ban by user ID

**⏰ Duration Formats:**
- `7d` = 7 days
- `2h` = 2 hours
- `30m` = 30 minutes
- `permanent` = Permanent ban

**📝 Examples:**
`.gban` - Permanent (reply to user)
`.gban 7d Spamming` - 7 days (reply to user)
`.gban 123456789 30m Flooding` - Ban by ID
        """)
        return
    
    try:
        # Get target user
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            target_user_id = reply_msg.sender_id
            user_entity = await event.client.get_entity(target_user_id)
        else:
            # Parse arguments
            args = event.text.split(maxsplit=3)
            if len(args) < 2:
                await event.edit("`Please provide a user ID!`")
                return
            
            try:
                target_user_id = int(args[1])
                user_entity = await event.client.get_entity(target_user_id)
            except ValueError:
                await event.edit("`Invalid user ID format!`")
                return
            except Exception as e:
                await event.edit(f"`Failed to fetch user: {str(e)}`")
                return
        
        # Prevent banning owner
        if user_entity.id == OWNER_ID:
            await event.edit("🤦‍♂️ **You cannot ban yourself (Owner)!**")
            return
        
        # Get duration and reason
        duration_match = event.pattern_match.group(1)
        reason_match = event.pattern_match.group(2)
        
        # Parse duration
        until_date = None
        duration_text = "Permanent"
        
        if duration_match:
            if 'permanent' in duration_match.lower():
                duration_text = "Permanent"
            else:
                try:
                    # Parse duration like 7d, 2h, 30m
                    duration_str = duration_match
                    if duration_str[-1].isalpha():
                        num = int(duration_str[:-1])
                        unit = duration_str[-1].lower()
                    else:
                        num = int(duration_str)
                        unit = 'd'
                    
                    if unit == 'd':
                        until_date = datetime.now() + timedelta(days=num)
                        duration_text = f"{num} day(s)"
                    elif unit == 'h':
                        until_date = datetime.now() + timedelta(hours=num)
                        duration_text = f"{num} hour(s)"
                    elif unit == 'm':
                        until_date = datetime.now() + timedelta(minutes=num)
                        duration_text = f"{num} minute(s)"
                    
                except:
                    # If duration parsing fails, treat as reason
                    if not reason_match:
                        reason_match = duration_match
                    duration_text = "Permanent"
        
        # Get reason
        reason = reason_match or "No reason provided"
        
        # Load GBan list
        gban_list = load_gban_list()
        
        # Check if already GBanned
        if str(user_entity.id) in gban_list:
            await event.edit(f"⚠️ **User is already globally banned!**\n\nUse `.gunban {user_entity.id}` to remove ban first.")
            return
        
        # Add to GBan list
        gban_list[str(user_entity.id)] = {
            "user_id": user_entity.id,
            "first_name": user_entity.first_name or "",
            "last_name": user_entity.last_name or "",
            "username": user_entity.username or "",
            "banned_by": OWNER_ID,
            "banned_at": datetime.now().isoformat(),
            "until": until_date.isoformat() if until_date else None,
            "duration": duration_text,
            "reason": reason,
            "permanent": until_date is None
        }
        
        save_gban_list(gban_list)
        
        # Start banning process
        processing_msg = await event.edit(f"""
🚫 **INITIATING GLOBAL BAN** 🚫

**👤 Target User:** {user_entity.first_name or 'Unknown'}
**🆔 User ID:** `{user_entity.id}`
**⏰ Duration:** {duration_text}
**📝 Reason:** {reason}
**👑 Banned By:** OWNER

**🔄 Scanning all groups...**
**⏳ Please wait, this may take a minute...**
        """)
        
        # Ban from all groups
        banned_chats = []
        failed_chats = []
        total_checked = 0
        
        async for dialog in event.client.iter_dialogs():
            if dialog.is_group or (dialog.is_channel and not dialog.is_user):
                total_checked += 1
                
                try:
                    # Check if bot is admin
                    chat = await event.client.get_entity(dialog.id)
                    
                    # Get bot's permissions (checking if we can ban)
                    try:
                        me = await event.client.get_me()
                        bot_permissions = await event.client.get_permissions(dialog.id, me.id)
                        
                        if bot_permissions.is_admin or bot_permissions.is_creator:
                            # Ban user
                            ban_rights = get_ban_rights(until_date=until_date)
                            
                            await event.client(EditBannedRequest(
                                dialog.id,
                                user_entity.id,
                                ban_rights
                            ))
                            
                            banned_chats.append(dialog.name or f"ID: {dialog.id}")
                            
                            # Update progress every 10 chats
                            if len(banned_chats) % 10 == 0:
                                await processing_msg.edit(f"""
🚫 **GLOBAL BAN PROGRESS**

**✅ Banned from:** {len(banned_chats)} chats
**❌ Failed:** {len(failed_chats)} chats
**📊 Total checked:** {total_checked} chats

**🔄 Continuing scan...**
                                """)
                            
                            await asyncio.sleep(0.2)  # Avoid flood
                            
                    except Exception as e:
                        failed_chats.append(f"{dialog.name or dialog.id}")
                        
                except Exception:
                    failed_chats.append(f"Chat {dialog.id}")
        
        # Final report
        report_msg = f"""
✅ **GLOBAL BAN COMPLETED SUCCESSFULLY** ✅

**👤 User:** {user_entity.first_name or 'Unknown'}
**🆔 ID:** `{user_entity.id}`
**⏰ Duration:** {duration_text}
**📝 Reason:** {reason}
**📅 Banned On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**📊 STATISTICS:**
├ ✅ **Successfully banned from:** {len(banned_chats)} chats
├ ❌ **Failed to ban from:** {len(failed_chats)} chats
├ 📈 **Total groups checked:** {total_checked}
└ 💾 **Added to GBan database:** Yes

**🔒 AUTO-BAN ENABLED:**
This user will be automatically banned if they join any group where this bot is admin.
        """
        
        await processing_msg.edit(report_msg)
        
        # Log to console
        logger.info(f"[GBAN] User {user_entity.id} globally banned by OWNER. Reason: {reason}")
        
    except Exception as e:
        await event.edit(f"❌ **GLOBAL BAN FAILED**\n\n**Error:** {str(e)}")
        logger.error(f"[GBAN ERROR] {str(e)}")

# ==================== .GUNBAN COMMAND ====================
@client.on(events.NewMessage(pattern=r'^\.gunban(?:\s+(\d+))?$', outgoing=True))
async def global_unban_command(event):
    """Remove global ban from a user (OWNER ONLY)"""
    
    # STRICT OWNER CHECK
    if not await check_owner_only(event):
        return
    
    # Get target user
    target_user_id = None
    
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        target_user_id = reply_msg.sender_id
    elif event.pattern_match.group(1):
        target_user_id = int(event.pattern_match.group(1))
    else:
        await event.edit("""
**🌍 GLOBAL UNBAN COMMAND (OWNER ONLY)**

**Usage:**
`.gunban` - Reply to user
`.gunban [user_id]` - Unban by user ID

**Examples:**
`.gunban` - Reply to user
`.gunban 123456789` - Unban by ID
        """)
        return
    
    try:
        # Load GBan list
        gban_list = load_gban_list()
        
        # Check if user is GBanned
        if str(target_user_id) not in gban_list:
            await event.edit(f"❌ **User `{target_user_id}` is not globally banned!**")
            return
        
        # Get user info from GBan list
        user_info = gban_list[str(target_user_id)]
        
        # Start unbanning process
        processing_msg = await event.edit(f"""
✅ **INITIATING GLOBAL UNBAN** ✅

**👤 User:** {user_info.get('first_name', 'Unknown')}
**🆔 ID:** `{target_user_id}`
**📝 Original Reason:** {user_info.get('reason', 'Unknown')}
**📅 Banned On:** {user_info.get('banned_at', 'Unknown')}

**🔄 Scanning all groups to unban...**
**⏳ Please wait...**
        """)
        
        # Unban from all groups
        unbanned_chats = []
        failed_chats = []
        total_checked = 0
        
        async for dialog in event.client.iter_dialogs():
            if dialog.is_group or (dialog.is_channel and not dialog.is_user):
                total_checked += 1
                
                try:
                    # Check if bot is admin
                    chat = await event.client.get_entity(dialog.id)
                    
                    # Get bot's permissions
                    try:
                        me = await event.client.get_me()
                        bot_permissions = await event.client.get_permissions(dialog.id, me.id)
                        
                        if bot_permissions.is_admin or bot_permissions.is_creator:
                            # Unban user
                            unban_rights = get_unban_rights()
                            
                            await event.client(EditBannedRequest(
                                dialog.id,
                                target_user_id,
                                unban_rights
                            ))
                            
                            unbanned_chats.append(dialog.name or f"ID: {dialog.id}")
                            
                            # Update progress
                            if len(unbanned_chats) % 10 == 0:
                                await processing_msg.edit(f"""
✅ **GLOBAL UNBAN PROGRESS**

**✅ Unbanned from:** {len(unbanned_chats)} chats
**❌ Failed:** {len(failed_chats)} chats
**📊 Total checked:** {total_checked} chats

**🔄 Continuing...**
                                """)
                            
                            await asyncio.sleep(0.2)
                            
                    except Exception:
                        failed_chats.append(f"{dialog.name or dialog.id}")
                        
                except Exception:
                    failed_chats.append(f"Chat {dialog.id}")
        
        # Remove from GBan list
        del gban_list[str(target_user_id)]
        save_gban_list(gban_list)
        
        # Final report
        report_msg = f"""
✅ **GLOBAL UNBAN COMPLETED SUCCESSFULLY** ✅

**👤 User:** {user_info.get('first_name', 'Unknown')}
**🆔 ID:** `{target_user_id}`
**📅 Unbanned On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**📊 STATISTICS:**
├ ✅ **Successfully unbanned from:** {len(unbanned_chats)} chats
├ ❌ **Failed to unban from:** {len(failed_chats)} chats
├ 📈 **Total groups checked:** {total_checked}
└ 🗑️ **Removed from GBan database:** Yes

**🔓 AUTO-BAN DISABLED:**
This user can now join groups freely.
        """
        
        await processing_msg.edit(report_msg)
        
        # Log to console
        logger.info(f"[GUNBAN] User {target_user_id} globally unbanned by OWNER")
        
    except Exception as e:
        await event.edit(f"❌ **GLOBAL UNBAN FAILED**\n\n**Error:** {str(e)}")
        logger.error(f"[GUNBAN ERROR] {str(e)}")

# ==================== .GBANLIST COMMAND ====================
@client.on(events.NewMessage(pattern=r'^\.gbanlist$', outgoing=True))
async def gban_list_command(event):
    """Show list of all globally banned users (OWNER ONLY)"""
    
    # STRICT OWNER CHECK
    if not await check_owner_only(event):
        return
    
    try:
        # Load GBan list
        gban_list = load_gban_list()
        
        if not gban_list:
            await event.edit("📭 **GBan list is empty!**\n\nNo users are globally banned.")
            return
        
        total_banned = len(gban_list)
        
        # Create formatted list
        ban_list_text = f"📋 **GLOBAL BAN LIST** 📋\n\n"
        ban_list_text += f"**Total Banned Users:** {total_banned}\n\n"
        ban_list_text += "─" * 30 + "\n\n"
        
        for idx, (user_id, user_data) in enumerate(gban_list.items(), 1):
            user_name = user_data.get('first_name', 'Unknown')
            username = f"@{user_data.get('username')}" if user_data.get('username') else "No username"
            reason = user_data.get('reason', 'No reason')
            banned_on = user_data.get('banned_at', 'Unknown')
            duration = user_data.get('duration', 'Permanent')
            
            ban_list_text += f"**{idx}. {user_name}**\n"
            ban_list_text += f"   ├ 🆔 ID: `{user_id}`\n"
            ban_list_text += f"   ├ 👤 Username: {username}\n"
            ban_list_text += f"   ├ ⏰ Duration: {duration}\n"
            ban_list_text += f"   ├ 📝 Reason: {reason[:50]}...\n"
            ban_list_text += f"   └ 📅 Banned: {banned_on[:10]}\n\n"
            
            # Limit to 15 users per message
            if idx == 15:
                ban_list_text += f"**... and {total_banned - 15} more users**\n"
                break
        
        ban_list_text += f"\n**Use:** `.gunban [user_id]` to remove ban"
        
        await event.edit(ban_list_text)
        
    except Exception as e:
        await event.edit(f"❌ **Failed to load GBan list:** {str(e)}")
        
from telethon import events
import requests, json

@client.on(events.NewMessage(pattern=r'\.num (\d+)'))
async def number_info(event):
    if event.sender_id != OWNER_ID:
        return
   
    num = event.pattern_match.group(1)
    api = f"https://abbas-number-info.vercel.app/track?num={num}"
    try:
        data = requests.get(api).json()
        await event.reply(f"📱 Number Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'\.vehicle (\S+)'))
async def vehicle_info(event):
    if event.sender_id != OWNER_ID:
        return
  
    vehicle_no = event.pattern_match.group(1)
    api = f"https://vehicle-5-api.vercel.app/vehicle_info?vehicle_no={vehicle_no}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🚗 Vehicle Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'\.aadhar (\d{12})'))
async def aadhar_info(event):
    if event.sender_id != OWNER_ID:
        return
    
    aadhaar = event.pattern_match.group(1)
    api = f"https://rose-x-tool.vercel.app/fetch?key=@Ros3_x&aadhaar={aadhaar}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🪪 Aadhaar Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")
        
@client.on(events.NewMessage(pattern=r'\.pin (\d{6})'))
async def pin_info(event):
    if event.sender_id != OWNER_ID:
        return
    
    pincode = event.pattern_match.group(1)
    api = f"https://pin-code-2-village.vercel.app/?pin={pincode}"
    try:
        data = requests.get(api).json()
        
        # Convert the data to a pretty-printed JSON string[citation:1][citation:6][citation:7]
        json_str = json.dumps(data, indent=2)
        # Split the string into individual lines[citation:3]
        all_lines = json_str.split('\n')
        
        # Get only the last 15 lines
        num_lines_to_show = 15
        if len(all_lines) > num_lines_to_show:
            lines_to_send = all_lines[-num_lines_to_show:]
            message_body = '\n'.join(lines_to_send)
        else:
            # If the JSON has 15 or fewer lines, send all of them
            message_body = json_str
        
        await event.reply(f"📮 Pincode Info:\n```{message_body}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'\.ip (\S+)'))
async def ip_info(event):
    if event.sender_id != OWNER_ID:
        return
    
    ip_address = event.pattern_match.group(1)
    api = f"https://ip-address-api-fawn.vercel.app/ipinfo?ip={ip_address}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🌐 IP Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")
        
@client.on(events.NewMessage(pattern=r'\.vnum (\S+)'))
async def vnum_info(event):
    if event.sender_id != OWNER_ID:
        return
    
    vehicle_no = event.pattern_match.group(1)
    api = f"https://vehicle-to-own-num.vercel.app/vehicle?owner={vehicle_no}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🌐 vehicle Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")
        # ------------------------------
# GOOGLE SEARCH CONFIG
# ------------------------------
GOOGLE_API_KEY = "AIzaSyBPnt16fUVxu78zWOdVmYhiByj-hooPL2U"           
CX_ID = "52a3d9bf39f3b4594"       

# ------------------------------
# SEARCH COMMAND
# ------------------------------
@client.on(events.NewMessage(pattern=r"\.search (.+)"))
async def search_google(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    query = event.pattern_match.group(1)

    search = await event.reply("**🔎 Searching… for results wait…**")
    await asyncio.sleep(0.8)
    await search.delete()

    url = (
        f"https://www.googleapis.com/customsearch/v1?"
        f"key={GOOGLE_API_KEY}&cx={CX_ID}&q={query}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await event.reply("❌ API se sahi response nahi aaya.")
                    return

                data = await resp.json()

    except Exception as e:
        await event.reply(f"⚠️ Error: {str(e)}")
        return

    if "items" not in data:
        await event.reply("**😕 Koi result nahi mila.**")
        return

    results = data["items"][:3]

    msg = f"🔍 **Search results for:** `{query}`\n\n"

    for idx, item in enumerate(results, 1):
        title = item.get("title", "No Title")
        desc = item.get("snippet", "No description available")
        link = item.get("link", "")

        msg += f"**{idx}. {title}**\n📄 {desc}\n🔗 {link}\n\n"

    # Image extract karna
    image_url = None
    try:
        for item in results:
            if "pagemap" in item and "cse_image" in item["pagemap"]:
                image_url = item["pagemap"]["cse_image"][0]["src"]
                break
            elif "pagemap" in item and "cse_thumbnail" in item["pagemap"]:
                image_url = item["pagemap"]["cse_thumbnail"][0]["src"]
                break
    except:
        image_url = None

    # Agar image URL mila hai to image ke sath message send karo
    if image_url:
        try:
            # Option 1: Direct URL se send karo (Telegram khud download karega)
            await event.client.send_file(
                event.chat_id,
                file=image_url,
                caption=msg[:1024] if len(msg) > 1024 else msg,
                reply_to=event.message,
                parse_mode='md'
            )
            
        except Exception as e:
            print(f"Image error: {e}")
            # Option 2: Agar URL se nahi ho pa raha, to download karke send karo
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            # Temporary file mein save karo
                            image_data = await resp.read()
                            
                            # BytesIO use karke
                            from io import BytesIO
                            bio = BytesIO(image_data)
                            bio.name = 'search_result.jpg'
                            
                            await event.client.send_file(
                                event.chat_id,
                                file=bio,
                                caption=msg[:1024] if len(msg) > 1024 else msg,
                                reply_to=event.message,
                                parse_mode='md'
                            )
                        else:
                            await event.reply(msg, parse_mode='md')
            except Exception as e2:
                print(f"Second image error: {e2}")
                await event.reply(msg, parse_mode='md')
    else:
        await event.reply(msg, parse_mode='md')
        
       # List of funny death messages with emojis
death_messages = [
    "🪦 **{username} mar chuka hai!**\n\n💀 User ki aatma ko shanti mile\n☠️ Ashtiyan gutter ke paani mein bah gayi\n⚰️ Ab wo sirf hamari yaadon mein hai",
    "🔫 **{username} ko eliminate kar diya gaya!**\n\n💥 Headshot with facts!\n🩸 Digital blood everywhere!\n🎯 Perfect aim, target neutralized!",
    "☠️ **{username} ka game over ho gaya!**\n\n👻 Ab wo ghost mode mein hain\n💸 Resurrection ke liye 1000₹ ka lagenge\n🪦 RIP in pieces!",
    "💣 **{username} bomb blast mein shaheed!**\n\n💥 KABOOM! Direct hit!\n🔥 Poora system crash ho gaya!\n🪦 Ab coding karne ke liye next life ka intezar karein",
    "⚰️ **{username} ki maut ho gayi!**\n\n🐍 Python ne kaat liya!\n🤖 Bot ne betrayal kar diya!\n💀 User deleted from existence!"
]

# List of funny kidnap messages with emojis
kidnap_messages = [
    "🚗 **{username} ko successfully kidnap kar liya gaya!** 🎭\n\n🔒 Ab yeh mere basement mein locked hain\n💵 Ransom: 10,000 memes\n📞 Contact karein: 1800-KIDNAP\n🕵️‍♂️ Police ko pata bhi nahi chalega!",
    "🎒 **{username} ko bag mein daal kar le gaya!** 👀\n\n🚙 Getaway car ready!\n🗺️ GPS tracking disabled!\n🍕 Hostage ko pizza khilaya jayega!\n⏰ 24 hours mein release honge!",
    "🦹‍♂️ **{username} ko evil villain utha kar le gaya!** 💨\n\n🏰 Secret hideout mein le jaya ja raha hai\n🔐 Super secure vault mein rakhenge\n🎪 Circus mein bech denge!",
    "👻 **{username} ko ghost kidnap kar ke le gaya!** 🌪️\n\n🏚️ Haunted mansion mein le jaya ja raha hai\n📱 Signal lost - tracking impossible!\n🍫 Chocolate ke badle chhod denge!",
    "🚁 **{username} ko helicopter se uthaya gaya!** 🪂\n\n🛩️ Destination: Unknown island\n🏝️ Luxury kidnapping package!\n📸 Instagram worthy kidnapping!"
]

@client.on(events.NewMessage(pattern=r'\.kill'))
async def kill_command(event):
    """Kill command handler - Owner only"""
    # Check if user is owner
    if event.sender_id != OWNER_ID:
        await event.reply("❌ **Ye command use krne ki aukat nhi h mittar 👺👺!** 🚫")
        return
    
    if not event.is_reply:
        await event.reply("❌ **Kill karne ke liye kisi message par reply karein!**")
        return
    
    try:
        replied_msg = await event.get_reply_message()
        user = await client.get_entity(replied_msg.sender_id)
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Select random death message
        death_message = random.choice(death_messages)
        formatted_message = death_message.format(username=username)
        
        # Add some dramatic effects with message editing
        message = await event.reply("🔫 Aiming...")
        await asyncio.sleep(2)
        
        await message.edit("💥 Firing...")
        await asyncio.sleep(2)
        
        await message.edit("🎯 Target hit!")
        await asyncio.sleep(1)
        
        await message.edit(formatted_message)
        
    except Exception as e:
        await event.reply(f"❌ Kill failed! Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'\.kidnap'))
async def kidnap_command(event):
    """Kidnap command handler - Owner only"""
    # Check if user is owner
    if event.sender_id != OWNER_ID:
        await event.reply("❌ **Ye command use krne ki aukat nhi h mittar 👺👺!** 🚫")
        return
    
    if not event.is_reply:
        await event.reply("❌ **Kidnap karne ke liye kisi message par reply karein!**")
        return
    
    try:
        replied_msg = await event.get_reply_message()
        user = await client.get_entity(replied_msg.sender_id)
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Select random kidnap message
        kidnap_message = random.choice(kidnap_messages)
        formatted_message = kidnap_message.format(username=username)
        
        # Add kidnapping drama with message editing
        message = await event.reply("🚗 Getting ready...")
        await asyncio.sleep(2)
        
        await message.edit("🦹‍♂️ Planning the operation...")
        await asyncio.sleep(2)
        
        await message.edit("🎭 Executing kidnapping...")
        await asyncio.sleep(2)
        
        await message.edit("✅ Success! Target captured!")
        await asyncio.sleep(1)
        
        await message.edit(formatted_message)
        
    except Exception as e:
        await event.reply(f"❌ Kidnap failed! Error: {str(e)}")

        
@client.on(events.NewMessage(pattern=r"\.create\s+(.+)"))
async def create_image(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    """Photo send karega, file nahi"""
    try:
        prompt = event.pattern_match.group(1).strip()
        
        if not prompt:
            await event.reply("❌ Usage: `.create <prompt>`")
            return
        
        msg = await event.reply(f"🔄 Creating...")
        
        api_url = f"https://text-to-img.apis-bj-devs.workers.dev/?prompt={requests.utils.quote(prompt)}"
        
        async with aiohttp.ClientSession() as session:
            # JSON response lo
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    await msg.edit(f"❌ API error: {resp.status}")
                    return
                
                data = await resp.json()
                
                if data.get('status') == 'success' and 'result' in data:
                    # Pehli image URL
                    image_url = data['result'][0]
                    
                    # Image download karo
                    async with session.get(image_url) as img_resp:
                        if img_resp.status != 200:
                            await msg.edit("❌ Image download failed")
                            return
                        
                        # IMPORTANT: Temporary file mein save karo
                        import tempfile
                        import os
                        
                        # Temporary file create karo
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                            tmp.write(await img_resp.read())
                            tmp_path = tmp.name
                         
                        try:
                            # Photo as photo send karo (yeh important hai)
                            await event.client.send_file(
                                event.chat_id,
                                tmp_path,  # File path
                                caption=f"**Prompt:** `{prompt}`",
                                reply_to=event.reply_to_msg_id if event.is_reply else None,
                                force_document=False  # ❌ IMPORTANT: file nahi, photo bhejna
                            )
                        finally:
                            # Temporary file delete karo
                            os.unlink(tmp_path)
                        
                        await msg.delete()
                else:
                    await msg.edit(f"❌ Error: {data}")
    
    except Exception as e:
        await event.edit(f"❌ Error: {str(e)}")


# ========== .whois command ==========
@client.on(events.NewMessage(pattern=r'^\.whois(?:\s|$)', func=lambda e: True))
async def whois_command(event):
    if event.sender_id != OWNER_ID:
        return
    await asyncio.sleep(0.6)
    await event.delete()
    """Get user info with emojis and style"""
    try:
        # User identify karein
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            user = await reply_msg.get_sender()
        else:
            # Check if username/id provided
            args = event.text.split(' ', 1)
            if len(args) > 1:
                user_arg = args[1].strip()
                try:
                    if user_arg.isdigit():
                        user = await event.client.get_entity(int(user_arg))
                    else:
                        user_arg = user_arg.replace('@', '')
                        user = await event.client.get_entity(user_arg)
                except:
                    reply = await event.reply("❌ User not found!")
                    await asyncio.sleep(2)
                    await reply.delete()
                    return
            else:
                user = await event.get_sender()
        
        # User details collect karein
        user_id = user.id
        first_name = user.first_name or "N/A"
        last_name = user.last_name or "N/A"
        username = f"@{user.username}" if user.username else "No Username"
        
        # Check if bot
        is_bot = "🤖 Yes" if hasattr(user, 'bot') and user.bot else "👤 No"
        
        # Check scam/fake
        is_scam = "⚠️ Yes" if hasattr(user, 'scam') and user.scam else "✅ No"
        is_fake = "⚠️ Yes" if hasattr(user, 'fake') and user.fake else "✅ No"
        
        # Premium check
        is_premium = "🌟 Yes" if hasattr(user, 'premium') and user.premium else "💫 No"
        
        # DC ID get karein
        dc_id = "N/A"
        dc_location = "Unknown"
        
        if hasattr(user, 'photo') and user.photo:
            # Photo se DC nikaalein
            dc_id = getattr(user.photo, 'dc_id', "N/A")
            
            # DC location identify karein
            dc_locations = {
                1: "🇺🇸 North America (Miami)",
                2: "🇳🇱 Europe (Amsterdam)",
                3: "🇸🇬 Asia (Singapore)",
                4: "🇦🇪 Middle East (Dubai)",
                5: "🇸🇬 Singapore 2"
            }
            dc_location = dc_locations.get(dc_id, f"DC {dc_id}")
        
        # Last seen time
        last_seen = "🕒 Recently"
        if hasattr(user, 'status'):
            if hasattr(user.status, 'was_online'):
                last_seen = f"🕒 {user.status.was_online.strftime('%Y-%m-%d %H:%M')}"
            elif user.status == 'UserStatusOnline':
                last_seen = "🟢 Online Now"
            elif user.status == 'UserStatusOffline':
                last_seen = "⚫ Offline"
            elif user.status == 'UserStatusRecently':
                last_seen = "🟡 Recently"
            elif user.status == 'UserStatusLastWeek':
                last_seen = "🟠 Last Week"
            elif user.status == 'UserStatusLastMonth':
                last_seen = "🔴 Last Month"
        
        # Stylish response banayein
        whois_text = f"""
🔍 **━━━【 USER INFO 】━━━🔍**

👤 **Name:** {first_name} {last_name}
🆔 **ID:** `{user_id}`
📛 **Username:** {username}
🤖 **Bot:** {is_bot}
🌟 **Premium:** {is_premium}

📡 **━━━【 STATUS 】━━━📡**
⏰ **Last Seen:** {last_seen}

🛡️ **━━━【 VERIFICATION 】━━━🛡️**
⚠️ **Scam:** {is_scam}
🎭 **Fake:** {is_fake}

🌐 **━━━【 DATA CENTER 】━━━🌐**
🖥️ **DC ID:** {dc_id}
📍 **Location:** {dc_location}

✨ **━━━【 END 】━━━✨**
        """
        
        # Photo ke saath send karein agar available ho
        try:
            # Method 1: Direct photo object use karein
            try:
                photos = await event.client.get_profile_photos(user, limit=1)
                if photos and len(photos) > 0:
                    await event.client.send_file(
                        event.chat_id,
                        photos[0],  # Direct photo object
                        caption=whois_text,
                        force_document=False  # YEH IMPORTANT HAI - Document nahi, photo send karega
                    )
                    return
            except:
                pass
            
            # Method 2: Download karke send karein
            try:
                photo_path = await event.client.download_profile_photo(user)
                
                if photo_path and os.path.exists(photo_path):
                    await event.client.send_file(
                        event.chat_id,
                        photo_path,
                        caption=whois_text,
                        force_document=False  # YEH IMPORTANT HAI
                    )
                    # Temporary file delete karein
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                    return
            except:
                pass
            
            # Agar photo nahi mila toh sirf text
            await event.reply(whois_text)
            
        except Exception as photo_error:
            # Photo download fail ho toh sirf text
            print(f"Photo error: {photo_error}")
            await event.reply(whois_text)
            
    except Exception as e:
        print(f"Whois error: {e}")
        reply = await event.reply(f"❌ Error getting user info: {str(e)}")
        await asyncio.sleep(2)
        await reply.delete()

# ========== DC ONLY COMMAND ==========
@client.on(events.NewMessage(pattern=r'^\.dc(?:\s|$)', func=lambda e: True))
async def dc_command(event):
    """Get only DC info of user"""
    try:
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            user = await reply_msg.get_sender()
        else:
            user = await event.get_sender()
        
        dc_id = "N/A"
        dc_info = "Unknown"
        
        if hasattr(user, 'photo') and user.photo:
            dc_id = getattr(user.photo, 'dc_id', "N/A")
            
            # DC details
            dc_details = {
                1: "**DC 1** - North America (Miami, USA)",
                2: "**DC 2** - Europe (Amsterdam, Netherlands)",
                3: "**DC 3** - Asia (Singapore)",
                4: "**DC 4** - Middle East (Dubai, UAE)",
                5: "**DC 5** - Singapore (Backup)"
            }
            
            dc_info = dc_details.get(dc_id, f"**DC {dc_id}** - Unknown Location")
        
        # DC map emoji
        dc_emoji = {
            1: "🇺🇸",
            2: "🇳🇱", 
            3: "🇸🇬",
            4: "🇦🇪",
            5: "🇸🇬"
        }.get(dc_id, "🌐")
        
        response = f"""
{dc_emoji} **DATA CENTER INFO** {dc_emoji}

👤 **User:** {user.first_name or 'N/A'}
🆔 **User ID:** `{user.id}`

🖥️ **DC ID:** `{dc_id}`
📍 **Location Details:**
{dc_info}

📡 *DC = Data Center (Telegram Server Location)*
        """
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ========== SIMPLE WHOIS WITH BETTER DC INFO ==========
@client.on(events.NewMessage(pattern='^[.]info$'))
async def simple_info(event):
    """Simple user info command"""
    try:
        if event.is_reply:
            reply = await event.get_reply_message()
            user = await reply.get_sender()
        else:
            user = await event.get_sender()
        
        # Basic info
        info_text = f"""
📱 **User Information**

**Name:** {user.first_name or ''} {user.last_name or ''}
**ID:** `{user.id}`
**Username:** @{user.username if user.username else 'No username'}
**Bot:** {'✅ Yes' if user.bot else '❌ No'}
**Verified:** {'✅ Yes' if user.verified else '❌ No'}
**Scam:** {'⚠️ Yes' if user.scam else '✅ No'}
**Fake:** {'⚠️ Yes' if user.fake else '✅ No'}
**Premium:** {'🌟 Yes' if hasattr(user, 'premium') and user.premium else '💫 No'}
        """
        
        # Try to get DC from photo
        if hasattr(user, 'photo') and user.photo:
            dc_id = user.photo.dc_id
            dc_map = {
                1: "🇺🇸 USA (Miami)",
                2: "🇳🇱 Netherlands (Amsterdam)", 
                3: "🇸🇬 Singapore",
                4: "🇦🇪 UAE (Dubai)",
                5: "🇸🇬 Singapore 2"
            }
            dc_text = dc_map.get(dc_id, f"DC {dc_id}")
            info_text += f"\n**Data Center:** {dc_text}"
        
        await event.reply(info_text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import os
import asyncio

# ========== Auto save view-once media ==========
@client.on(events.NewMessage())
async def auto_save_view_once(event):
    """Automatically save view-once media to saved messages"""
    
    try:
        # Check if message has media
        if not event.message.media:
            return
            
        # Check if it's a view-once message
        if hasattr(event.message, 'media') and event.message.media:
            media = event.message.media
            
            # Check for view-once photo
            if hasattr(media, 'ttl_seconds') and media.ttl_seconds and media.ttl_seconds > 0:
                # Get sender info
                sender = await event.get_sender()
                sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                sender_username = f"@{sender.username}" if sender.username else "No username"
                sender_id = sender.id
                
                # Get chat info
                chat = await event.get_chat()
                chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
                chat_id = chat.id
                
                # Download the media
                try:
                    # Create caption with sender info
                    caption = (
                        f"📸 **Auto-saved View-Once Media**\n\n"
                        f"👤 **Sender:** {sender_name}\n"
                        f"📱 **Username:** {sender_username}\n"
                        f"🆔 **User ID:** `{sender_id}`\n"
                        f"💬 **Chat:** {chat_title}\n"
                        f"🔢 **Chat ID:** `{chat_id}`\n"
                        f"📅 **Date:** {event.message.date}\n"
                        f"⏱️ **TTL:** {media.ttl_seconds} seconds"
                    )
                    
                    # Download the media
                    file_path = await event.message.download_media()
                    
                    # Send to saved messages
                    if file_path:
                        await client.send_file(
                            'me',  # Send to saved messages
                            file_path,
                            caption=caption
                        )
                        
                        # Delete the downloaded file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            
                        # Optional: Send confirmation in chat (uncomment if needed)
                        # await event.reply("✅ View-once media saved to Saved Messages!")
                        
                except Exception as download_error:
                    print(f"Download error: {download_error}")
                    
    except Exception as e:
        print(f"Auto-save error: {e}")


# ========== .save command (for manual save) ==========
@client.on(events.NewMessage(pattern=r'^\.save(?:\s|$)', func=lambda e: True))
async def save_command(event):
    """Save view-once media (manual command)"""
    if not event.is_reply:
        await event.reply("❌ Reply to a view-once photo/video to save it!")
        return
    
    try:
        reply_msg = await event.get_reply_message()
        
        # Check if replied message has media with TTL
        if not (reply_msg.media and hasattr(reply_msg.media, 'ttl_seconds') 
                and reply_msg.media.ttl_seconds and reply_msg.media.ttl_seconds > 0):
            await event.reply("❌ No view-once media found!")
            return
        
        # Get sender info
        sender = await reply_msg.get_sender()
        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        sender_username = f"@{sender.username}" if sender.username else "No username"
        sender_id = sender.id
        
        # Get chat info
        chat = await event.get_chat()
        chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
        chat_id = chat.id
        
        # Download the media
        await event.reply("⏳ Downloading view-once media...")
        
        file_path = await reply_msg.download_media()
        
        if file_path:
            # Create caption
            caption = (
                f"📸 **View-Once Media Saved**\n\n"
                f"👤 **Sender:** {sender_name}\n"
                f"📱 **Username:** {sender_username}\n"
                f"🆔 **User ID:** `{sender_id}`\n"
                f"💬 **Chat:** {chat_title}\n"
                f"🔢 **Chat ID:** `{chat_id}`\n"
                f"📅 **Date:** {reply_msg.date}\n"
                f"⏱️ **TTL:** {reply_msg.media.ttl_seconds} seconds\n"
                f"🔧 **Saved via:** `.save` command"
            )
            
            # Send to saved messages
            await client.send_file(
                'me',
                file_path,
                caption=caption
            )
            
            # Delete the downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            await event.reply("✅ View-once media saved to Saved Messages!")
        else:
            await event.reply("❌ Failed to download media!")
            
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ========== .zombie command ==========
@client.on(events.NewMessage(pattern=r'^\.zombie(?:\s|$)', func=lambda e: e.is_group))
async def zombie_command(event):
    """Remove all deleted accounts from group"""
    try:
        # Admin check karein
        user_perms = await event.client.get_permissions(event.chat_id, event.sender_id)
        if not (user_perms.is_admin or user_perms.is_creator):
            await event.edit("❌ You need to be admin to use this command!")
            return
        
        await event.edit("🧟 **Scanning for deleted accounts...**")
        
        deleted_users = []
        
        # All participants collect karein
        participants = await event.client.get_participants(event.chat_id)
        
        for user in participants:
            if user.deleted:
                deleted_users.append(user.id)
        
        if not deleted_users:
            await event.edit("✅ **No deleted accounts found!** Clean as a whistle! 🎉")
            return
        
        # Confirmation ke liye
        confirm_msg = await event.reply(
            f"⚠️ **Found {len(deleted_users)} deleted accounts!**\n"
            f"Type `.yes` to remove them or `.no` to cancel."
        )
        
        # Confirmation wait karein
        try:
            # Define a conversation handler
            @client.on(events.NewMessage(pattern=r'^\.(yes|no)$', chats=event.chat_id, from_users=event.sender_id))
            async def confirm_handler(confirm_event):
                await delete_command_message(event)
                nonlocal confirm_msg
                
                if confirm_event.text == '.yes':
                    await confirm_msg.reply("🗑️ **Removing deleted accounts...**")
                    removed_count = 0
                    
                    for user_id in deleted_users:
                        try:
                            await event.client.edit_permissions(
                                event.chat_id,
                                user_id,
                                view_messages=False
                            )
                            removed_count += 1
                            await asyncio.sleep(0.5)  # Flood avoid
                        except:
                            continue
                    
                    await event.reply(f"✅ **Cleaned {removed_count} deleted accounts!** 🧹")
                    
                elif confirm_event.text == '.no':
                    await confirm_msg.edit("❌ **Operation cancelled!**")
                
                # Handler remove karein
                client.remove_event_handler(confirm_handler)
            
            # 30 seconds wait
            await asyncio.sleep(30)
            
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
            
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ========== Helper Functions ==========
import html

async def is_admin(chat_id, user_id):
    """Check if user is admin"""
    try:
        perms = await client.get_permissions(chat_id, user_id)
        return perms.is_admin or perms.is_creator
    except:
        return False

        
    #admins
@client.on(events.NewMessage(pattern=r"\.adminlist$"))
async def adminlist_handler(event):
    if not event.is_group:
        return await event.edit("❌ 𝙔𝙚 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 𝙨𝙞𝙧𝙛 𝙜𝙧𝙤𝙪𝙥𝙨 𝙢𝙚 𝙠𝙖𝙖𝙢 𝙠𝙖𝙧𝙩𝙞 𝙝𝙖𝙞")

    admins = await client(GetParticipantsRequest(
        channel=event.chat_id,
        filter=ChannelParticipantsAdmins(),
        offset=0,
        limit=100,
        hash=0
    ))

    text = (
        "👑 **𝘼𝘿𝙈𝙄𝙉** 👑\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for i, user in enumerate(admins.users, start=1):
        name = user.first_name or "Admin"

        if user.username:
            mention = f"@{user.username}"
        else:
            mention = f"[{name}](tg://user?id={user.id})"

        text += f"🔹 **{i}. {mention}**\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "⚡ 𝙋𝙤𝙬𝙚𝙧𝙚𝙙 𝙗𝙮 𝙐𝙨𝙚𝙧𝙗𝙤𝙩 ⚡"

    await event.reply(text, link_preview=False)
    
# Target bot
INFO_BOT = "@funstate00_bot"

@client.on(events.NewMessage(pattern=r'\.data'))
async def data_command(event):
    """Send only user ID to bot"""
    try:
        # Delete command message
        await event.delete()
    except:
        pass
    
    # Check if replying to a user
    if not event.is_reply:
        await event.respond("❌ **Please reply to a user's message**")
        return
    
    # Get the replied message
    reply_msg = await event.get_reply_message()
    user_id = reply_msg.sender_id
    
    try:
        # Get user info
        user = await client.get_entity(user_id)
        
        # Send status
        status_msg = await event.respond(f"🔄 **Fetching Information About User...**")
        
        # Send ONLY user ID to the bot (no command)
        await client.send_message(INFO_BOT, f"{user_id}")
        
        # Wait for bot response
        await asyncio.sleep(2)
        
        # Get bot's response
        bot_response = None
        async for message in client.iter_messages(INFO_BOT, limit=5):
            if message.sender_id != event.sender_id and message.text:
                bot_response = message.text
                break
        
        if bot_response:
            # Send bot's response to chat
            await event.respond(f"🤖 **Information Found:**\n\n{bot_response}")
            await status_msg.delete()
        else:
            await status_msg.edit(f"✅ **User ID sent to bot**\n👤 **User:** {user.first_name or ''}\n🆔 **ID:** `{user_id}`\n❌ **No response yet**")
        
    except Exception as e:
        await event.respond(f"❌ **Error:** {str(e)}")

# Sangmata bots
SANGMATA_BOTS = [
    '@SangMata_BOT'
]

@client.on(events.NewMessage(pattern=r'\.history'))
async def history_command(event):
    if event.sender_id != OWNER_ID:
        return
    
    # Delete command message immediately
    try:
        await event.delete()
    except:
        pass
    
    # Get user quickly
    user_obj = None
    if event.is_reply:
        reply = await event.get_reply_message()
        user_obj = await event.client.get_entity(reply.sender_id)
    else:
        args = event.message.message.split()
        if len(args) > 1:
            try:
                user_obj = await event.client.get_entity(args[1])
            except:
                await event.respond("Reply to user or provide username.")
                return
        else:
            await event.respond(".history [reply/username]")
            return
    
    if not user_obj:
        return
    
    user_id = user_obj.id
    
    # Send initial response fast
    progress_msg = await event.respond("🔍 Fetching history...")
    
    # Function to query a single bot
    async def query_bot(bot_username):
        try:
            async with event.client.conversation(bot_username, timeout=8) as conv:
                await conv.send_message(f"/history {user_id}")
                response = await conv.get_response(timeout=10)
                
                if response and response.text:
                    return response.text
                    
        except asyncio.TimeoutError:
            return "timeout"
        except FloodWaitError as e:
            return f"flood_wait:{e.seconds}"
        except Exception:
            return "error"
        return None
    
    # Query all bots in parallel
    tasks = [query_bot(bot) for bot in SANGMATA_BOTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if result and isinstance(result, str):
            if result in ["timeout", "error"] or result.startswith("flood_wait:"):
                continue
            elif result and ("History for" in result or "Names" in result):
                # Found valid response
                await progress_msg.delete()
                
                # Format the response in beautiful box
                formatted_result = format_history_box(result, user_id)
                
                # Wrap in code block
                final_output = f"```\n{formatted_result}\n```"
                
                # Handle long messages
                if len(final_output) > 4096:
                    parts = []
                    current_part = ""
                    
                    for line in formatted_result.split('\n'):
                        if len(current_part) + len(line) + 1 < 4000:
                            current_part += line + '\n'
                        else:
                            parts.append(f"```\n{current_part}\n```")
                            current_part = line + '\n'
                    
                    if current_part:
                        parts.append(f"```\n{current_part}\n```")
                    
                    await event.respond(parts[0])
                    
                    for part in parts[1:]:
                        await asyncio.sleep(1)
                        await event.respond(part)
                else:
                    await event.respond(final_output)
                
                return
    
    # If no results
    await progress_msg.edit("❌ History Not Found 🚫😭")


def format_history_box(text, user_id):
    """Format Sangmata response in beautiful box with emojis"""
    lines = text.split('\n')
    
    formatted = "╭━━━━⟬ Account History ⟭━━━━╮\n"
    formatted += "┃\n"
    formatted += f"┃ ⟡➣ Target ID - {user_id}\n"
    formatted += "┃\n"
    
    current_section = None
    names_found = False
    usernames_found = False
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        if not line:
            continue
        
        # Skip the main header
        if "History for" in line:
            continue
        
        # Check for Names section (case insensitive)
        if line.lower() == "names" or line.lower().startswith("names"):
            if not names_found:
                formatted += "┃ 📝 Names\n"
                formatted += "┃\n"
                current_section = "names"
                names_found = True
            continue
        
        # Check for Usernames section
        elif line.lower() == "usernames" or line.lower().startswith("usernames"):
            if not usernames_found:
                if names_found:
                    formatted += "┃\n"
                formatted += "┃ 🧾 Usernames\n"
                formatted += "┃\n"
                current_section = "usernames"
                usernames_found = True
            continue
        
        # Process numbered entries (e.g., "1. [07/04/26 18:33:10] .")
        if line and line[0].isdigit():
            # Extract the content after the number and dot
            parts = line.split('. ', 1)
            if len(parts) > 1:
                content = parts[1].strip()
                
                # Remove the date part and keep only the actual name/username
                # Format: "[07/04/26 18:33:10] ." or "[07/04/26 18:33:10] username"
                import re
                # Remove date pattern [DD/MM/YY HH:MM:SS]
                clean_content = re.sub(r'\[.*?\]\s*', '', content)
                
                # If content is just "." or empty, show as "(empty)"
                if not clean_content or clean_content == '.':
                    clean_content = "(empty)"
                
                # Add to formatted output
                if current_section == "names":
                    formatted += f"┃ ⟡➣ {clean_content}\n"
                elif current_section == "usernames":
                    formatted += f"┃ ⟡➣ {clean_content}\n"
    
    # If no sections found, show raw response
    if not names_found and not usernames_found:
        formatted += "┃ Raw Response:\n"
        formatted += "┃\n"
        for line in lines:
            line = line.strip()
            if line and "History for" not in line:
                # Limit line length
                if len(line) > 60:
                    line = line[:57] + "..."
                formatted += f"┃ {line}\n"
    
    # Ensure proper spacing before footer
    if formatted.endswith('\n'):
        formatted += "┃\n"
    else:
        formatted += "\n┃\n"
    
    # Add footer
    formatted += "╰━━━━━━━━━━━━━━━━━━━━━━╯"
    
    return formatted

#weather

API_KEY = "33abfb8d949296ba419c8e342afded3f"

@client.on(events.NewMessage(pattern=r"\.weather (.+)"))
async def weather_handler(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    city = event.pattern_match.group(1)

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    r = requests.get(url).json()

    if r.get("cod") != 200:
        return await event.reply("City not found sir 🚫.")

    temp = r["main"]["temp"]
    feels = r["main"]["feels_like"]
    desc = r["weather"][0]["description"]

    await event.reply(
        f"🌤 Weather: {city}\n"
        f"🌡 Temp: {temp}°C\n"
        f"🤒 Feels like: {feels}°C\n"
        f"📝 Condition: {desc}"
    )

# Store old profile photos (file path)
PFP_HISTORY = {}

@client.on(events.NewMessage(pattern=r'^\.cp$', outgoing=True))
async def change_pfp_cmd(event):
    """Change profile picture from replied photo"""
    reply = await event.get_reply_message()
    
    if not reply or not reply.photo:
        await event.edit("❌ **Please reply to a photo!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    processing = await event.edit("🔄 **Changing profile picture...**")
    
    try:
        # Download the photo
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            temp_path = tmp.name
        
        await reply.download_media(file=temp_path)
        
        # Save current PFP path for restore
        current_photos = await client.get_profile_photos('me')
        if current_photos:
            # Download current PFP
            old_pfp_path = f"old_pfp_{event.sender_id}.jpg"
            await client.download_media(current_photos[0], file=old_pfp_path)
            PFP_HISTORY[event.sender_id] = old_pfp_path
        
        # Upload new profile photo
        file = await client.upload_file(temp_path)
        await client(UploadProfilePhotoRequest(file=file))
        
        await processing.edit("✅ **Profile picture changed successfully!**")
        
        # Clean up temp file
        os.unlink(temp_path)
        
    except Exception as e:
        await processing.edit(f"❌ **Error:** `{str(e)}`")
    
    await asyncio.sleep(3)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^\.bio(?:\s+(.+))?', outgoing=True))
async def change_bio_cmd(event):
    """Change profile bio"""
    new_bio = event.pattern_match.group(1)
    
    if not new_bio:
        # Show current bio
        me = await client.get_me()
        current_bio = me.about or "No bio set"
        await event.edit(f"📝 **Current Bio:**\n`{current_bio}`")
        await asyncio.sleep(5)
        await event.delete()
        return
    
    processing = await event.edit("🔄 **Updating bio...**")
    
    try:
        await client(UpdateProfileRequest(
            about=new_bio
        ))
        
        await processing.edit(f"✅ **Bio updated successfully!**\n\n**New Bio:** `{new_bio}`")
        
    except Exception as e:
        await processing.edit(f"❌ **Error:** `{str(e)}`")
    
    await asyncio.sleep(5)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^\.rcp$', outgoing=True))
async def restore_pfp_cmd(event):
    """Restore previous profile picture"""
    
    if event.sender_id not in PFP_HISTORY:
        await event.edit("❌ **No previous profile picture found!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    processing = await event.edit("🔄 **Restoring previous profile picture...**")
    
    try:
        old_pfp_path = PFP_HISTORY[event.sender_id]
        
        if not os.path.exists(old_pfp_path):
            await processing.edit("❌ **Previous profile picture file not found!**")
            return
        
        # Upload and set old photo
        file = await client.upload_file(old_pfp_path)
        await client(UploadProfilePhotoRequest(file=file))
        
        # Clean up
        os.unlink(old_pfp_path)
        del PFP_HISTORY[event.sender_id]
        
        await processing.edit("✅ **Previous profile picture restored!**")
        
    except Exception as e:
        await processing.edit(f"❌ **Error:** `{str(e)}`")
    
    await asyncio.sleep(3)
    await event.delete()
    
@client.on(events.NewMessage(pattern=r"\.dp$"))
async def dp_handler(event):
    if event.sender_id != OWNER_ID:
        return
    await delete_command_message(event)
    reply = await event.get_reply_message()

    if reply:
        target = reply.sender
    else:
        target = event.chat

    try:
        photo = await client.get_profile_photos(target, limit=1)
        if not photo:
            return await event.reply("bhadwe ne dp nahi lagai 👺👺.")

        await client.send_file(
            event.chat_id,
            photo[0]
        )
    except Exception:
        await event.reply("DP fetch karne me error aaya.")
        
@client.on(events.NewMessage(pattern=r'^\.qr(?: |$)([\s\S]*)$'))
async def qr_generator(event):
    """Generate Colorful QR Code from text/URL"""
    input_text = event.pattern_match.group(1).strip()
    
    if not input_text:
        await event.reply("❌ **Usage:** `.qr <text or URL>`\nExample: `.qr https://github.com`")
        return
    
    try:
        # Attractive color combinations
        colors = [
    ("#0F2027", "#203A43"),  # Dark Blue → Steel Blue (clean & pro)
    ("#141E30", "#243B55"),  # Midnight Blue → Slate
    ("#232526", "#414345"),  # Charcoal → Soft Gray (minimal)
    ("#1A2980", "#26D0CE"),  # Deep Blue → Aqua (balanced)
    ("#2C3E50", "#4CA2AF"),  # Navy → Muted Cyan
    ("#3A1C71", "#D76D77"),  # Royal Purple → Soft Rose
    ("#0B486B", "#F56217"),  # Dark Blue → Orange (high contrast but classy)
    ("#1F4037", "#99F2C8"),  # Forest Green → Mint
]

        
        fill_color, bg_color = random.choice(colors)
        
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=15,
            border=4,
        )
        qr.add_data(input_text)
        qr.make(fit=True)
        
        # Create image with colors
        img = qr.make_image(fill_color=fill_color, back_color=bg_color)
        
        # Convert to RGB
        img = img.convert("RGB")
        
        # Save to bytes as JPG (not PNG)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)  # JPEG format with 95% quality
        buf.seek(0)
        buf.name = 'qr_code.jpg'  # JPG filename
        
        # Send as photo
        await event.client.send_message(
            event.chat_id,
            f"**🎨 QR Code Generated!**",
            file=buf,
            reply_to=event.id,
            parse_mode='md'
        )
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")


# Cat Animation (Edit same message)
@client.on(events.NewMessage(pattern='.cat'))
async def cat_cmd(event):
    msg = event.message
    await msg.edit("┈┈┏━╮╭━┓┈╭━━━━╮")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯
┈╭━┻╮╲┗━━━━╮╭╮┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯
┈╭━┻╮╲┗━━━━╮╭╮┈
┈┃▎▎┃╲╲╲╲╲╲┣━╯┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯
┈╭━┻╮╲┗━━━━╮╭╮┈
┈┃▎▎┃╲╲╲╲╲╲┣━╯┈
┈╰━┳┻▅╯╲╲╲╲┃┈┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯
┈╭━┻╮╲┗━━━━╮╭╮┈
┈┃▎▎┃╲╲╲╲╲╲┣━╯┈
┈╰━┳┻▅╯╲╲╲╲┃┈┈┈
┈┈┈╰━┳┓┏┳┓┏╯┈┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈┏━╮╭━┓┈╭━━━━╮
┈┈┃┏┗┛┓┃╭┫cat ┃
┈┈╰┓▋▋┏╯╯╰━━━━╯
┈╭━┻╮╲┗━━━━╮╭╮┈
┈┃▎▎┃╲╲╲╲╲╲┣━╯┈
┈╰━┳┻▅╯╲╲╲╲┃┈┈┈
┈┈┈╰━┳┓┏┳┓┏╯┈┈┈
┈┈┈┈┈┗┻┛┗┻┛┈┈┈┈""")

# Girlfriend Animation
@client.on(events.NewMessage(pattern='.gf'))
async def gf_cmd(event):
    msg = event.message
    await msg.edit("_/﹋\_")
    await asyncio.sleep(0.2)
    await msg.edit("""_/﹋\_
(҂_´)""")
    await asyncio.sleep(0.2)
    await msg.edit("""_/﹋\_
(҂_´)
<,︻╦╤─ ҉""")
    await asyncio.sleep(0.2)
    await msg.edit("""_/﹋\_
(҂_´)
<,︻╦╤─ ҉
_/﹋\_""")
    await asyncio.sleep(0.2)
    await msg.edit("""_/﹋\_
(҂_´)
<,︻╦╤─ ҉
_/﹋\_
**Do you want to be my girlfriend??!**""")

# Helicopter Animation
@client.on(events.NewMessage(pattern='.helicopter'))
async def helicopter_cmd(event):
    msg = event.message
    await msg.edit("▬▬▬.◙.▬▬▬")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══ 
╬═╬""")
    await asyncio.sleep(0.2)
    for i in range(7):
        text = f"""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══"""
        for j in range(i+1):
            text += f"\n╬═╬"
        await msg.edit(text)
        await asyncio.sleep(0.2)
    
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ Hello Everyone :)""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ Hello Everyone :) 
╬═╬☻/""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ Hello Everyone :) 
╬═╬☻/ 
╬═╬/▌""")
    await asyncio.sleep(0.2)
    await msg.edit("""▬▬▬.◙.▬▬▬ 
═▂▄▄▓▄▄▂ 
◢◤ █▀▀████▄▄▄▄◢◤ 
█▄ █ █▄ ███▀▀▀▀▀▀▀╬ 
◥█████◤ 
══╩══╩══ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ 
╬═╬ Hello Everyone :) 
╬═╬☻/ 
╬═╬/▌ 
╬═╬/ \\""")

# Tank Animation
@client.on(events.NewMessage(pattern='.tank'))
async def tank_cmd(event):
    msg = event.message
    await msg.edit("█۞███████]▄▄▄▄▄▄▄▄▄▄▃")
    await asyncio.sleep(0.2)
    await msg.edit("""█۞███████]▄▄▄▄▄▄▄▄▄▄▃ 
▂▄▅█████████▅▄▃▂…""")
    await asyncio.sleep(0.2)
    await msg.edit("""█۞███████]▄▄▄▄▄▄▄▄▄▄▃ 
▂▄▅█████████▅▄▃▂…
[███████████████████]""")
    await asyncio.sleep(0.2)
    await msg.edit("""█۞███████]▄▄▄▄▄▄▄▄▄▄▃ 
▂▄▅█████████▅▄▃▂…
[███████████████████]
◥⊙▲⊙▲⊙▲⊙▲⊙▲⊙▲⊙◤""")

# Run Animation
@client.on(events.NewMessage(pattern='.run'))
async def run_cmd(event):
    msg = event.message
    await msg.edit("────██──────▀▀▀██")
    await asyncio.sleep(0.2)
    await msg.edit("""────██──────▀▀▀██
──▄▀█▄▄▄─────▄▀█▄▄▄""")
    await asyncio.sleep(0.2)
    await msg.edit("""────██──────▀▀▀██
──▄▀█▄▄▄─────▄▀█▄▄▄
▄▀──█▄▄──────█─█▄▄""")
    await asyncio.sleep(0.2)
    await msg.edit("""────██──────▀▀▀██
──▄▀█▄▄▄─────▄▀█▄▄▄
▄▀──█▄▄──────█─█▄▄
─▄▄▄▀──▀▄───▄▄▄▀──▀▄""")
    await asyncio.sleep(0.2)
    await msg.edit("""────██──────▀▀▀██
──▄▀█▄▄▄─────▄▀█▄▄▄
▄▀──█▄▄──────█─█▄▄
─▄▄▄▀──▀▄───▄▄▄▀──▀▄
─▀───────▀▀─▀───────▀▀""")
    await asyncio.sleep(0.2)
    await msg.edit("""────██──────▀▀▀██
──▄▀█▄▄▄─────▄▀█▄▄▄
▄▀──█▄▄──────█─█▄▄
─▄▄▄▀──▀▄───▄▄▄▀──▀▄
─▀───────▀▀─▀───────▀▀
Awkwokwokwok..""")

# Nikal Animation
@client.on(events.NewMessage(pattern='.nikal'))
async def nikal_cmd(event):
    msg = event.message
    await msg.edit("⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼
⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀   ⠘⠤⣄⣠⠞⠀""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼
⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀   ⠘⠤⣄⣠⠞⠀
⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼
⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀   ⠘⠤⣄⣠⠞⠀
⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣤⣴⣿⣏⠁⠀⠀⠸⣏⢯⣷⣖⣦⡀⠀⠀⠀⠀⠀⠀""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼
⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀   ⠘⠤⣄⣠⠞⠀
⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣤⣴⣿⣏⠁⠀⠀⠸⣏⢯⣷⣖⣦⡀⠀⠀⠀⠀⠀⠀
⢀⣾⣽⣿⣿⣿⣿⠛⢲⣶⣾⢉⡷⣿⣿⠵⣿⠀⠀⠀⠀⠀⠀""")
    await asyncio.sleep(0.2)
    await msg.edit("""⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀
 ⠀⣴⠿⠏⠀⠀⠀⠀⠀  ⠀⢳⡀⠀⡏⠀⠀    ⠀⢷
⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀  ⠀     ⡇
⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿  ⣸ Nikal   ⡇
 ⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀   ⣿  ⢹⠀        ⡇
  ⠙⢿⣯⠄⠀⠀lodu⠀⠀⡿ ⠀⡇⠀⠀⠀⠀    ⡼
⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀   ⠘⠤⣄⣠⠞⠀
⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣤⣴⣿⣏⠁⠀⠀⠸⣏⢯⣷⣖⣦⡀⠀⠀⠀⠀⠀⠀
⢀⣾⣽⣿⣿⣿⣿⠛⢲⣶⣾⢉⡷⣿⣿⠵⣿⠀⠀⠀⠀⠀⠀
⣼⣿⠍⠉⣿⡭⠉⠙⢺⣇⣼⡏⠀⠀ ⠀⣄⢸⠀⠀⠀⠀⠀⠀""")

# Good Morning Animation
@client.on(events.NewMessage(pattern='.gmm'))
async def gm_cmd(event):
    msg = event.message
    await msg.edit("｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮
╭━┳━┳━┳╯┃╭━━┳━┳┳┳━┳╋╋━┳┳━╮""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮
╭━┳━┳━┳╯┃╭━━┳━┳┳┳━┳╋╋━┳┳━╮
┃╋┃╋┃╋┃╋┃┃┃┃┃╋┃╭┫┃┃┃┃┃┃┃╋┃""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮
╭━┳━┳━┳╯┃╭━━┳━┳┳┳━┳╋╋━┳┳━╮
┃╋┃╋┃╋┃╋┃┃┃┃┃╋┃╭┫┃┃┃┃┃┃┃╋┃
┣╮┣━┻━┻━╯╰┻┻┻━┻╯╰┻━┻┻┻━╋╮┃""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮
╭━┳━┳━┳╯┃╭━━┳━┳┳┳━┳╋╋━┳┳━╮
┃╋┃╋┃╋┃╋┃┃┃┃┃╋┃╭┫┃┃┃┃┃┃┃╋┃
┣╮┣━┻━┻━╯╰┻┻┻━┻╯╰┻━┻┻┻━╋╮┃
╰━╯╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╰━╯""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･
╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╭╮
╭━┳━┳━┳╯┃╭━━┳━┳┳┳━┳╋╋━┳┳━╮
┃╋┃╋┃╋┃╋┃┃┃┃┃╋┃╭┫┃┃┃┃┃┃┃╋┃
┣╮┣━┻━┻━╯╰┻┻┻━┻╯╰┻━┻┻┻━╋╮┃
╰━╯╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╰━╯
｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･｡♥｡･ﾟ♡ﾟ･""")

# Good Night Animation
@client.on(events.NewMessage(pattern='.gn'))
async def gn_cmd(event):
    msg = event.message
    await msg.edit("｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮
╭━┳━┳━┳╯┃╭━┳╋╋━┫╰┫╰╮""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮
╭━┳━┳━┳╯┃╭━┳╋╋━┫╰┫╰╮
┃╋┃╋┃╋┃╋┃┃┃┃┃┃╋┃┃┃╭┫""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮
╭━┳━┳━┳╯┃╭━┳╋╋━┫╰┫╰╮
┃╋┃╋┃╋┃╋┃┃┃┃┃┃╋┃┃┃╭┫
┣╮┣━┻━┻━╯╰┻━┻╋╮┣┻┻━╯""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮
╭━┳━┳━┳╯┃╭━┳╋╋━┫╰┫╰╮
┃╋┃╋┃╋┃╋┃┃┃┃┃┃╋┃┃┃╭┫
┣╮┣━┻━┻━╯╰┻━┻╋╮┣┻┻━╯
╰━╯╱╱╱╱╱╱╱╱╱╱╰━╯""")
    await asyncio.sleep(0.2)
    await msg.edit("""｡♥｡･ﾟ♡ﾟ･｡♥｡･｡･｡･｡♥｡･
╱╱╱╱╱╱╱╭╮╱╱╱╭╮╱╭╮╭╮
╭━┳━┳━┳╯┃╭━┳╋╋━┫╰┫╰╮
┃╋┃╋┃╋┃╋┃┃┃┃┃┃╋┃┃┃╭┫
┣╮┣━┻━┻━╯╰┻━┻╋╮┣┻┻━╯
╰━╯╱╱╱╱╱╱╱╱╱╱╰━╯
｡♥｡･ﾟ♡ﾟ･｡♥° ♥｡･ﾟ♡ﾟ･""")
    
# Pikachu Animation
@client.on(events.NewMessage(pattern='.pikachu'))
async def pikachu_cmd(event):
    msg = event.message
    await msg.edit("⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿
⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿
⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿
⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿""")
    await asyncio.sleep(0.2)
    await msg.edit("""⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿
⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿
⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿
⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿""")

# Hmm Animation
@client.on(events.NewMessage(pattern='.hmm'))
async def hmm_cmd(event):
    msg = event.message
    await msg.edit("┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕
┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕
┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕
┈╲┈┈┈╲┈┈┈┈╱┈┈┈╱┈╲""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕
┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕
┈╲┈┈┈╲┈┈┈┈╱┈┈┈╱┈╲
┈┈╲┈┈▕▔▔▔▔▏┈┈╱╲╲╲▏""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕
┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕
┈╲┈┈┈╲┈┈┈┈╱┈┈┈╱┈╲
┈┈╲┈┈▕▔▔▔▔▏┈┈╱╲╲╲▏
┈╱▔┈┈▕┈┈┈┈▏┈┈▔╲▔▔""")
    await asyncio.sleep(0.2)
    await msg.edit("""┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM
┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM
╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈
▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈
▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈
╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈
┈╲┈┈▏╭━━━━╯▕▕┈┈┈
┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈
┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲
┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲
┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕
┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕
┈╲┈┈┈╲┈┈┈┈╱┈┈┈╱┈╲
┈┈╲┈┈▕▔▔▔▔▏┈┈╱╲╲╲▏
┈╱▔┈┈▕┈┈┈┈▏┈┈▔╲▔▔
┈╲▂▂▂╱┈┈┈┈╲▂▂▂╱┈""")  
    
# Heart Color Animation
@client.on(events.NewMessage(pattern='.heart'))
async def heart_cmd(event):
    msg = event.message
    
    hearts = [
        "❤️",  # Red Heart
        "🧡",  # Orange Heart
        "💛",  # Yellow Heart
        "💚",  # Green Heart
        "💙",  # Blue Heart
        "💜",  # Purple Heart
        "🖤",  # Black Heart
        "🤍",  # White Heart
        "🤎",  # Brown Heart
        "💕",  # Two Hearts
        "💞",  # Revolving Hearts
        "💓",  # Beating Heart
        "💗",  # Growing Heart
        "💖",  # Sparkling Heart
        "💘",  # Heart with Arrow
        "💝",  # Heart with Ribbon
        "💟",  # Heart Decoration
        "❣️",  # Heavy Heart Exclamation
        "💌",  # Love Letter
        "🫀",  # Anatomical Heart
        "🫶",  # Heart Hands
    ]
    
    # Show each heart for 0.3 seconds
    for heart in hearts:
        await msg.edit(heart)
        await asyncio.sleep(0.4)
    
    # Final animation - blinking heart
    for i in range(3):
        await msg.edit("💖")
        await asyncio.sleep(0.4)
        await msg.edit("✨")
        await asyncio.sleep(0.3)
    
    # End with red heart
    await msg.edit("❤️ LOVE YOU! ❤️")

# Drugs Animation
@client.on(events.NewMessage(pattern='.drugs'))
async def drugs_cmd(event):
    msg = event.message
    
    # Start with warning
    await msg.edit("⚠️")
    await asyncio.sleep(0.3)
    
    await msg.edit("⚠️ DRUGS")
    await asyncio.sleep(0.3)
    
    await msg.edit("⚠️ DRUGS ARE")
    await asyncio.sleep(0.3)
    
    await msg.edit("⚠️ DRUGS ARE BAD")
    await asyncio.sleep(0.3)
    
    # Start building the syringe
    await msg.edit("💉")
    await asyncio.sleep(0.3)
    
    await msg.edit("""
　　　　　|
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　|""")
    await asyncio.sleep(0.2)
    
    # Add the face
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼|""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼ 
＜ 、･　　|　　＼""")
    await asyncio.sleep(0.2)
    
    await msg.edit("""
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼ 
＜ 、･　　|　　＼ 
　＼＿＿／∪ _ ∪)""")
    await asyncio.sleep(0.2)
    
    # Complete animation
    await msg.edit("""
Drugs Everything...          
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼ 
＜ 、･　　|　　＼ 
　＼＿＿／∪ _ ∪) 
　　　　　 Ｕ Ｕ""")
    await asyncio.sleep(1)
    
    # Add effects
    await msg.edit("""
💀 Drugs Everything... 💀     
　　　　　|
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼ 
＜ 、･　　|　　＼ 
　＼＿＿／∪ _ ∪) 
　　　　　 Ｕ Ｕ
         
""")
    await asyncio.sleep(0.5)
    
    # Final warning message
    await msg.edit("""
☠️  D R U G S  ☠️
          
　　　　　💉
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　　　　　| 
　／￣￣＼| 
＜ ´･ 　　 |＼ 
　|　３　 | 丶＼ 
＜ 、･　　|　　＼ 
　＼＿＿／∪ _ ∪) 
　　　　　 Ｕ Ｕ
""")
    
# Cobra Animation
@client.on(events.NewMessage(pattern='.cobra'))
async def cobra_cmd(event):
    msg = event.message
    
    # Start with cobra head
    await msg.edit("🐍")
    await asyncio.sleep(0.2)
    
    await msg.edit("🐍\n▓")
    await asyncio.sleep(0.2)
    
    # Build the cobra body
    await msg.edit("""🐍 COBRA
░░░░▓""")
    await asyncio.sleep(0.1)
    
    await msg.edit("""🐍 COBRA
░░░░▓
░░░▓▓""")
    await asyncio.sleep(0.1)
    
    await msg.edit("""🐍 COBRA
░░░░▓
░░░▓▓
░░█▓▓█""")
    await asyncio.sleep(0.1)
    
    await msg.edit("""🐍 COBRA
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██""")
    await asyncio.sleep(0.1)
    
    # Start the snake moving animation
    snake_body = [
        "░░░░▓",
        "░░░▓▓", 
        "░░█▓▓█",
        "░██▓▓██",
        "░░██▓▓██",
        "░░░██▓▓██",
        "░░░░██▓▓██",
        "░░░░░██▓▓██",
        "░░░░██▓▓██",
        "░░░██▓▓██",
        "░░██▓▓██",
        "░██▓▓██",
        "░░██▓▓██",
        "░░░██▓▓██",
        "░░░░██▓▓██",
        "░░░░░██▓▓██",
        "░░░░██▓▓██",
        "░░░██▓▓██",
        "░░██▓▓██",
        "░██▓▓██",
    ]
    
    # Show cobra moving
    for i in range(15):
        body_part = "\n".join(snake_body[i:i+8])
        await msg.edit(f"""🐍 HISS... SSS...
{body_part}""")
        await asyncio.sleep(0.15)
    
    # Show full cobra body
    await msg.edit("""🐍 ⚡ COBRA SNAKE ⚡
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██""")
    await asyncio.sleep(0.3)
    
    # Cobra striking
    await msg.edit("""🐍⚡
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
SSSSSS... HISS!""")
    await asyncio.sleep(0.3)
    
    # More movement
    await msg.edit("""🐍⚠️ DANGER!
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██""")
    await asyncio.sleep(0.3)
    
    # Full length cobra
    await msg.edit("""🐍 🐍 🐍 COBRA 🐍 🐍 🐍
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██""")
    await asyncio.sleep(0.5)
    
    # Cobra coiled
    await msg.edit("""🐍 COBRA COILED
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░░██▓▓███
░░░░██▓▓████
░░░░░██▓▓█████
░░░░░░██▓▓██████
░░░░░░███▓▓███████
░░░░░████▓▓████████
░░░░█████▓▓█████████""")
    await asyncio.sleep(0.5)
    
    # Final cobra with full body
    await msg.edit("""🐍 ⚠️ VENOMOUS COBRA ⚠️
░░░░▓
░░░▓▓
░░█▓▓█
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░██▓▓██
░░██▓▓██
░░░██▓▓██
░░░░██▓▓██
░░░░░██▓▓██
░░░░██▓▓██
░░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░██▓▓██
░░░██▓▓███
░░░░██▓▓████
░░░░░██▓▓█████
░░░░░░██▓▓██████
░░░░░░███▓▓███████
░░░░░████▓▓████████
░░░░█████▓▓█████████
░░░█████░░░█████●███
░░████░░░░░░░███████
░░███░░░░░░░░░██████
░░██░░░░░░░░░░░████
░░░░░░░░░░░░░░░░███
░░░░░░░░░░░░░░░░░░░
        
⚠️ DANGER: VENOMOUS SNAKE ⚠️
🐍 COBRA - Naja naja""")
    
# Rain Animation
@client.on(events.NewMessage(pattern='.rain'))
async def rain_cmd(event):
    msg = event.message
    
    # Cloud forming
    await msg.edit("☁️")
    await asyncio.sleep(0.3)
    
    await msg.edit("☁️ ☁️")
    await asyncio.sleep(0.3)
    
    await msg.edit("☁️ ☁️ ☁️")
    await asyncio.sleep(0.3)
    
    await msg.edit("🌧️ CLOUDS FORMING...")
    await asyncio.sleep(0.3)
    
    # Rain starts
    rain_frames = [
        """🌧️  RAIN  🌧️
  '  '  '  '
 '  '  '  ' 
'  '  '  '  """,
        """🌧️  RAIN  🌧️
 '  '  '  ' 
'  '  '  '  
  '  '  '  '""",
        """🌧️  RAIN  🌧️
'  '  '  '  
  '  '  '  '
 '  '  '  ' """
    ]
    
    for _ in range(8):
        for frame in rain_frames:
            await msg.edit(frame)
            await asyncio.sleep(0.2)
    
    # Heavy rain
    await msg.edit("""⛈️ HEAVY RAIN ⛈️
💧💧💧💧💧💧💧
💧💧💧💧💧💧💧
💧💧💧💧💧💧💧
💧💧💧💧💧💧💧
🌊 PUDDLES FORMING 🌊""")
    await asyncio.sleep(1)
    
    # Final
    await msg.edit("""🌧️🌧️🌧️🌧️🌧️🌧️🌧️
  💧💧💧💧💧💧
    💧💧💧💧💧
      💧💧💧💧
        💧💧💧
          💧💧
            💧
            
☔ TAKE AN UMBRELLA! ☔""")

# Snow Animation
@client.on(events.NewMessage(pattern='.snow'))
async def snow_cmd(event):
    msg = event.message
    
    # Cold weather
    await msg.edit("❄️")
    await asyncio.sleep(0.3)
    
    await msg.edit("❄️ ❄️")
    await asyncio.sleep(0.3)
    
    await msg.edit("❄️ ❄️ ❄️")
    await asyncio.sleep(0.3)
    
    # Snow falling
    snow_flakes = ["❄️", "✨", "＊", "✧", "✶", "✺", "❅", "❆"]
    
    for _ in range(15):
        snow = ""
        for i in range(5):
            line = ""
            for j in range(10):
                if random.random() > 0.6:
                    line += random.choice(snow_flakes) + " "
                else:
                    line += "  "
            snow += line + "\n"
        
        await msg.edit(f"""🌨️ SNOWFALL 🌨️
{snow}
⛄ BUILDING A SNOWMAN ⛄""")
        await asyncio.sleep(0.3)
    
    # Snow covered
    await msg.edit("""🏔️ WINTER WONDERLAND 🏔️
❄️❄️❄️❄️❄️❄️❄️❄️❄️
  ❄️❄️❄️❄️❄️❄️❄️❄️
    ❄️❄️❄️❄️❄️❄️❄️
      ❄️❄️❄️❄️❄️❄️
        ❄️❄️❄️❄️❄️
          ❄️❄️❄️❄️
            ❄️❄️❄️
              ❄️❄️
                ❄️
                
☃️ BRRR... IT'S COLD! ☃️""")

# Fire Animation
@client.on(events.NewMessage(pattern='.fire'))
async def fire_cmd(event):
    msg = event.message
    
    # Spark
    await msg.edit("✨")
    await asyncio.sleep(0.2)
    
    await msg.edit("🔥")
    await asyncio.sleep(0.2)
    
    # Fire growing
    fire_frames = [
        """🔥
 | 
 | """,
        """ 🔥
 /|\\
 | """,
        """  🔥
 /|\\
/ | \\""",
        """   🔥🔥
  /|\\
 / | \\
|     |""",
        """    🔥🔥🔥
   /|\\
  / | \\
 /  |  \\
|       |""",
        """     🔥🔥🔥🔥
    /|\\
   / | \\
  /  |  \\
 /   |   \\
|         |"""
    ]
    
    for frame in fire_frames:
        await msg.edit(frame)
        await asyncio.sleep(0.3)
    
    # Burning fire
    burning = [
        """🔥 FIRE! 🔥
     🔥🔥🔥
    🔥🔥🔥🔥
   🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥""",
        """🔥 FIRE! 🔥
    🔥🔥🔥🔥
   🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥
🔥🔥🔥🔥🔥🔥🔥🔥""",
        """🔥 FIRE! 🔥
   🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥
🔥🔥🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥"""
    ]
    
    for _ in range(10):
        for frame in burning:
            await msg.edit(frame)
            await asyncio.sleep(0.2)
    
    # Fire extinguishing
    await msg.edit("""🚨 FIRE ALERT! 🚨
🔥🔥🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥🔥
   🔥🔥🔥🔥🔥
    🔥🔥🔥🔥
     🔥🔥🔥""")
    await asyncio.sleep(0.5)
    
    await msg.edit("""💦 EXTINGUISHING... 💦
🔥🔥🔥🔥🔥🔥🔥🔥
 🔥🔥🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥🔥
   🔥🔥🔥🔥🔥
    🔥🔥🔥🔥""")
    await asyncio.sleep(0.5)
    
    await msg.edit("""✅ FIRE PUT OUT ✅
 🔥🔥🔥🔥🔥🔥
  🔥🔥🔥🔥🔥
   🔥🔥🔥🔥
    🔥🔥🔥
     🔥🔥
      🔥""")
    await asyncio.sleep(0.5)
    
    await msg.edit("""⚠️ FIRE SAFETY ⚠️
   🚒
  /|\\
 / | \\
🚫 NO PLAYING WITH FIRE! 🔥""")

# Storm Animation
@client.on(events.NewMessage(pattern='.storm'))
async def storm_cmd(event):
    msg = event.message
    
    # Dark clouds
    await msg.edit("☁️")
    await asyncio.sleep(0.2)
    
    await msg.edit("☁️ ☁️")
    await asyncio.sleep(0.2)
    
    await msg.edit("☁️ ☁️ ☁️")
    await asyncio.sleep(0.2)
    
    await msg.edit("🌩️ DARK CLOUDS...")
    await asyncio.sleep(0.3)
    
    # Storm building
    storm_frames = [
        """🌪️ STORM APPROACHING 🌪️
   ⚡
  /|\\
 / | \\""",
        """🌪️ STORM APPROACHING 🌪️
    ⚡
   /|\\
  / | \\
 /  |  \\""",
        """🌪️ STORM WARNING 🌪️
     ⚡⚡
    /|\\
   / | \\
  /  |  \\
 /   |   \\""",
        """🌪️ STORM WARNING 🌪️
      ⚡⚡⚡
     /|\\
    / | \\
   /  |  \\
  /   |   \\
 /    |    \\""",
    ]
    
    for frame in storm_frames:
        await msg.edit(frame)
        await asyncio.sleep(0.4)
    
    # Full storm
    storm_animation = [
        """⛈️ THUNDERSTORM! ⛈️
⚡⚡⚡⚡⚡⚡⚡⚡
🌧️🌧️🌧️🌧️🌧️🌧️🌧️🌧️
💨💨💨💨💨💨💨💨💨💨
🌪️ WIND SPEED: 80 km/h 🌪️""",
        """⛈️ THUNDERSTORM! ⛈️
🌧️🌧️🌧️🌧️🌧️🌧️🌧️🌧️
⚡⚡⚡⚡⚡⚡⚡⚡
💨💨💨💨💨💨💨💨💨💨
🌪️ WIND SPEED: 100 km/h 🌪️""",
        """⛈️ THUNDERSTORM! ⛈️
💨💨💨💨💨💨💨💨💨💨
🌧️🌧️🌧️🌧️🌧️🌧️🌧️🌧️
⚡⚡⚡⚡⚡⚡⚡⚡
🌪️ WIND SPEED: 120 km/h 🌪️"""
    ]
    
    for _ in range(12):
        for frame in storm_animation:
            await msg.edit(frame)
            await asyncio.sleep(0.2)
    
    # Storm calming
    await msg.edit("""🌬️ STORM SUBSIDING...
⚡
🌧️
💨
SEEK SHELTER! 🏠""")
    await asyncio.sleep(1)
    
    await msg.edit("""🌈 STORM PASSED 🌈
  ☁️     ☁️
    ☀️
  /|\\
 / | \\
STAY SAFE! ⚠️""")

# Lightning Animation
@client.on(events.NewMessage(pattern='.lightning'))
async def lightning_cmd(event):
    msg = event.message
    
    # Dark sky
    await msg.edit("🌑")
    await asyncio.sleep(0.3)
    
    await msg.edit("🌑 🌑")
    await asyncio.sleep(0.3)
    
    await msg.edit("🌑 🌑 🌑")
    await asyncio.sleep(0.3)
    
    # Lightning strikes
    lightning_patterns = [
        """⚡ LIGHTNING STRIKE! ⚡
    ⚡
   ⚡ ⚡
  ⚡   ⚡
 ⚡     ⚡
⚡       ⚡""",
        """⚡ LIGHTNING STRIKE! ⚡
 ⚡     ⚡
  ⚡   ⚡
   ⚡ ⚡
    ⚡
   ⚡ ⚡
  ⚡   ⚡""",
        """⚡ LIGHTNING STRIKE! ⚡
⚡       ⚡
 ⚡     ⚡
  ⚡   ⚡
   ⚡ ⚡
    ⚡""",
        """⚡ LIGHTNING STRIKE! ⚡
    ⚡
   ⚡⚡
  ⚡  ⚡
 ⚡    ⚡
⚡      ⚡""",
        """⚡ LIGHTNING STRIKE! ⚡
⚡      ⚡
 ⚡    ⚡
  ⚡  ⚡
   ⚡⚡
    ⚡"""
    ]
    
    # Flash effect
    for _ in range(8):
        # Flash on
        for pattern in lightning_patterns[:3]:
            await msg.edit(pattern)
            await asyncio.sleep(0.1)
        
        # Flash off (dark)
        await msg.edit("""🌑 DARK SKY 🌑
    
THUNDER CRASHES! 💥""")
        await asyncio.sleep(0.2)
        
        # Flash on again
        for pattern in lightning_patterns[3:]:
            await msg.edit(pattern)
            await asyncio.sleep(0.1)
        
        # Dark again
        await msg.edit("""🌑 DARK SKY 🌑
    
BOOM! 🔊""")
        await asyncio.sleep(0.3)
    
    # Multiple lightning
    await msg.edit("""⚡⚡ MULTIPLE STRIKES! ⚡⚡
   ⚡     ⚡
  ⚡ ⚡   ⚡ ⚡
 ⚡   ⚡ ⚡   ⚡
⚡     ⚡     ⚡
 ⚡   ⚡ ⚡   ⚡
  ⚡ ⚡   ⚡ ⚡
   ⚡     ⚡""")
    await asyncio.sleep(0.5)
    
    # Lightning hitting ground
    await msg.edit("""🌩️ LIGHTNING BOLT! 🌩️
         ⚡
        ⚡ ⚡
       ⚡   ⚡
      ⚡     ⚡
     ⚡       ⚡
    ⚡         ⚡
   ⚡           ⚡
  ⚡             ⚡
 ⚡               ⚡
💥 HIT THE GROUND! 💥""")
    await asyncio.sleep(0.8)
    
    # Final warning
    await msg.edit("""⚠️ LIGHTNING SAFETY ⚠️
    ⚡
   ⚡ ⚡
  ⚡   ⚡
 ⚡     ⚡
🏠 STAY INDOORS 🏠
🚫 NO OPEN AREAS 🚫
☎️ EMERGENCY: 112 ☎️""")
    
# India Flag Animation with Sare Jahan Se Achha
@client.on(events.NewMessage(pattern='.india'))
async def india_cmd(event):
    msg = event.message
    
    # Start with Ashok Chakra
    await msg.edit("☸️")
    await asyncio.sleep(0.3)
    
    await msg.edit("☸️\nभारत")
    await asyncio.sleep(0.3)
    
    # Building the flag
    steps = [
        """   ┃
   🟠""",
        """   ┃
   🟠
   ⚪""",
        """   ┃
   🟠
   ⚪
   🟢""",
        """   ┃
   🟠🟠🟠
   ⚪⚪⚪
   🟢🟢🟢""",
        """   ┃
   🟠🟠🟠🟠🟠
   ⚪⚪⚪⚪⚪
   🟢🟢🟢🟢🟢""",
        """   ┃
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢""",
        """🇮🇳
   ┃
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢"""
    ]
    
    for step in steps:
        await msg.edit(step)
        await asyncio.sleep(0.2)
    
    # Flag waving animation
    wave_frames = [
        """🇮🇳
   │
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢""",
        """🇮🇳
   ╱
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢""",
        """🇮🇳
   │
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢""",
        """🇮🇳
   ╲
   🟠🟠🟠🟠🟠
   ⚪⚪🟦☸️🟦⚪⚪
   🟢🟢🟢🟢🟢"""
    ]
    
    # Wave flag 5 times
    for _ in range(5):
        for frame in wave_frames:
            await msg.edit(frame)
            await asyncio.sleep(0.2)
    
    # Show complete flag with lyrics
    lyrics = [
        "सारे जहाँ से अच्छा हिन्दोस्तां हमारा",
        "हम बुलबुलें हैं इसकी यह गुलिस्तां हमारा",
        "ग़ुरबत में हों अगर हम, रहता है दिल वतन में",
        "समझो वहीं हमें भी, दिल हो जहाँ हमारा"
    ]
    
    # Show flag with each line
    for i, line in enumerate(lyrics):
        flag_design = f"""🇮🇳🇮🇳🇮🇳🇮🇳🇮🇳🇮🇳🇮🇳
┏━━━━━━━━━━━━━━━━━━━━┓
┃   🟠🟠🟠🟠🟠🟠🟠   ┃
┃   ⚪⚪🟦☸️🟦⚪⚪   ┃
┃   🟢🟢🟢🟢🟢🟢🟢   ┃
┗━━━━━━━━━━━━━━━━━━━━┛
{line}"""
        
        await msg.edit(flag_design)
        await asyncio.sleep(1)
    
    # National anthem style
    await msg.edit("""🎺 जन गण मन... 🎺
┏━━━━━━━━━━━━━━━━━━━━┓
┃   🟠🟠🟠🟠🟠🟠🟠   ┃
┃   ⚪⚪🟦☸️🟦⚪⚪   ┃
┃   🟢🟢🟢🟢🟢🟢🟢   ┃
┗━━━━━━━━━━━━━━━━━━━━┛
वन्दे मातरम्! 🙏""")
    await asyncio.sleep(1)
    
    # Final patriotic display
    await msg.edit("""✨ भारत माता की जय! ✨
██████████████████████
█🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠█
█⚪⚪⚪🟦☸️🟦⚪⚪⚪█
█🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢█
██████████████████████

🇮🇳 जय हिन्द! 🇮🇳
🇮🇳 वन्दे मातरम्! 🇮🇳
🇮🇳 भारत माता की जय! 🇮🇳""")
    await asyncio.sleep(1)
    
    # End with Ashok Chakra
    await msg.edit("""☸️ अशोक चक्र ☸️
   ⚪⚪⚪⚪⚪
 ⚪🟦🟦🟦🟦🟦⚪
⚪🟦  २४   🟦⚪
 ⚪🟦🟦🟦🟦🟦⚪
   ⚪⚪⚪⚪⚪
   
धर्मचक्र प्रवर्तनाय
सत्यमेव जयते! ✨""")
    
# Dance Animation
@client.on(events.NewMessage(pattern='.dance'))
async def dance_cmd(event):
    msg = event.message
    
    # Start with music
    await msg.edit("🎵")
    await asyncio.sleep(0.2)
    
    # Dance moves
    dance_moves = [
        """💃 DANCE TIME! 💃
   O
  /|\\
  / \\""",
        """💃 DANCE TIME! 💃
 \\O/
  |
  / \\""",
        """💃 DANCE TIME! 💃
   O
  <|>
  / \\""",
        """💃 DANCE TIME! 💃
 \\O/
  |\\
  / \\""",
        """💃 DANCE TIME! 💃
   O
  /|\\
 / \\""",
        """💃 DANCE TIME! 💃
   O
  /|\\
_/ \\_""",
        """💃 DANCE TIME! 💃
 \\O/
  |\\
_/ \\_""",
        """💃 DANCE TIME! 💃
   O
  <|>
_/ \\_"""
    ]
    
    # Dance for 10 seconds
    for _ in range(15):
        for move in dance_moves:
            await msg.edit(move)
            await asyncio.sleep(0.2)
    
    # Final dance
    await msg.edit("""🕺💃 DANCE PARTY! 💃🕺
   O   O
  /|\\ /|\\
  / \\ / \\
🎶 Let's Dance! 🎶""")

# Love Animation
@client.on(events.NewMessage(pattern='.love'))
async def love_cmd(event):
    msg = event.message
    
    # Start with single heart
    await msg.edit("❤️")
    await asyncio.sleep(0.3)
    
    # Heart breaking
    await msg.edit("💔")
    await asyncio.sleep(0.5)
    
    # Broken pieces
    await msg.edit("💔\n/\\")
    await asyncio.sleep(0.3)
    
    await msg.edit("💔\n/\\\n\\/")
    await asyncio.sleep(0.3)
    
    # Pieces falling
    await msg.edit("   💔\n  /\\\n \\/\n💔")
    await asyncio.sleep(0.3)
    
    await msg.edit("     💔\n    /\\\n   \\/\n  💔\n /\\")
    await asyncio.sleep(0.3)
    
    # Pieces coming back together
    await msg.edit("💔 pieces coming together...")
    await asyncio.sleep(0.5)
    
    await msg.edit("    💔\n   <3\n  💔")
    await asyncio.sleep(0.3)
    
    await msg.edit("   💔\n  <3>\n 💔")
    await asyncio.sleep(0.3)
    
    await msg.edit("  💔\n <3❤️3>\n💔")
    await asyncio.sleep(0.3)
    
    # Heart healing
    await msg.edit("❤️‍🩹")
    await asyncio.sleep(0.5)
    
    # Heart complete again
    await msg.edit("❤️")
    await asyncio.sleep(0.3)
    
    # Love grows
    love_growth = [
        "❤️",
        "💕",
        "💞",
        "💖",
        "💗",
        "💓",
        "💘"
    ]
    
    for heart in love_growth:
        await msg.edit(heart)
        await asyncio.sleep(0.2)
    
    # Final love message
    await msg.edit("""💖 LOVE CONQUERS ALL 💖
❤️🧡💛💚💙💜
   /\\   /\\
  /  \\ /  \\
 /    ❤    \\
 \\   LOVE   /
  \\        /
   \\      /
    \\    /
     \\  /
      \\/
      
✨ True Love Never Dies ✨""")

# Bomb Animation
@client.on(events.NewMessage(pattern='.bomb'))
async def bomb_cmd(event):
    msg = event.message
    
    # Bomb with timer
    await msg.edit("💣")
    await asyncio.sleep(0.3)
    
    await msg.edit("💣 5...")
    await asyncio.sleep(0.5)
    
    await msg.edit("💣 4...")
    await asyncio.sleep(0.5)
    
    await msg.edit("💣 3...")
    await asyncio.sleep(0.5)
    
    await msg.edit("💣 2...")
    await asyncio.sleep(0.5)
    
    await msg.edit("💣 1...")
    await asyncio.sleep(0.5)
    
    # Explosion sequence
    explosion_frames = [
        """💥
🔥""",
        """💥💥
🔥🔥""",
        """💥💥💥
🔥🔥🔥""",
        """💥💥💥💥
🔥🔥🔥🔥""",
        """💥💥💥💥💥
🔥🔥🔥🔥🔥""",
        """💥💥💥💥💥💥
🔥🔥🔥🔥🔥🔥""",
        """💥💥💥💥💥💥💥
🔥🔥🔥🔥🔥🔥🔥""",
        """💥💥💥💥💥💥💥💥
🔥🔥🔥🔥🔥🔥🔥🔥""",
        """💥💥💥💥💥💥💥💥💥
🔥🔥🔥🔥🔥🔥🔥🔥🔥""",
    ]
    
    for frame in explosion_frames:
        await msg.edit(frame)
        await asyncio.sleep(0.1)
    
    # Big explosion
    await msg.edit("""💥💥💥💥💥💥💥💥💥💥
💥💥💥💥💥💥💥💥💥💥
💥💥💥💥💥💥💥💥💥💥
💥💥💥💥💥💥💥💥💥💥
💥💥💥💥💥💥💥💥💥💥
BOOM! 💥""")
    await asyncio.sleep(0.3)
    
    # Explosion clearing
    await msg.edit("""☁️☁️☁️☁️☁️☁️☁️☁️☁️☁️
☁️☁️☁️☁️☁️☁️☁️☁️☁️☁️
☁️☁️☁️☁️☁️☁️☁️☁️☁️☁️
☁️☁️☁️☁️☁️☁️☁️☁️☁️☁️
☁️☁️☁️☁️☁️☁️☁️☁️☁️☁️
Smoke clears...""")
    await asyncio.sleep(0.5)
    
    # Final crater
    await msg.edit("""🌋 EXPLOSION COMPLETE 🌋
      
      /\\
     /  \\
    /    \\
   /      \\
  /________\\
  
⚠️ AREA DESTROYED ⚠️""")

# Clock Animation
@client.on(events.NewMessage(pattern='.clock'))
async def clock_cmd(event):
    msg = event.message
    
    # Clock face
    clock_positions = [
        """🕐
  ╲
   │
   │""",
        """🕑
   ╲
    ╲
     │""",
        """🕒
    ╲
     ╲
      │""",
        """🕓
     │
      ╲
       ╲""",
        """🕔
     │
      │
       ╲""",
        """🕕
     │
      │
       │""",
        """🕖
     │
      │
     ╱""",
        """🕗
     │
    ╱
   ╱""",
        """🕘
   ╱
  ╱
 │""",
        """🕙
  ╱
 ╱
│""",
        """🕚
 ╱
│
│""",
        """🕛
│
│
│"""
    ]
    
    # Show 1 minute of clock ticking
    for _ in range(5):  # 5 minutes
        for i, position in enumerate(clock_positions):
            time_display = f"{i+1:02d}:00" if i < 12 else "12:00"
            await msg.edit(f"""⏰ ANALOG CLOCK ⏰
  ┌─────────┐
  │{position.center(9)}│
  └─────────┘
🕰️ {time_display} 🕰️""")
            await asyncio.sleep(0.2)
    
    # Digital clock countdown
    for i in range(10, 0, -1):
        await msg.edit(f"""⏱️ COUNTDOWN ⏱️
┏━━━━━━━━━━━┓
┃  00:{i:02d}  ┃
┗━━━━━━━━━━━┛
Time's running out!""")
        await asyncio.sleep(0.5)
    
    # Alarm ringing
    await msg.edit("""🔔 ALARM! 🔔
  ┌───────┐
  │ 07:30 │
  └───────┘
⏰ WAKE UP! ⏰
💤💤💤💤💤""")
    await asyncio.sleep(1)
    
    # Final clock
    await msg.edit("""🕰️ TIME NEVER STOPS 🕰️
  ┌──────────┐
  │   12    │
  │11   ☀️  1│
  │10   │   2│
  │9    │   3│
  │  8──┼──4│
  │7        5│
  │    6    │
  └──────────┘
⏳ Time is precious! ⏳""")

# Train Animation
@client.on(events.NewMessage(pattern='.train'))
async def train_cmd(event):
    msg = event.message
    
    # Train approaching
    await msg.edit("🚂")
    await asyncio.sleep(0.3)
    
    await msg.edit("🚂 CHOO CHOO!")
    await asyncio.sleep(0.3)
    
    # Train building
    train_parts = [
        "[🚂]",
        "[🚂][🚃]",
        "[🚂][🚃][🚃]",
        "[🚂][🚃][🚃][🚃]",
        "[🚂][🚃][🚃][🚃][🚃]",
        "[🚂][🚃][🚃][🚃][🚃][🚃]",
    ]
    
    for part in train_parts:
        await msg.edit(f"{part}\n▬▬▬▬▬▬▬▬▬")
        await asyncio.sleep(0.3)
    
    # Train moving
    track = "─" * 50
    
    for i in range(20):
        train_display = f"""{' ' * i}[🚂][🚃][🚃][🚃][🚃][🚃]
{track}
🚉 TRAIN IN MOTION 🚉
SPEED: {60 + i*5} km/h"""
        await msg.edit(train_display)
        await asyncio.sleep(0.2)
    
    # Train at station
    await msg.edit("""🚂🛑 TRAIN ARRIVING 🛑🚂
[🚂][🚃][🚃][🚃][🚃][🚃]
▬▬▬▬▬▬▬🚉▬▬▬▬▬▬▬
👥 BOARDING PASSENGERS 👥""")
    await asyncio.sleep(1)
    
    # Train departing
    await msg.edit("""🚂⚠️ TRAIN DEPARTING ⚠️🚂
[🚂][🚃][🚃][🚃][🚃][🚃]
▬▬▬▬▬▬▬🚉▬▬▬▬▬▬▬
🚶‍♂️🚶‍♀️ ALL ABOARD! 🚶‍♀️🚶‍♂️""")
    await asyncio.sleep(1)
    
    # Final train moving away
    for i in range(10):
        spaces = " " * (i * 3)
        await msg.edit(f"""{spaces}[🚂][🚃][🚃][🚃][🚃][🚃]
{'─' * 50}
🚂 CHOO CHOO! FAREWELL! 🚂""")
        await asyncio.sleep(0.3)

# Party Animation
@client.on(events.NewMessage(pattern='.party'))
async def party_cmd(event):
    msg = event.message
    
    # Party starting
    await msg.edit("🎉")
    await asyncio.sleep(0.2)
    
    await msg.edit("🎉 PARTY!")
    await asyncio.sleep(0.2)
    
    # Confetti
    confetti = ["🎊", "🎈", "✨", "🥳", "🎆", "🎇"]
    
    for _ in range(10):
        screen = ""
        for _ in range(3):
            line = ""
            for _ in range(8):
                line += random.choice(confetti) + " "
            screen += line + "\n"
        
        await msg.edit(f"""🥳 PARTY TIME! 🥳
{screen}
💃 DANCE 🕺
🎶 MUSIC 🎵""")
        await asyncio.sleep(0.3)
    
    # Poppers
    popper_frames = [
        """🎉 PARTY POPPERS! 🎉
   🎊
  🎊🎊
 🎊🎊🎊
🎊🎊🎊🎊""",
        """🎉 PARTY POPPERS! 🎉
   ✨
  ✨✨
 ✨✨✨
✨✨✨✨""",
        """🎉 PARTY POPPERS! 🎉
   🎈
  🎈🎈
 🎈🎈🎈
🎈🎈🎈🎈"""
    ]
    
    for _ in range(5):
        for frame in popper_frames:
            await msg.edit(frame)
            await asyncio.sleep(0.2)
    
    # Fireworks
    firework_frames = [
        """🎆 FIREWORKS! 🎆
   ✨
    *""",
        """🎆 FIREWORKS! 🎆
   ✨
  * *""",
        """🎆 FIREWORKS! 🎆
   ✨
 * * *""",
        """🎆 FIREWORKS! 🎆
   ✨
* * * *""",
        """🎆 FIREWORKS! 🎆
   💥
* * * *""",
        """🎆 FIREWORKS! 🎆
   🎇
* * * *"""
    ]
    
    for _ in range(3):
        for frame in firework_frames:
            await msg.edit(frame)
            await asyncio.sleep(0.1)
    
    # Final party scene
    await msg.edit("""🎊🎉🎈 ULTIMATE PARTY! 🎈🎉🎊
✨✨✨✨✨✨✨✨✨
🎂🍰🎂🍰🎂🍰🎂🍰🎂
💃🕺💃🕺💃🕺💃🕺💃
🎵🎶🎵🎶🎵🎶🎵🎶🎵
🎆🎇🎆🎇🎆🎇🎆🎇🎆

🥳 HAPPY CELEBRATION! 🥳""")

# Ghost Animation
@client.on(events.NewMessage(pattern='.ghost'))
async def ghost_cmd(event):
    msg = event.message
    
    # Ghost appearing
    await msg.edit("👻")
    await asyncio.sleep(0.3)
    
    await msg.edit("👻 BOO!")
    await asyncio.sleep(0.3)
    
    # Ghost floating
    ghost_frames = [
        """👻
 | 
/ \\""",
        """ 👻
 \\|
 / \\""",
        """  👻
  /|
 / \\""",
        """   👻
   /|
  / \\""",
        """    👻
    /|
   / \\""",
        """     👻
     /|
    / \\"""
    ]
    
    # Ghost floating right
    for frame in ghost_frames:
        await msg.edit(frame)
        await asyncio.sleep(0.2)
    
    # Ghost floating left
    for frame in reversed(ghost_frames):
        await msg.edit(frame)
        await asyncio.sleep(0.2)
    
    # Scary ghost
    await msg.edit("""😱 SCARY GHOST! 😱
   👻👻👻
  👻😈👻
   👻👻👻
  /|||\\
 / | | \\
BOOOO! 👻""")
    await asyncio.sleep(0.5)
    
    # Ghost vanishing
    vanish_frames = [
        """👻
 | 
/ \\""",
        """👻
 |""",
        """👻""",
        """✨""",
        """ """,
        """💨""",
        """🌫️"""
    ]
    
    for frame in vanish_frames:
        await msg.edit(f"GHOST VANISHING...\n{frame}")
        await asyncio.sleep(0.3)
    
    # Final haunted house
    await msg.edit("""🏚️ HAUNTED HOUSE 🏚️
   /\\
  /  \\
 /____\\
 | 👻 |
 |    |
 |____|
/      \\

😨 ENTER IF YOU DARE! 😨""")
    

SYSTEM_PROMPT = """You are replying on behalf of a real human.
Reply naturally, casually, short.
Do not mention AI, ChatGPT, bot, assistant.
Sound like a normal busy person.
Always talk in hinglish.
If user abuses, reply with abuse words like madharchod, behenchod, bhosdike, mc, bc, teri maa ki chut, randi ke pille, gandu, lauda mera, teri maa ki, mkc.
"""
            

from telethon.tl.functions.phone import CreateGroupCallRequest, JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.types import InputGroupCall, DataJSON
import json
import random
import asyncio

# Store call data globally
vc_data = {}

@client.on(events.NewMessage(pattern=r"^\.startvc$"))
async def start_vc(event):
    if not is_owner(event): 
        return
    await delete_command_message(event)
    
    try:
        msg = await event.reply("🎤 Creating voice chat...")
        
        chat = await event.get_chat()
        
        # Create voice chat
        result = await client(CreateGroupCallRequest(
            peer=chat,
            random_id=random.randint(0, 2**31-1)
        ))
        
        # Debug: Check what's in result
        print(f"CreateGroupCall result: {result}")
        print(f"Result attributes: {dir(result)}")
        
        # Different ways to get call ID based on result structure
        call_id = None
        access_hash = None
        
        # Try different attribute names
        if hasattr(result, 'call') and hasattr(result.call, 'id'):
            call_id = result.call.id
            access_hash = result.call.access_hash
        elif hasattr(result, 'id'):
            call_id = result.id
            access_hash = getattr(result, 'access_hash', 0)
        elif hasattr(result, 'updates') and len(result.updates) > 0:
            for update in result.updates:
                if hasattr(update, 'call'):
                    call_id = update.call.id
                    access_hash = update.call.access_hash
                    break
        
        if call_id:
            # Store call data
            vc_data[chat.id] = {
                'call_id': call_id,
                'access_hash': access_hash
            }
            await msg.edit(f"✅ Voice chat created!\nCall ID: `{call_id}`\nNow use `.join`")
        else:
            await msg.edit("⚠️ Voice chat created but couldn't get call ID")
        
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r"^\.join$"))
async def join_vc(event):
    if not is_owner(event): 
        return
    await delete_command_message(event)
    
    try:
        msg = await event.reply("🎧 Joining voice chat...")
        
        chat = await event.get_chat()
        chat_id = chat.id
        
        # Check if we have call data
        if chat_id not in vc_data:
            # Try to get active call from chat
            try:
                # Get full chat info
                from telethon.tl.functions.channels import GetFullChannelRequest
                full = await client(GetFullChannelRequest(chat))
                
                if hasattr(full, 'full_chat') and hasattr(full.full_chat, 'call'):
                    call_id = full.full_chat.call.id
                    access_hash = full.full_chat.call.access_hash
                    
                    vc_data[chat_id] = {
                        'call_id': call_id,
                        'access_hash': access_hash
                    }
                else:
                    await msg.edit("❌ No voice chat found. Use `.startvc` first")
                    return
                    
            except:
                await msg.edit("❌ No voice chat found. Use `.startvc` first")
                return
        
        call_info = vc_data[chat_id]
        
        # Prepare call parameters
        call_data = {
            "ufrag": "user",
            "pwd": "pass" + str(random.randint(1000, 9999)),
            "fingerprints": [],
            "ssrc": random.randint(1000000, 9999999),
            "sources": [0]
        }
        
        params = DataJSON(data=json.dumps(call_data))
        
        # Join the call
        result = await client(JoinGroupCallRequest(
            call=InputGroupCall(
                id=call_info['call_id'],
                access_hash=call_info['access_hash']
            ),
            join_as=await event.client.get_input_entity('me'),
            params=params
        ))
        
        await msg.edit("✅ Joined voice chat successfully!")
        
    except Exception as e:
        await msg.edit(f"❌ Join Error: {str(e)[:100]}")

@client.on(events.NewMessage(pattern=r"^\.(leave|left)$"))
async def leave_vc(event):
    if not is_owner(event): 
        return
    await delete_command_message(event)
    
    try:
        msg = await event.reply("👋 Leaving voice chat...")
        
        chat = await event.get_chat()
        chat_id = chat.id
        
        if chat_id not in vc_data:
            await msg.edit("❌ Not in any voice chat")
            return
        
        call_info = vc_data[chat_id]
        
        # Leave the call
        result = await client(LeaveGroupCallRequest(
            call=InputGroupCall(
                id=call_info['call_id'],
                access_hash=call_info['access_hash']
            ),
            source=0
        ))
        
        await msg.edit("✅ Left voice chat!")
        
    except Exception as e:
        await msg.edit(f"❌ Leave Error: {str(e)[:100]}")
        
@client.on(events.NewMessage(pattern=r'^\.tts(?:\s+([mf]))?(?:\s+(hindi|eng))?\s+(.+)', outgoing=True))
async def tts_cmd(event):
    """Convert text to speech with male/female voice in Hindi or English"""
    gender = event.pattern_match.group(1) or 'm'  # default male
    language = event.pattern_match.group(2) or 'eng'  # default english
    text = event.pattern_match.group(3)
    reply = await event.get_reply_message()
    
    # Delete command message
    await event.delete()
    
    # Send processing message
    processing_msg = await event.reply("**Converting to speech...**")
    
    try:
        if len(text) > 500:
            text = text[:500]
        
        # Voice mapping
        if language == 'hindi':
            voice = 'hi-IN-MadhurNeural' if gender == 'm' else 'hi-IN-SwaraNeural'
        else:  # english
            voice = 'en-US-GuyNeural' if gender == 'm' else 'en-US-JennyNeural'
        
        filename = f"tts_{event.id}.mp3"
        
        await edge_tts.Communicate(text, voice).save(filename)
        
        await processing_msg.delete()
        
        await client.send_file(
            event.chat_id,
            filename,
            voice_note=True,
            reply_to=reply.id if reply else None
        )
        
        os.remove(filename)
        
    except Exception as e:
        await processing_msg.edit(f"**TTS Error:** {str(e)}")
        await asyncio.sleep(3)
        await processing_msg.delete()
        if os.path.exists(filename):
            os.remove(filename)

@client.on(events.NewMessage(pattern=r'^\.report(?:\s+(\d+))?', outgoing=True))
async def report_cmd(event):
    """Report message multiple times to Telegram"""
    reply = await event.get_reply_message()
    
    if not reply:
        await event.edit("❌ **Please reply to a message to report it!**")
        await asyncio.sleep(3)
        await event.delete()
        return
    
    # Parse count (default 1, max 20)
    count = int(event.pattern_match.group(1) or 1)
    if count > 20:
        count = 20
    
    # Send processing message
    processing = await event.edit(f"📢 **Reporting message {count} time(s)...**")
    
    try:
        success = 0
        for i in range(count):
            try:
                await client(ReportRequest(
                    peer=await event.get_input_chat(),
                    id=[reply.id],
                    reason=InputReportReasonSpam(),
                    message=f"Report #{i+1} via userbot"
                ))
                success += 1
                await asyncio.sleep(0.5)  # Small delay between reports
            except:
                pass
        
        if success > 0:
            await processing.edit(f"✅ **Message reported {success} time(s) successfully!**")
        else:
            await processing.edit("❌ **Failed to report message!**")
            
    except Exception as e:
        await processing.edit(f"❌ **Report Error:** `{str(e)}`")
    
    await asyncio.sleep(3)
    await event.delete()
    
@client.on(events.NewMessage(pattern=r'^\.unpin(?: |$)(.*)', outgoing=True))
async def unpin_cmd(event):
    """Unpin a specific message or all"""
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    
    try:
        if args == "all":
            await client.unpin_message(event.chat_id, None)
            await event.edit("**📌 All messages unpinned!**")
        elif reply:
            await client.unpin_message(event.chat_id, reply.id)
            await event.edit("**📌 Message unpinned!**")
        else:
            # Unpin latest pinned message
            await client.unpin_message(event.chat_id)
            await event.edit("**📌 Latest pinned message removed!**")
        
        await asyncio.sleep(2)
        await event.delete()
    except Exception as e:
        await event.edit(f"**Failed to unpin:** {str(e)}")
        
@client.on(events.NewMessage(pattern=r'^\.pin(?: |$)(.*)', outgoing=True))
async def pin_cmd(event):
    """Pin a message (silently if -s flag used)"""
    reply = await event.get_reply_message()
    if not reply:
        await event.edit("**Reply to a message to pin it!**")
        return
    
    args = event.pattern_match.group(1)
    silent = "-s" in args or "--silent" in args
    
    try:
        await client.pin_message(
            event.chat_id,
            reply.id,
            notify=not silent
        )
        await event.edit(f"**📌 Message pinned!** {'(silently)' if silent else ''}")
        await asyncio.sleep(2)
        await event.delete()
    except Exception as e:
        await event.edit(f"**Failed to pin:** {str(e)}")
    
@client.on(events.NewMessage(pattern=r'^\.ss(?: |$)(.*)', outgoing=True))
async def screenshot_cmd(event):
    """Take website screenshot"""
    url = event.pattern_match.group(1)
    if not url:
        await event.edit("**Usage:** `.ss https://google.com`")
        return
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    await event.edit("**Taking screenshot...**")
    
    try:
        # Using external API
        api_url = f"https://image.thum.io/get/width/800/crop/600/{url}"
        
        await client.send_file(
            event.chat_id,
            api_url,
            caption=f"**Screenshot of:** {url}",
            reply_to=event.reply_to_msg_id
        )
        await event.delete()
    except:
        await event.edit("**Failed to capture screenshot!**")


        
import pyfiglet

@client.on(events.NewMessage(pattern=r'^\.ascii(?:\s+(.+))?', outgoing=True))
async def ascii_cmd(event):
    """Convert text to ASCII art"""
    text = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    
    if not text and not reply:
        await event.edit("""
**ASCII Art Generator**

**Usage:**
`.ascii Hello World`
`.ascii slant Telegram`
`.ascii big Python`

**Available fonts:** `standard`, `slant`, `big`, `block`, `bubble`
        """)
        return
    
    # Parse font if specified
    fonts = ['standard', 'slant', 'big', 'block', 'bubble', 'digital']
    font = 'standard'
    
    if text:
        parts = text.split(' ', 1)
        if parts[0].lower() in fonts:
            font = parts[0].lower()
            if len(parts) > 1:
                text = parts[1]
            else:
                text = ""
    
    # Get text from reply if no text provided
    if not text and reply:
        text = reply.text or reply.caption or ""
    
    if not text:
        await event.edit("**❌ Please provide text to convert!**")
        return
    
    # Limit text length
    if len(text) > 20:
        text = text[:20]
        await event.edit("**⚠️ Text too long, truncated to 20 characters**")
    
    try:
        # Generate ASCII art
        ascii_art = pyfiglet.figlet_format(text, font=font)
        
        # Check if ASCII art is too long for Telegram
        if len(ascii_art) > 4000:
            # Split into parts
            parts = [ascii_art[i:i+4000] for i in range(0, len(ascii_art), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await event.edit(f"**ASCII Art ({font}):**\n```{part}```")
                else:
                    await event.respond(f"```{part}```")
        else:
            await event.edit(f"**ASCII Art ({font}):**\n```{ascii_art}```")
    
    except Exception as e:
        await event.edit(f"**❌ Error:** `{str(e)}`\n**Try:** `.ascii` for help")
        
@client.on(events.NewMessage(pattern=r'^\.demote(?:\s+@?(\w+))?', outgoing=True))
async def demote_cmd(event):
    """Remove admin rights from user"""
    reply = await event.get_reply_message()
    
    # Get username from message or reply
    username = event.pattern_match.group(1)
    
    if not username and not reply:
        await event.edit("**Usage:** `.demote @username` or reply to admin")
        return
    
    try:
        # Get user entity
        if username:
            user = await client.get_entity(username)
        else:
            user = await client.get_entity(reply.sender_id)
        
        # Remove all admin rights (empty rights)
        no_rights = ChatAdminRights(
            change_info=False,
            post_messages=False,
            edit_messages=False,
            delete_messages=False,
            ban_users=False,
            invite_users=False,
            pin_messages=False,
            add_admins=False,
            anonymous=False,
            manage_call=False,
            other=False
        )
        
        # Demote user
        await client(EditAdminRequest(
            channel=event.chat_id,
            user_id=user.id,
            admin_rights=no_rights,
            rank=""  # Empty title
        ))
        
        await event.edit(f"**✅ Successfully demoted [{user.first_name}](tg://user?id={user.id})!**")
        
    except Exception as e:
        error_msg = str(e)
        if "USER_NOT_PARTICIPANT" in error_msg:
            await event.edit("**❌ User is not in this chat!**")
        elif "USER_ADMIN_INVALID" in error_msg:
            await event.edit("**❌ Can't demote this user!**")
        elif "CHAT_ADMIN_REQUIRED" in error_msg:
            await event.edit("**❌ You need admin rights to demote!**")
        elif "USER_ID_INVALID" in error_msg:
            await event.edit("**❌ Invalid user specified!**")
        else:
            await event.edit(f"**❌ Error:** `{error_msg}`")
            
@client.on(events.NewMessage(pattern=r'^\.promote(?:\s+@?(\w+))?(?:\s+(.*))?', outgoing=True))
async def promote_cmd(event):
    """Promote user to admin with optional title"""
    reply = await event.get_reply_message()
    
    # Get username from message or reply
    username = event.pattern_match.group(1)
    custom_title = event.pattern_match.group(2)
    
    if not username and not reply:
        await event.edit("**Usage:** `.promote @username [title]` or reply to user")
        return
    
    try:
        # Get user entity
        if username:
            user = await client.get_entity(username)
        else:
            user = await client.get_entity(reply.sender_id)
        
        # Define admin rights (you can customize these)
        admin_rights = ChatAdminRights(
            change_info=True,      # Can change chat info
            post_messages=True,    # Can post messages (for channels)
            edit_messages=True,    # Can edit messages
            delete_messages=True,  # Can delete messages
            ban_users=True,        # Can ban users
            invite_users=True,     # Can invite users
            pin_messages=True,     # Can pin messages
            add_admins=True,       # Can add other admins
            anonymous=False,       # Can send messages anonymously
            manage_call=True,      # Can manage voice calls
            other=True             # Other admin rights
        )
        
        # Promote user
        await client(EditAdminRequest(
            channel=event.chat_id,
            user_id=user.id,
            admin_rights=admin_rights,
            rank=custom_title or "Admin"  # Admin title
        ))
        
        # Success message
        title_text = f" as **{custom_title}**" if custom_title else ""
        await event.edit(f"**✅ Successfully promoted [{user.first_name}](tg://user?id={user.id}){title_text}!**")
        
    except Exception as e:
        error_msg = str(e)
        if "USER_NOT_PARTICIPANT" in error_msg:
            await event.edit("**❌ User is not in this chat!**")
        elif "USER_ADMIN_INVALID" in error_msg:
            await event.edit("**❌ Can't promote this user!**")
        elif "CHAT_ADMIN_REQUIRED" in error_msg:
            await event.edit("**❌ You need admin rights to promote!**")
        elif "USER_ID_INVALID" in error_msg:
            await event.edit("**❌ Invalid user specified!**")
        else:
            await event.edit(f"**❌ Error:** `{error_msg}`")
            
# Dictionary to store active fights
active_fights = {}  # {target_user_id: True/False}

@client.on(events.NewMessage(pattern=r'^type$', outgoing=True))
async def typefight_start(event):
    """Start typefight silently"""
    
    if not event.is_reply:
        # Silent fail - kuch nahi hoga
        await event.delete()
        return
    
    # Get target user
    reply_msg = await event.get_reply_message()
    target_user = reply_msg.sender_id
    
    # Check if already fighting
    if target_user in active_fights and active_fights[target_user]:
        await event.delete()
        return
    
    # Start fight silently
    active_fights[target_user] = True
    
    
    # Create listener for target user
    @client.on(events.NewMessage(incoming=True))
    async def fight_listener(listener_event):
        # Skip if not from target or fight ended
        if listener_event.sender_id != target_user or not active_fights.get(target_user, False):
            return
        
        # Send random roast
        roast = random.choice(abuse_roast)
        await listener_event.reply(roast)
        
        # Small delay to avoid rate limit
        await asyncio.sleep(1.5)
    
    # Store listener reference
    if not hasattr(client, 'fight_listeners'):
        client.fight_listeners = {}
    if target_user not in client.fight_listeners:
        client.fight_listeners[target_user] = []
    client.fight_listeners[target_user].append(fight_listener)

@client.on(events.NewMessage(pattern=r'^end$', outgoing=True))
async def typefight_stop(event):
    """Stop typefight silently"""
    
    if not event.is_reply:
        await event.delete()
        return
    
    # Get target user
    reply_msg = await event.get_reply_message()
    target_user = reply_msg.sender_id
    
    # Stop fight
    if target_user in active_fights:
        active_fights[target_user] = False
        del active_fights[target_user]
    
    # Remove listeners
    if hasattr(client, 'fight_listeners') and target_user in client.fight_listeners:
        for listener in client.fight_listeners[target_user]:
            client.remove_event_handler(listener)
        del client.fight_listeners[target_user]
    
    # Delete command message
    await event.delete()
    
# ------------- SETTINGS -----------------
MAX_PER_RUN = 10000000000000000
DELAY_SECONDS = 6  # 🔥 DEFAULT DELAY 6 SECONDS FOR ALL COMMANDS
TAG_DELAY = 4      # 🔥 TAG COMMANDS DELAY

# ----------- MESSAGES DATA --------------

# 🔥 BOYS ROAST LINES
boys_roast = [
"**BHAI, TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**BHAI, TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**BHAI TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**BHAI TU EK CHALTA PHIRTA BUG HAI.** 🐛",
    "**TU HERO NAHI, SIRF ERROR 404 KA EXAMPLE HAI.** ❌",
"**TERE JOKES SE CALCULATOR BHI CONFUSE HO JAYE.** 🧮",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**BHAI TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU EK BROKEN LINK HO.** 🔗",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU EK OFFLINE FILE JAISA HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MEMBER HO WHATSAPP GROUP KA.** 🔇",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LIFE KA BETA VERSION HAI.** 🧪",
"**TU EK CHALTA PHIRTA CAPTCHA HAI.** 🔢",
"**TERE BAATEIN BACKGROUND NOISE JAISI HAI.** 🎧",
"**TU CHALTA PHIRTA DEMO ACCOUNT HAI.** 📝",
"**BHAI TU WALKING ERROR MESSAGE HO.** ❌",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE LOGIC KE AAGE CALCULATOR BHI FAIL HO JAYE.** 🧮",
"**TU EK CANCELLED DOWNLOAD KA EXAMPLE HAI.** ⬇️",
"**BHAI TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU LIFE KA GLITCH HO.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎬",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HO – SABKO SKIP KARNA HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HO – SAB IGNORE KARTE HAI.** 📅",
"**BHAI TU DEMO ACCOUNT KA HUMAN VERSION HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HO.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HO JO HAMESHA CRASH HOTI HAI.** 📱",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**BHAI TU HERO NAHI, SIRF DEMO VIDEO KA CLIP HAI.** 🎞️",
"**TU EK CRASHED APP HAI – KABHI OPEN NAHI HOTA.** 📱",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**BHAI TU LIFE KA BUG REPORT HAI.** 🐛",
"**TU EK FORWARDED MESSAGE JAISA HAI – IGNORE KARTA SABKO.** 📩",
"**TERE HAIRSTYLE SE BARBER BHI SHOCK HO JAYE.** 💇‍♂️",
"**TU CHALTA PHIRTA CAPTCHA HAI – SABKO CONFUSE KARTA.** 🔢",
"**BHAI TU LOW BATTERY ALERT HAI.** 🔋",
"**TU EK CANCELLED CALL HO – KOI NAHI SUNTA.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN BHI PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA POSTER HAI.** 🖼️",
"**BHAI TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO ACCOUNT HAI – INCOMPLETE AUR USELESS.** 📝",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU WALKING TYPO HAI.** ✏️",
"**BHAI TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF TEASER VIDEO KA CLIP HAI.** 🎬",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**BHAI TU OTT TRIAL SHOW HAI – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU EK WALKING ERROR MESSAGE HAI.** ❌",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HAI – SAB IGNORE KARTE HAIN.** 📅",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HAI JO HAMESHA CRASH HOTI HAI.** 📱",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**BHAI TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TU EK WALKING TYPO HAI.** ✏️",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HAI – INCOMPLETE AUR USELESS.** 🎥",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU LOW BATTERY ALERT HAI.** 🔋",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – KOI NAHI DEKHTA.** 📄",
"**TERE UPDATES HAMESHA PENDING HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAIN.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**BHAI TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🖱️",
"**TERE BAAT KARTE HI SABKO LAGTA HAI SPAM CALL AAYI.** 📞",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
    "**BHAI, TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**BHAI, TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**BHAI TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**BHAI TU CHAI KI PYALI KI TARAH HAI – GARAM HAI PAR KISI KO PASAND NAHI!** ☕",
    "**TERE JAISE LOGON KE LIYE HI BLOCK BUTTON BANA HAI!** 🚫",
    "**BHAI TU INSTAGRAM REELS KI TARAH HAI – 15 SECOND MEIN BORING!** ⏱️",
    "**TERE DIMAG KI SPEED 2G HAI – LOAD HONE MEIN 10 SAAL LAGTE HAIN!** 🐌"
]

# 👧 GIRLS ROAST LINES
girls_roast = [
    "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
    "**TUMHARI HASEEB SE TOH CALCULATOR BHI GALAT ANSWER DETA HAI!** 🧮",
    "**TUMHARI BATO SE TOH WEATHER FORECAST BHI ACCURATE HO JATA HAI!** 🌦️",
    "**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN!** 👗",
    "**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN!** 😎"
     "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
    "**TUMHARI SELFIE DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI BATO SE WEATHER FORECAST BHI ACCURATE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LEVEL LOW HO JATA HAI.** ⏳",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI SMILE DEKHKAR LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE COMPUTER BHI CONFUSED HO JATA HAI.** 🖥️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI ATTITUDE SE MOUNTAINS BHI HIL JATE HAIN.** ⛰️",
"**TUMHARI BATO SE WEATHER BHI BAD MOOD MEIN AA JATA HAI.** 🌧️",
"**TUMHARI STYLE DEKHKAR DRESSING EXPERTS BHI RETIRE HO JATE HAIN.** 👠",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – SABKO WARNING DENE KE LIYE.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA LOUD HAI.** 🔊",
"**TUMHARI SELFIE DEKHKAR FILTER BHI TIRCHHI NAZAR KARNE LAG JATA HAI.** 📸",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI HEIGHT KAM KAR LETE HAIN.** 🏔️",
"**TUMHARI BATO SE WEATHER BHI SURPRISE HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 😎",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 📢",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI STYLE SE FASHION EXPERTS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR DETE HAIN.** 🧮",
"**TUMHARI ATTITUDE SE CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI BATO SE WEATHER FORECAST BHI FAIL HO JATA HAI.** 🌧️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 🔔",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA  CHHOD DETE HAIN.** 😎",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI SHOCK HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA LOUD HAI.** 🔊",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LEVEL LOW HO JATA HAI.** ⏳",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI BATO SE WEATHER FORECAST BHI ACCURATE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 📢",
"**TUMHARI SMILE DEKHKAR LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE COMPUTER BHI CONFUSED HO JATA HAI.** 🖥️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI ATTITUDE SE MOUNTAINS BHI HIL JATE HAIN.** ⛰️",
"**TUMHARI BATO SE WEATHER BHI SURPRISE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI SELFIES DEKHKAR FILTER BHI RETIRE HO JATA HAI.** 🤳",
"**TUMHARI AWAAZ SUNKE LOGON KA EARPHONE OFF HO JATA HAI.** 🎧",
"**TUMHARI STYLE DEKHKAR FASHION WEEK CANCEL HO JATA HAI.** 👗",
"**TUMHARI HASEEB SE CALCULATOR BHI SHOCK HO JATA HAI.** 🧮",
"**TUM EK WIFI PASSWORD HO – SABKO YAAD, PAR KISI KAAM KA NAHI.** 📶",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR CAMERA BHI CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI SMILE SE SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️KAAM",
"**TUM EK SOFTWARE UPDATE HO – SABKO WARNING DEKHTE HI IRRITATION HO JATI HAI.** 💻",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI RETIRE HO JATE HAIN.** 🎨",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK UNNECESSARY UPDATE HO – ZARURAT NAHI, PAR FORCEFULLY AATI HO.** ⚠️",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SMILE SE LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUM EK FORCEFULLY INSTALLED APP HO – USEFUL NAHI, BAS EXIST HO.** 📲",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI BATO SE WEATHER FORECAST BHI FAIL HO JATA HAI.** 🌧️",
"**TUMHARI STYLE SE FASHION EXPERTS BHI SHOCK HO JATE HAIN.** 👠",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUM EK SOFTWARE UPDATE HO – FORCEFULLY INSTALLED, NEEDED NAHI.** 💻",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LOW HO JATA HAI.** ⏳",
"**TUMHARI SMILE SE LOGON KA MOOD UP HO JATA HAI – AUR DOWN BHI KABHI KABHI.** 🙂",
"**TUM EK UNWANTED UPDATE HO – SABKO WARNING DE DETI HO.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI SELFIES DEKHKAR CAMERA CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI STYLE DEKHKAR FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE SE CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR DETE HAIN.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUM EK FORCEFULLY INSTALLED APP HO – USEFUL NAHI, BAS EXIST HO.** 📲",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN HO JATA HAI.** 🔇",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI SHOCK HO JATE HAIN.** 🎨",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE HO – FORCEFULLY INSTALLED, NEEDED NAHI.** 💻",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI SMILE SE LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUM EK UNNECESSARY UPDATE HO – ZARURAT NAHI, PAR FORCEFULLY AATI HO.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
    "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
    "**TUMHARI HASEEB SE TOH CALCULATOR BHI GALAT ANSWER DETA HAI!** 🧮",
    "**TUMHARI BATO SE TOH WEATHER FORECAST BHI ACCURATE HO JATA HAI!** 🌦️",
    "**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN!** 👗",
    "**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN!** 😎",
    "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
    "**TUMHARI HASEEB SE TOH CALCULATOR BHI GALAT ANSWER DETA HAI!** 🧮",
    "**TUMHARI BATO SE TOH WEATHER FORECAST BHI ACCURATE HO JATA HAI!** 🌦️",
    "**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN!** 👗",
    "**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN!** 😎"
]

# 🗣️ ABUSE ROAST LINES
abuse_roast = [
"🤩💥🔥🔥uL   TERI MUMMY KI CHUT MEI TERE LAND KO DAL KE KAAT DUNGA MADARCHOD 🔪😂🔥",
    "u@   SUN TERI MAA KA BHOSDA AUR TERI BAHEN KA BHI BHOSDA 👿😎👊",
    "😍👊💥up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA",
    "uW   TUJHE DEKH KE TERI RANDI BAHEN PE TARAS ATA HAI MUJHE BAHEN KE LODEEEE 👿💥🤩🔥",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI",
    "uF   SUN MADARCHOD JYADA NA UCHAL MAA CHOD DENGE EK MIN MEI ✅🤣🔥🤩",
    "ui   APNI AMMA SE PUCHNA USKO US KAALI RAAT MEI KAUN CHODNEE AYA THAAA! TERE IS PAPA KA NAAM LEGI 😂👿😳",
    " TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uV   TOHAR BAHIN CHODU BBAHEN KE LAWDE USME MITTI DAL KE CEMENT SE BHAR DU 🏠🤢🤩💥",
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "u|   TUJHE AB TAK NAHI SMJH AYA KI MAI HI HU TUJHE PAIDA KARNE WALA BHOSDIKEE APNI MAA SE PUCH RANDI KE BACHEEEE 🤩👊👤😍",
    "uM   TERI MAA KE BHOSDE MEI SPOTIFY DAL KE LOFI BAJAUNGA DIN BHAR 😍🎶🎶💥",
    "JUNGLE ME NACHTA HE MORE TERI MAAKI CHUDAI DEKKE SAB BOLTE ONCE MORE ONCE MORE 🤣🤣💦💋�I   GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤🤣�",
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE BHAI DEDIYA",
    "MAA KAA BJSODAAA� MADARXHODDDz TERIUUI MAAA KAA BHSODAAAz-TERIIIIII BEHENNNN KO CHODDDUUUU MADARXHODDDDz NIKAL MADARCHODz RANDI KE BACHEz TERA MAA MERI FANz TERI SEXY BAHEN KI CHUT",
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋",
    "CHAL BETA TUJHE MAAF KIA 🤣 ABB APNI GF KO BHEJ",
    "NSHARAM KAR TERI BEHEN KA BHOSDA KITNA GAALIA SUNWAYEGA APNI MAAA BEHEN KE UPER�NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGAuF   TERI VAHEEN NHI HAI KYA? 9 MAHINE RUK SAGI VAHEEN DETA HU 🤣🤣🤩uC   TERI MAA K BHOSDE ME AEROPLANEPARK KARKE UDAAN BHAR DUGA ✈️🛫uV   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣",
    "uE   TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "ub   TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "u]   TERI BAHEN KI CHUT MEI APNA BADA SA LODA GHUSSA DUNGAA KALLAAP KE MAR JAYEGI 🤩😳😳🔥",
    "u   TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩",
    "uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥",
    "up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥",
    "ui   TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍",
    "ug   TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uZ   SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "uZ   TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    "u,   TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤",
    "uZ   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋"
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂��‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY",   
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",   
    "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥ui",   
    "TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍ug",  
    "TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍uZ",  
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥uZ",   
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥r    r    r    u",   
    "TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤uZ",   
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋u6",   
    "TERI VAHEEN KO HORLICKS PEELAKE CHODUNGA MADARCHOD😚U",   
    "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI 💦💋",
    "�@   SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
    "�H   ABE TERI MAAKA BHOSDA MADERCHOOD KR PILLE PAPA SE LADEGA TU 😼😂🤤",
    "�8   GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦",
    "�A   ABE TERI BEHEN KO CHODU RANDIKE PILLE KUTTE KE CHODE 😂👻🔥",
    "�M   TERI MAAKO AISE CHODA AISE CHODA TERI MAAA BED PEHI MUTH DIA 💦💦💦💦",
    "�N   TERI BEHEN KE BHOSDE ME AAAG LAGADIA MERA MOTA LUND DALKE 🔥🔥💦😆😆",
    "�*RANDIKE BACHHE TERI MAAKO CHODU CHAL NIKAL�F",   
    "KITNA CHODU TERI RANDI MAAKI CHUTH ABB APNI BEHEN KO BHEJ 😆👻🤤�P",   
    "TERI BEHEN KOTO CHOD CHODKE PURA FAAD DIA CHUTH ABB TERI GF KO BHEJ 😆💦🤤�}",   
    "TERI GF KO ETNA CHODA BEHEN KE LODE TERI GF TO MERI RANDI BANGAYI ABB CHAL TERI MAAKO CHODTA FIRSE ♥️💦😆😆😆😆�<",   
    "HARI HARI GHAAS ME JHOPDA TERI MAAKA BHOSDA 🤣🤣💋💦�:", 
    "CHAL TERE BAAP KO BHEJ TERA BASKA NHI HE PAPA SE LADEGA TU�7",
    "TERI BEHEN KI CHUTH ME BOMB DALKE UDA DUNGA MAAKE LAWDE�V",  
    "TERI MAAKO TRAIN ME LEJAKE TOP BED PE LITAKE CHOD DUNGA SUAR KE PILLE 🤣🤣💋💋�D",   
    "TERI MAAAKE NUDES GOOGLE PE UPLOAD KARDUNGA BEHEN KE LAEWDE 👻🔥r    �Z",   
    "TERI BEHEN KO CHOD CHODKE VIDEO BANAKE XNXX.COM PE NEELAM KARDUNGA KUTTE KE PILLE 💦💋�O",   
    "TERI MAAAKI CHUDAI KO PORNHUB.COM PE UPLOAD KARDUNGA SUAR KE CHODE 🤣💋💦�Z",   
    "ABE TERI BEHEN KO CHODU RANDIKE BACHHE TEREKO CHAKKO SE PILWAVUNGA RANDIKE BACHHE 🤣🤣�B",  
    "TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄�&TERI BEHEN KI CHUTH ME MERA LUND KAALA�S",
    "TERI BEHEN LETI MERI LUND BADE MASTI SE TERI BEHEN KO MENE CHOD DALA BOHOT SASTE SE�G",   
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋�",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY", 
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",
   "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA",
   "UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣",
   "SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
   "TERI ITEM KI GAAND ME LUND DAALKE,TERE JAISA EK OR NIKAAL DUNGA MADARCHOD🤘🏻🙌🏻☠️ uh",   
   "AUKAAT ME REH VRNA GAAND ME DANDA DAAL KE MUH SE NIKAAL DUNGA SHARIR BHI DANDE JESA DIKHEGA 🙄🤭🤭uW",   
   "TERI MUMMY KE SAATH LUDO KHELTE KHELTE USKE MUH ME APNA LODA DE DUNGA☝🏻☝🏻😬u",   
   "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI👀👯 uG",   
   "TERI MAA KI CHUT MEI BATTERY LAGA KE POWERBANK BANA DUNGA 🔋 🔥🤩u_",   
   "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍uE",   
   "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱uT",   
   "TERI CHUT KI CHUT MEI SHOULDERING KAR DUNGAA HILATE HUYE BHI DARD HOGAAA😱🤮👺uF",
   "TERI MAA KO REDI PE BAITHAL KE USSE USKI CHUT BILWAUNGAA 💰 😵🤩ub",   
   "BHOSDIKE TERI MAA KI CHUT MEI 4 HOLE HAI UNME MSEAL LAGA BAHUT BAHETI HAI BHOFDIKE👊🤮🤢🤢u_",   
   "TERI BAHEN KI CHUT MEI BARGAD KA PED UGA DUNGAA CORONA MEI SAB OXYGEN LEKAR JAYENGE🤢🤩🥳uQ",   
   "TERI MAA KI CHUT MEI SUDO LAGA KE BIGSPAM LAGA KE 9999 FUCK LAGAA DU 🤩🥳🔥uD",   
   "TERI VAHEN KE BHOSDIKE MEI BESAN KE LADDU BHAR DUNGA🤩🥳🔥😈u",
   "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "**CHUTIYE!** 🐒",
    "**MADARCHOD!** 👺",
    "**KUTTE KE PILLE!** 🐕",
    "**SUAR KE BACHHE!** 🐖",
    "**GAANDU!** 🍑",
    "**LODE!** 🍆"
    "**BHAINS KI AULAAD!** 🐃",
    "**KUTTE KE PILLE!** 🐕",
    "**SUAR KE BACHHE!** 🐖",
    "**GAANDU!** 🍑",
    "**LODE!** 🍆"
]

# 💖 FLIRT LINES
flirt_lines = [
"**Tumhare bina ye raat adhoori lagti hai 🌙**",
    "**Tumhari aankhon me meri duniya basti hai ✨**",
    "**Tumhari muskaan mere din ka sabse pyara hissa hai 🌸**",
    "**Tumhare saath bitaye lamhe hamesha yaadgar rahte hain 🖼️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tum meri zindagi ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz sunke dil dhadakne lagta hai 🎵**",
    "**Tumhare saath har pal meri life magical lagti hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari aankhen mere dil ko chain deti hain 🌟**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tumhare saath ka har lamha meri life ka gift hai 🎁**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har lamha meri life ka best moment hai 🖼️**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri duniya ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko roshan karti hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**"
    "**Tumhari aankhen dekhkar dil ka har kone khush ho jata hai 💓**",
    "**Tumhari muskaan mere din ka sabse sundar hissa hai 🌸**",
    "**Tumhare saath har pal ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ki awaaz aur dil ki dhadkan ho 🫀**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tumhari baatein sunke dil ko chain milta hai 🕊️**",
    "**Tum meri duniya ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz se dil ki dhadkan tez ho jati hai 🎵**",
    "**Tumhare saath ka har pal meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ka highlight hain 🖼️**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari aankhen meri duniya ka reflection hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic ho jo sabko khush kar deta hai 💖**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhari yaadon mein guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhare bina zindagi ka rang adhoora lagta hai 🌈**",
    "**Tumhari aankhen dekhkar dil khush ho jata hai 😊**",
    "**Tumhari muskaan meri duniya ko roshan karti hai 🌟**",
    "**Tumhare saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ka sukoon ho 🕊️**",
    "**Tumhari awaaz sunke din suhana lagta hai 🎵**",
    "**Tumhari baatein meri zindagi ko khubsurat banati hain 🌸**",
    "**Tum meri zindagi ka sabse pyaara hissa ho 💖**",
    "**Tumhare saath gujare lamhe hamesha yaadgar rahenge 🌃**",
    "**Tumhari aankhon mein pyaar ki chamak hai ✨**",
    "**Tumhari muskurahat se sab dard door ho jata hai 🫀**",
    "**Tum meri duniya ka woh sitara ho jo kabhi nahi bujh sakta 🌌**",
    "**Tumhari yaadon mein raatein suhani lagti hain 🌙**",
    "**Tumhari baatein dil ko chain deti hain 🕊️**",
    "**Tumhari aankhen meri jaan ka aaina hain 💞**",
    "**Tumhare saath ka har pal ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ki sabse khoobsurat yaad ho 📖**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhari baatein sunke dil me sukoon aata hai 🫀**",
    "**Tum meri zindagi ka woh magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari aankhon ka noor meri duniya roshan karta hai 🌟**",
    "**Tumhari awaaz sunke dil me khushi hoti hai 🎵**",
    "**Tum meri zindagi ka hero ho 💖**",
    "**Tumhari yaadon mein gujra pal hamesha special lagta hai 🌃**",
    "**Tumhari muskaan sabse khubsurat rang hai 🌈**",
    "**Tumhare saath har lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important hissa ho 💞**",
    "**Tumhari aankhen dil ko chhoo jati hain ✨**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 🖼️**",
    "**Tum meri rooh ki awaaz ho 🫀**",
    "**Tumhari muskaan se dil me pyaar jagta hai 💖**",
    "**Tumhari yaadon mein har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri zindagi ka star ho 🌟**",
    "**Tumhari baatein sunke dil me ek nayi energy aati hai ⚡**",
    "**Tumhare saath gujare lamhe meri zindagi ka treasure hain 💎**",
    "**Tum meri love story ka hero aur best friend ho 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌌**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhare saath bitaye lamhe meri zindagi ka gift hain 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz mere dil ki dhadkan ko tez kar deti hai 🫀**",
    "**Tum meri rooh ka sukoon ho aur dil ki khushi bhi 🌹**",
    "**Tumhari yaadon mein guzra lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important part ho 💖**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari baatein meri zindagi me khushiyan bhar deti hain 🌸**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath har pal meri life ko magical banata hai ✨**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari awaaz sunke din me sweetness aa jati hai 🍯**",
    "**Tumhari muskaan meri rooh ko khush kar deti hai 🌹**",
    "**Tumhare saath bita lamha hamesha yaadgar hai 🖼️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💖**",
    "**Tumhari muskaan mere din ka highlight hai 🌸**",
    "**Tumhare saath har pal meri life ka adventure hai 🎢**",
    "**Tum meri love story ka magic ho ✨**",
    "**Tumhari yaadon mein guzra pal hamesha special lagta hai 🌅**",
    "**Tumhari awaaz meri rooh ko sukoon deti hai 🕊️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhari muskaan sabse khubsurat feeling hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ko magical banate hain 🌌**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha yaadgar lagta hai 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhare saath bita lamha meri life ka highlight hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💞**",
    "**Tumhare saath gujare lamhe meri life ka best part hain 🖼️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero ho aur sabse pyaara 💖**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💞**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhare bina ye duniya adhoori lagti hai 😍🌍**",
    "**Tumhari aankhen dekhkar toh dil dhadakne lagta hai 💓**",
    "**Tumhari muskurahat toh chand ko bhi sharmila deti hai 🌙**",
    "**Tumhari baatein sunkar toh time fly ho jata hai ⏰**",
    "**Tum toh meri duniya ka sabse khobsurat hisaab ho 💫**",
    "**Tumhari yaadon mein toh raatein guzaar deta hoon 🌃**",
    "**Tumhari har ada pe toh main fida hoon 😘**",
    "**Tumhari awaaz toh suron se bhi meethai hai 🎵**",
    "**Tumhare bina toh jeena bhi bekar lagta hai 🥺**",
    "**Tum meri zindagi ka sabse khobsurat safar ho 💖**",
    "**Tumhari muskurahat meri rooh ko sukoon deti hai 🕊️**",
    "**Tumhare nazdeek aane se dil ko khushi milti hai 😊**",
    "**Tumhari har ek baat meri dhadkan ko tez kar deti hai 🫀**",
    "**Tumhari aankhon mein jhilmilata huwa pyaar dikhata hai ✨**",
    "**Tumhari awaaz sunke din bhi chand jesa lagta hai 🌙**",
    "**Tum meri rooh ka hisa hai aur dil ka raja 😍**",
    "**Tumhare saath bitaya har pal ek khubsurat memory hai 📖**",
    "**Tumhari muskurahat meri duniya ko roshan kar deti hai 🌟**",
    "**Tumhari yaadon mein guzarte lamhe meri zindagi ko khubsurat banate hain 🌸**",
    "**Tum meri duniya ka light ho jo har andhere ko chhant deti hai 🌅**",
    "**Tumhari baaton se mera din perfect ho jata hai ☀️**",
    "**Tumhare bina meri life adhoori lagti hai 🌵**",
    "**Tumhari har ek ada meri dil ko chu jati hai 💞**",
    "**Tumhari nazaron mein mera future dikhata hai 🔮**",
    "**Tum meri zindagi ka sweetest part ho 🍬**",
    "**Tumhari hansi sunke dil ko ek alag khushi milti hai 🌼**",
    "**Tumhari baatein sunke time ka pata hi nahi chalta ⏳**",
    "**Tumhari aankhon ka jadoo mera dil chura leta hai 💫**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari muskurahat meri rooh ko hamesha khush rakhti hai 🌹**",
    "**Tumhare saath bita pal har dard ko door kar deta hai 🕊️**",
    "**Tumhari aankhon mein mera future aur pyaar deta hai 🌌**",
    "**Tumhare saath bita pal hamesha yaad rahega 📖**",
    "**Tum meri zindagi ka magic ho ✨**",
    "**Tumhari awaaz sunke din meetha ho jata hai 🍯**",
    "**Tumhari har ek ada mera dil chura leti hai 💘**",
    "**Tumhari yaadon mein guzra lamha hamesha khubsurat lagta hai 🌟**",
    "**Tum meri rooh ko khushi aur sukoon dete ho 🫀🕊️**",
    "**Tumhari muskurahat duniya ke sabse khubsurat rang jesa lagta hai 🎨**",
    "**Tum meri life ka hero aur best friend ho 💞**",
    "**Tumhari har ek baat meri zindagi ko beautiful banati hai 🌹**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath har pal ek dream jesa lagta hai 🌙**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari baatein sunke dil me ek alag khushi aati hai 😊**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo sabko roshan kar deta hai 🌅**",
    "**Tumhari hansi sunke mera dil dance karne lagta hai 💃**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📝**",
    "**Tumhari awaaz sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari har ek ada mera dil fida kar deti hai 💞**",
    "**Tumhari aankhon mein mere pyaar ka aaina hai 🌌**",
    "**Tum meri zindagi ka magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari muskurahat sunke din meetha ho jata hai 🍯**",
    "**Tumhare saath bita pal meri life ka best part ho 📖**",
    "**Tumhari awaaz mera dil chu jati hai 🎵**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari muskurahat meri zindagi ko khubsurat banati hai 🌹**",
    "**Tum meri rooh ka hisa ho 🫀**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📖**",
    "**Tumhari yaadon mein guzra lamha meri life ko beautiful banata hai 🌸**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo roshan kar deta hai 🌅**",
    "**Tumhari baatein sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath bita pal hamesha mere liye special ho 📖**",
    "**Tumhari awaaz sunke mera dil dance karne lagta hai 💃**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka hero ho 💖**",
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HO 💖**",
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HO 💖**",
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HO 💖**"
]

# 🔥 HINDI BOYS ROAST LINES
hindi_boys_roast = [
 "**भाई, तू अपने आपको हीरो समझता है, हकीकत में तू जीरो है!** 🤡",
    "**तेरे जैसे लोगों को देखकर ही म्यूट बटन का आविष्कार हुआ था!** 🔇",
    "**भाई, तू इतना बेकार है कि रीसायकल बिन भी तुझे स्वीकार नहीं करेगा!** 🗑️",
    "**तू अपने घर का WiFi पासवर्ड है – सबको याद है पर किसी काम का नहीं!** 📶",
    "**भाई तू तो वॉकिंग क्रिंज कॉन्टेंट है!** 😬",
    "**तेरी फोटो देखकर कैमरा भी अपना लेंस बंद कर लेता है!** 📸",
    "**भाई तू चाय की प्याली की तरह है – गर्म है पर किसी को पसंद नहीं!** ☕",
    "**तेरे जैसे लोगों के लिए ही ब्लॉक बटन बना है!** 🚫",
    "**भाई तू इंस्टाग्राम रील्स की तरह है – 15 सेकंड में बोरिंग!** ⏱️",
    "**तेरे दिमाग की स्पीड 2G है – लोड होने में 10 साल लगते हैं!** 🐌",
    "**भाई, तेरी सोच इतनी छोटी है कि खुद को भी बड़ा नहीं समझ पाता!** 🤏",
    "**तेरे jokes इतने खराब हैं कि गूगल भी हंसने से मना कर देगा!** 😂",
    "**भाई, तू WiFi की तरह है – दिखता है लेकिन किसी काम का नहीं!** 📶",
    "**तेरे memes देखने के बाद लोग अपनी आँखें बंद कर लेते हैं!** 🙈",
    "**भाई, तेरी सेल्फी देखकर कैमरा भी शर्मिंदा हो जाता है!** 📸",
    "**तू चाय की तरह है – हर किसी को नहीं पसंद, सिर्फ कुछ लोग tolerate करते हैं!** ☕",
    "**भाई, तेरी बातें सुनकर यूट्यूब भी skip कर देता है!** ⏭️",
    "**तेरी आवाज़ सुनते ही Spotify भी mute हो जाता है!** 🔇",
    "**भाई, तू dictionary में भी ‘irrelevant’ के synonym के तौर पर लिखा जा सकता है!** 📖",
    "**तेरे status देखकर WhatsApp भी हिल जाता है!** 😬",
    "**भाई, तू refrigerator की तरह है – ठंडा है पर कोई पसंद नहीं करता!** ❄️",
    "**तेरे jokes सुनकर Alexa भी response देना छोड़ देती है!** 🤖",
    "**भाई, तू Google Maps की तरह है – किसी को रास्ता दिखाने लायक नहीं!** 🗺️",
    "**तेरी फोटो देखकर Photoshop भी हाथ खड़े कर देता है!** 🖌️",
    "**भाई, तू TikTok वीडियो की तरह है – 1 सेकंड में बोरिंग!** ⏱️",
    "**तेरी बातें सुनकर Siri भी confuse हो जाती है!** 📱",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है और कोई use नहीं करता!** 🔋",
    "**तेरे jokes इतने outdated हैं कि Internet भी laugh नहीं करता!** 🌐",
    "**भाई, तू microwave की तरह है – गरम है पर कोई real flavor नहीं!** 🍲",
    "**तेरी selfies देखने के बाद Camera भी auto-delete कर देता है!** 📸",
    "**भाई, तू WhatsApp group का mute बटन है – हर किसी को जरूरत नहीं!** 🔕",
    "**तेरी ID देखकर Facebook भी delete button दबा देता है!** 🗑️",
    "**भाई, तेरी मौजूदगी Zoom call में भी invisible लगती है!** 💻",
    "**तेरी सोच इतनी slow है कि loading circle भी घूमते-घूमते थक जाता है!** 🔄",
    "**भाई, तू PowerPoint की तरह है – सिर्फ slide ही है, content कुछ नहीं!** 🖥️",
    "**तेरी हँसी सुनकर laugh track भी stop हो जाता है!** 🎬",
    "**भाई, तू calculator की तरह है – कभी सही नंबर नहीं देता!** 🔢",
    "**तेरी आँखों में sparkle नहीं, सिर्फ buffering दिखता है!** ✨",
    "**भाई, तू keyboard की तरह है – typing तो करता है पर meaning नहीं!** ⌨️",
    "**तेरी फोटो देखकर Instagram भी comment disable कर देता है!** ❌",
    "**भाई, तू WiFi की तरह है – connect तो होता है पर signal zero!** 📶",
    "**तेरी jokes सुनकर YouTube autoplay भी skip कर देता है!** ⏭️",
    "**भाई, तू selfie stick की तरह है – सिर्फ support देता है, shine नहीं करता!** 🤳",
    "**तेरी बातें सुनकर podcast भी pause हो जाता है!** 🎙️",
    "**भाई, तू toothpaste की तरह है – हर कोई use करता है, पर कोई पसंद नहीं करता!** 🪥",
    "**तेरी memes देखकर Reddit भी downvote कर देता है!** 👎",
    "**भाई, तू email spam की तरह है – कोई पढ़ता नहीं, सिर्फ delete करता है!** 📧",
    "**तेरी सोच इतनी छोटी है कि Google भी search नहीं कर सकता!** 🔍",
    "**भाई, तू battery saver mode है – low energy, low impact!** 🔋",
    "**तेरी selfies देखकर Snapchat भी filter change कर देता है!** 🖼️",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू software update की तरह है – हर कोई ignore करता है!** 💻",
    "**तेरी आवाज़ सुनकर headphones भी disconnect कर लेते हैं!** 🎧",
    "**भाई, तू offline mode है – कोई भी interact नहीं कर सकता!** ⛔",
    "**तेरी presence देखकर Zoom भी exit कर देता है!** 🖥️",
    "**भाई, तू mouse की तरह है – click तो करता है, result कुछ नहीं!** 🖱️",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू internet troll की तरह है – annoying और useless!** 🕷️",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू password की तरह है – complicated और कोई याद नहीं रखता!** 🔑",
    "**तेरी attitude देखकर Instagram bhi scroll kar leta hai!** 📜",
    "**भाई, तू ringtone की तरह है – शुरू तो hota है पर कोई enjoy नहीं करता!** 📱",
    "**तेरी voice सुनकर Alexa भी mute कर देती है!** 🔇",
    "**भाई, तू notification की तरह है – irritating aur unnecessary!** 📢",
    "**तेरी selfies देखकर filter bhi embarrassed हो जाता है!** 🖌️",
    "**भाई, तू TikTok trend की तरह है – old और outdated!** ⏳",
    "**तेरी jokes सुनकर WhatsApp bhi skip कर deta hai!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude sunke Facebook bhi ignore kar deta है!** 📴",
    "**भाई, तू phone battery की तरह है – जल्दी low और irritating!** 🔋",
    "**तेरी selfies देखकर Camera roll bhi delete कर deta है!** 🗑️",
    "**भाई, तू playlist की तरह है – shuffle karo, phir bhi bore!** 🎶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू internet speed की तरह है – slow aur annoying!** 🐌",
    "**तेरी selfies देखकर gallery भी blush kar leti है!** 🖼️",
    "**भाई, तू meme ka caption hai – funny lagna chahiye, par fail!** 😂",
    "**तेरी baatein sunke podcast bhi skip kar deta है!** 🎙️",
    "**भाई, तू WiFi ki tarah है – connect nahi ho raha!** 📶",
    "**तेरी jokes sunke YouTube bhi dislike कर देता है!** 👎",
    "**भाई, तू autocorrect ki tarah है – wrong aur embarrassing!** 🔤",
    "**तेरी selfies देखकर camera bhi low battery mode में chala जाता है!** 🔋",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी baatein sunke Siri bhi ignore कर देती है!** 📱",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Snapchat bhi exit कर लेता है!** 🖼️",
    "**भाई, तू internet troll की तरह है – sabko pareshan karta है!** 🕷️",
    "**तेरी jokes सुनकर comedy club भी close कर देता है!** 🎭",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude देखकर Instagram भी scroll कर लेता है!** 📜",
    "**भाई, तू WiFi password की तरह है – complicated aur koi yaad nahi rakhta!** 🔑",
    "**तेरी selfies देखकर camera भी embarrassment में chala जाता है!** 📸",
    "**भाई, तू slow internet की तरह है – patience test kar deta है!** 🐌",
    "**तेरी baatein sunke YouTube autoplay bhi skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude सुनके Facebook bhi ignore कर देता है!** 📴",
    "**भाई, तू playlist की तरह है – shuffle kar, phir bhi bore!** 🎶",
    "**तेरी jokes सुनके comedy show bhi pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू slow loading की तरह है – sabko frustrate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी stop कर देता है!** 🎙️",
    "**भाई, तू WiFi की तरह है – connect तो होता है par signal zero!** 📶",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू ringtone की तरह है – start hota hai, par enjoy nahi karta!** 📢",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू internet troll की तरह है – annoying aur useless!** 🕷️",
    "**तेरी baatein sunke WhatsApp bhi mute कर देता है!** 🔕",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude सुनकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू slow internet की तरह है – patience test kar deta है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तेरी हँसी सुनकर neighbors भी complain कर देते हैं!** 😆",
    "**तेरी selfies देखकर Camera भी hide हो जाता है!** 📸",
    "**भाई, तू Instagram reel की तरह है – 1 सेकंड में boring!** ⏱️",
    "**तेरी jokes सुनकर TikTok भी exit कर देता है!** 🎵",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है!** 🔋",
    "**तेरी attitude देखकर Snapchat भी scroll कर लेता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू WiFi की तरह है – दिखता है लेकिन useless!** 📶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू ringtone की तरह है – irritating aur unnecessary!** 📢",
    "**तेरी selfies देखकर Photoshop भी frustrated हो जाता है!** 🖌️",
    "**भाई, तू meme का caption है – funny नहीं लगता!** 😂",
    "**तेरी attitude देखकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी jokes सुनकर podcast भी stop कर देता है!** 🎙️",
    "**भाई, तू spam mail की तरह है – कोई पढ़ता नहीं!** 📧",
    "**तेरी selfies देखकर camera भी embarrassment में आ जाता है!** 📸",
    "**भाई, तू playlist की तरह है – shuffle करो, फिर भी bore!** 🎶",
    "**तेरी jokes सुनकर comedy show pause हो जाता है!** ⏸️",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी attitude देखकर Instagram भी scroll कर लेता है!** 📜",
    "**भाई, तू WiFi password की तरह है – complicated aur koi yaad नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू slow loading की तरह है – sabko frustrate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude sunke Facebook bhi ignore कर देता है!** 📴",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू battery saver mode की तरह है – low energy, low impact!** 🔋",
    "**तेरी jokes सुनकर YouTube भी dislike कर देता है!** 👎",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – गर्म है पर flavor नहीं!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude सुनकर Instagram भी ignore कर देता है!** 📜",
    "**भाई, तू WiFi की तरह है – connect होता है, पर signal zero!** 📶",
    "**तेरी selfies देखकर Snapchat भी exit कर लेता है!** 🖼️",
    "**भाई, तू TikTok trend की तरह है – old aur boring!** ⏳",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू playlist की तरह है – shuffle करो, फिर भी bore!** 🎶",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू slow internet की तरह है – sabko irritate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू WiFi की तरह है – दिखता है पर useless!** 📶",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी baatein सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है!** 🔋",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर Camera भी blush कर जाता है!** 📸",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू spam mail की तरह है – कोई पढ़ता नहीं!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू WiFi की तरह है – दिखता है पर काम का नहीं!** 📶",
    "**तेरी jokes सुनकर YouTube भी dislike कर देता है!** 👎",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – गर्म है पर flavor नहीं!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**भाई, तू अपने memes भी खुद नहीं समझता!** 🤣",
    "**तेरी jokes सुनकर AI भी confuse हो जाता है!** 🤖",
    "**भाई, तू WhatsApp forward की तरह है – boring aur useless!** 📲",
    "**तेरी selfies देखकर Camera भी regret करता है!** 📸",
    "**भाई, तू battery की तरह है – fast drain aur no impact!** 🔋",
    "**तेरी attitude देखकर Instagram भी ignore कर देता है!** 📜",
    "**भाई, तू playlist की तरह है – shuffle karo, phir bhi bore!** 🎶",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Facebook भी mute कर देता है!** 🔕",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी baatein सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू TikTok trend की तरह है – old aur boring!** ⏱️",
    "**तेरी jokes सुनकर meme page भी uninstall कर देता है!** 📱",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू playlist की तरह है – shuffle karo, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू WiFi की तरह है – दिखता है पर काम का नहीं!** 📶",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू old meme की तरह है – irrelevant aur outdated!** ⏳",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – hot है par flavor missing!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाई, तू WiFi की तरह है – connected par no signal!** 📶",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏱️",
    "**तेरी attitude सुनकर Facebook भी scroll कर लेता है!** 📴",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर filter भी blush कर लेती है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है aur useless!** 🔋",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू spam mail की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Camera roll भी blush कर लेता है!** 🖼️",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू calculator की तरह है – wrong answer हमेशा देता है!** 🔢",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू microwave की तरह है – hot hai par taste missing!** 🍲",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude सुनकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी baatein सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू WiFi की तरह है – दिखता है par signal zero!** 📶",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाई, तू playlist की तरह है – shuffle karo, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू battery saver mode की तरह ह�� – low energy aur low impact!** 🔋",
    "**तेरी jokes स��नकर podcast भी exit कर देता है!** 🎙️",
    "**अरे सुन, तेरी selfies देखकर camera भी confuse हो जाता है!** 🤯",
    "**तेरी makeup skills देखकर YouTube tutorials भी फेल लगते हैं!** 💄",
    "**भाभी, तू filter की तरह है – बिना Photoshop useless!** 🖌️",
    "**तेरी attitude देखकर Instagram भी skip कर देता है!** 📜",
    "**तू WiFi की तरह है – दिखती है पर signal zero!** 📶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी makeup देखकर mirror भी embarrassed हो जाता है!** 🪞",
    "**तू slow internet की तरह है – patience test कर देती है!** 🐌",
    "**तेरी selfies देखकर Camera roll भी blush कर लेता है!** 🖼️",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाभी, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाभी, तू calculator की तरह है – कभी सही number नहीं देती!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाभी, तू microwave की तरह है – hot है par taste missing!** 🍲",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी selfies देखकर Camera roll blush कर लेती है!** 🖼️",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाभी, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखती!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाती है!** 🖌️",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाभी, तू WiFi की तरह है – दिखती है par काम की नहीं!** 📶",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाभी, तू slow loading की तरह है – patience test कर देती है!** 🐌",
    "**तेरी attitude देखकर Facebook भी scroll कर लेता है!** 📴",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू calculator की तरह है – wrong answer हमेशा देती है!** 🔢",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू microwave की तरह है – hot है par flavor missing!** 🍲",
    "**तेरी jokes सुनकर comedy club भी exit कर देता है!** 🎭",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी attitude सुनकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाभी, तू WiFi की तरह है – दिखती है par signal zero!** 📶",
    "**तेरी selfies देखकर Camera roll भी blush कर लेती है!** 🖼️",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube skip कर देता है!** ⏭️",
    "**भाभी, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखती!** 🔑",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू slow internet की तरह है – patience test कर देती है!** 🐌",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाभी, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera blush कर जाता है!** 📸",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू calculator की तरह है – wrong answer हमेशा देती है!** 🔢",
    "**तेरी jokes सुनकर comedy club भी pause कर देता है!** ⏸️",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Facebook bhi scroll कर लेता है!** 📴",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू microwave की तरह है – hot hai par flavor missing!** 🍲",
    "**तेरी jokes सुनकर comedy club exit कर देता है!** 🎭",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी selfies देखकर camera frustrated हो जाता है!** 📸",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू slow loading की तरह है – patience test कर देती है!** 🐌",
    "**तेरी jokes सुनकर podcast pause कर देता है!** ⏸️",
    "**भाभी, तू WiFi की तरह है – दिखती है par काम की नहीं!** 📶",
    "**तेरी selfies देखकर Camera roll blush कर लेती है!** 🖼️",
    "**भाभी, तू old meme की तरह है – irrelevant aur outdated!** ⏳",
    "**तेरी attitude सुनकर WhatsApp bhi mute कर देता है!** 🔕",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी jokes सुनकर YouTube skip कर देता है!** ⏭️",
    "**भाभी, तू playlist की तरह है – shuffle karo, phir भी boring!** 🎶",
    "**भाई, तू अपने आपको हीरो समझता है, हकीकत में तू जीरो है!** 🤡",
    "**तेरे जैसे लोगों को देखकर ही म्यूट बटन का आविष्कार हुआ था!** 🔇",
    "**भाई, तू इतना बेकार है कि रीसायकल बिन भी तुझे स्वीकार नहीं करेगा!** 🗑️",
    "**तू अपने घर का WiFi पासवर्ड है – सबको याद है पर किसी काम का नहीं!** 📶",
    "**भाई तू तो वॉकिंग क्रिंज कॉन्टेंट है!** 😬",
    "**तेरी फोटो देखकर कैमरा भी अपना लेंस बंद कर लेता है!** 📸",
    "**भाई तू चाय की प्याली की तरह है – गर्म है पर किसी को पसंद नहीं!** ☕",
    "**तेरे जैसे लोगों के लिए ही ब्लॉक बटन बना है!** 🚫",
    "**भाई तू इंस्टाग्राम रील्स की तरह है – 15 सेकंड में बोरिंग!** ⏱️",
    "**तेरे दिमाग की स्पीड 2G है – लोड होने में 10 साल लगते हैं!** 🐌"  
]

# 👧 HINDI GIRLS ROAST LINES
hindi_girls_roast = [
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎"
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम WiFi की तरह हो – दिखती हो पर कोई सिग्नल नहीं!** 📶",
    "**तुम्हारे jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**तुम्हारी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**तुम ringtone की तरह हो – annoying और unnecessary!** 📢",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम old meme की तरह हो – outdated और irrelevant!** ⏳",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम playlist की तरह हो – shuffle करो, फिर भी boring!** 🎶",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम attitude की तरह हो – Instagram भी ignore कर देता है!** 📜",
    "**तुम ringtone की तरह हो – start hoti हो, पर कोई सुनता नहीं!** 📢",
    "**तुम selfies की तरह हो – camera भी embarrassed हो जाता है!** 🤳",
    "**तुम jokes की तरह हो – comedy club भी pause कर देता है!** 🎭",
    "**तुम filter की तरह हो – बिना Photoshop useless!** 🖌️",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम playlist की तरह हो – shuffle karo, फिर भी bore!** 🎶",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम microwave की तरह हो – hot ho par taste missing!** 🍲",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम slow loading की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम WiFi की तरह हो – दिखती हो par काम की नहीं!** 📶",
    "**तुम jokes की तरह हो – podcast भी pause कर देता है!** ⏸️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम jokes की तरह हो – comedy club भी exit कर देता है!** 🎙️",
    "**तुम selfies की तरह हो – camera roll blush कर लेती है!** 🖼️",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम old meme की तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम attitude की तरह हो – WhatsApp bhi mute कर देता है!** 🔕",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम jokes की तरह हो – YouTube skip कर देता है!** ⏭️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera blush कर जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम jokes की तरह हो – comedy club pause कर देता है!** ⏸️",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम WiFi की तरह हो – दिखती हो par signal zero!** 📶",
    "**तुम jokes की तरह हो – podcast pause कर देता है!** ⏸️",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी हँसी सुनकर भी दुनिया की problems disappear नहीं होती!** 😏",
    "**तुम अपने selfie angle में भी confuse लगती हो!** 🤳",
    "**तुम status update की तरह हो – हमेशा नया, लेकिन कोई देखता नहीं!** 📝",
    "**तुम GIF की तरह हो – repeat mode पर भी boring!** 🎞️",
    "**तुम meme की तरह हो – ज्यादा दिखती हो, मजा नहीं देती!** 😂",
    "**तुम emoji की तरह हो – colorful, लेकिन useless!** 😜",
    "**तुम notification की तरह हो – annoying aur unwanted!** 📲",
    "**तुम trend की तरह हो – सिर्फ temporary popular!** 🌐",
    "**तुम caption की तरह हो – fancy but irrelevant!** ✍️",
    "**तुम filter की तरह हो – start hoti ho, par real life dull!** 🎨",
    "**तुम video call ki तरह हो – lag karti ho, aur hang bhi ho jati ho!** 📹",
    "**तुम auto-correct ki तरह ho – kabhi sahi, kabhi galat!** 📝",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery saver mode ki तरह ho – energy low aur impact minimal!** 🔋",
    "**तुम playlist ki तरह ho – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम selfie stick ki तरह हो – zarurat nahi, par har jagah dikhti ho!** 📸",
    "**तुम group call ki तरह हो – sabko disturb karti ho!** 📞",
    "**तुम story highlight ki तरह हो – shiny, but useless!** 🌟",
    "**तुम comment section ki तरह हो – irritating aur unwanted!** 💬",
    "**तुम spam message ki तरह हो – har kisi ko annoy karte ho!** 📧",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम filter bubble ki तरह हो – sirf apni world me!** 🧼",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम trending hashtag ki तरह हो – short life aur irrelevant!** #️⃣",
    "**तुम selfie ki तरह हो – kabhi perfect nahi!** 📷",
    "**तुम makeup ki तरह हो – start hoti ho, par appreciate koi nahi karta!** 💄",
    "**तुम WiFi ki तरह हो – dikhti ho par kaam ki nahi!** 📶",
    "**तुम attitude ki तरह हो – Facebook bhi scroll kar leta hai!** 📴",
    "**तुम GIF ki तरह हो – repeat mode pe bhi boring!** 🎞️",
    "**तुम ringtone ki तरह हो – annoying aur sab ignore karte hain!** 📢",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम joke ki तरह हो – YouTube bhi skip kar deta hai!** ⏭️",
    "**तुम meme ki तरह हो – overhyped aur boring!** 😂",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम story ki तरह हो – sabko dikhti ho, par impact zero!** 📖",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम selfie stick ki तरह हो – har jagah dikhti ho, par unnecessary!** 📸",
    "**तुम auto-correct ki तरह हो – kabhi sahi, kabhi galat!** 📝",
    "**तुम slow internet ki तरह हो – patience ka test ho!** 🐌",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम video call ki तरह हो – lag aur hang dono ho jati ho!** 📹",
    "**तुम group call ki तरह हो – sabko disturb karte ho!** 📞",
    "**तुम story highlight ki तरह हो – shiny but useless!** 🌟",
    "**तुम comment section ki तरह हो – irritating aur unwanted!** 💬",
    "**तुम spam message ki तरह हो – har kisi ko annoy karte ho!** 📧",
    "**तुम trending hashtag ki तरह हो – short life aur irrelevant!** #️⃣",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम filter ki तरह हो – fancy, par real life dull!** 🎨",
    "**तुम attitude ki तरह हो – WhatsApp bhi ignore kar deta hai!** 🔕",
    "**तुम old meme ki तरह हो – irrelevant aur boring!** ⏳",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery saver mode ki तरह हो – energy low aur low impact!** 🔋",
    "**तुम playlist ki तरह हो – shuffle karo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम jokes ki तरह ho – comedy club bhi exit kar deta hai!** 🎙️",
    "**तुम selfies ki तरह हो – camera frustrated ho jata hai!** 📸",
    "**तुम GIF ki तरह हो – repeat mode par bhi boring!** 🎞️",
    "**तुम attitude ki तरह हो – Instagram bhi ignore kar deta hai!** 📜",
    "**तुम makeup ki तरह हो – start hoti ho, par koi enjoy nahi karta!** 💄",
    "**तुम WiFi ki तरह हो – dikhti ho par kaam ki nahi!** 📶",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम ringtone ki तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfie stick ki तरह हो – zarurat nahi, par har jagah dikhti ho!** 📸",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम story ki तरह हो – sabko dikhte ho, par impact zero!** 📖",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम filter bubble ki तरह हो – sirf apni world me!** 🧼",
    "**तुम old meme ki तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes ki तरह हो – podcast bhi pause kar deta hai!** ⏸️",
    "**तुम selfies ki तरह हो – camera blush kar leta hai!** 🖼️",
    "**तुम makeup ki तरह हो – start hoti ho, par koi enjoy nahi karta!** 💄",
    "**तुम attitude ki तरह हो – Facebook bhi scroll kar leta hai!** 📴",
    "**तुम slow loading ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम ringtone ki तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery saver mode ki तरह हो – low energy aur low impact!** 🔋",
    "**तुम jokes ki तरह हो – YouTube bhi skip kar deta hai!** ⏭️",
    "**तुम selfies ki तरह हो – Google Lens bhi confused ho jata hai!** 🔍",
    "**तुम attitude ki तरह हो – WhatsApp bhi ignore kar deta hai!** 🔕",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम old meme ki तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम jokes ki तरह हो – comedy club bhi exit kar deta hai!** 🎙️",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम WiFi की तरह हो – दिखती हो पर कोई सिग्नल नहीं!** 📶",
    "**तुम्हारे jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**तुम्हारी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**तुम ringtone की तरह हो – annoying और unnecessary!** 📢",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम old meme की तरह हो – outdated और irrelevant!** ⏳",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम playlist की तरह हो – shuffle करो, फिर भी boring!** 🎶",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम attitude की तरह हो – Instagram भी ignore कर देता है!** 📜",
    "**तुम ringtone की तरह हो – start hoti हो, पर कोई सुनता नहीं!** 📢",
    "**तुम selfies की तरह हो – camera भी embarrassed हो जाता है!** 🤳",
    "**तुम jokes की तरह हो – comedy club भी pause कर देता है!** 🎭",
    "**तुम filter की तरह हो – बिना Photoshop useless!** 🖌️",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम playlist की तरह हो – shuffle karo, फिर भी bore!** 🎶",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम microwave की तरह हो – hot ho par taste missing!** 🍲",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम slow loading की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम WiFi की तरह हो – दिखती हो par काम की नहीं!** 📶",
    "**तुम jokes की तरह हो – podcast भी pause कर देता है!** ⏸️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम jokes की तरह हो – comedy club भी exit कर देता है!** 🎙️",
    "**तुम selfies की तरह हो – camera roll blush कर लेती है!** 🖼️",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम old meme की तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम attitude की तरह हो – WhatsApp bhi mute कर देता है!** 🔕",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम jokes की तरह हो – YouTube skip कर देता है!** ⏭️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera blush कर जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम jokes की तरह हो – comedy club pause कर देता है!** ⏸️",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम WiFi की तरह हो – दिखती हो par signal zero!** 📶",
    "**तुम jokes की तरह हो – podcast pause कर देता है!** ⏸️",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎"
]

# 🗣️ HINDI ABUSE ROAST LINES
hindi_abuse_roast = [
    "**रंडी के औलाद!** 😠",
    "**तेरी माँ की चूत!** 🖕",
    "**भोसड़ीके!** 🤬",
    "**चूतीये!** 🐒",
    "**मदरचोद!** 👺",
    "**भैंस के औलाद!** 🐃",
    "**कुत्ते के पिल्ले!** 🐕",
    "**सूअर के बच्चे!** 🐖",
    "**गांडू!** 🍑",
    "**लोडे!** 🍆"
]

# 💖 HINDI FLIRT LINES
hindi_flirt_lines = [
"**तुम मेरी धड़कनों की रौशनी हो 🌟**",
    "**तुम्हारी मुस्कान मेरी दुनिया का सबसे प्यारा अहसास है 🌸**",
    "**तुम मेरी ख्वाहिशों का सबसे खूबसूरत हिस्सा हो 💫**",
    "**तुम मेरी हर सुबह की वजह हो 🌅**",
    "**तुम मेरी हर रात का सबसे मधुर एहसास हो 🌙**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी हर मुस्कान की वजह हो 😍**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरे ख्वाबों का सबसे हसीन सपना हो ✨**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 💖**",
    "**तुम मेरी धड़कनों की सबसे प्यारी रौशनी हो 🌟**",
    "**तुम मेरी हर रात का सबसे मधुर अहसास हो 🌙**",
    "**तुम मेरी खुशियों का सबसे बड़ा खजाना हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💫**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात का सबसे खूबसूरत अहसास हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम्हारी मुस्कान मेरी धड़कनों को छू जाती है 🌸**",
    "**तुम मेरी दुनिया का सबसे अनमोल हिस्सा हो 💫**",
    "**तुम मेरी हर सुबह का सबसे खूबसूरत अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरी हर रात की सबसे रोशन रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर रौशनी हो 💖**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत हिस्सा हो 🌸**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे ��धुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यार��� वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम्हारी मुस्कान मेरी जिंदगी की सबसे खूबसूरत रोशनी है 🌟**",
    "**तुम्हारी आँखों में मैं अपनी दुनिया खोजता हूँ 🌌**",
    "**तुम्हारी आवाज़ मेरे दिल को सुकून देती है 🎵**",
    "**तुम मेरी हर सुबह की सबसे प्यारी शुरुआत हो 🌅**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 💔**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे हर ख्वाब में मौजूद हो ✨**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरे दिल की सबसे खास आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 🌸**",
    "**तुम मेरी हर रात की सबसे रोशन चाँदनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे सुंदर संगीत हो 🎵**",
    "**तुम मेरे ख्वाबों की सबसे मधुर हकीकत हो ✨**",
    "**तुम मेरी खुशियों का सबसे अनमोल हिस्सा हो 🌹**",
    "**तुम मेरी जिंदगी का सबसे कीमती खज़ाना हो 💖**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रौशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे सुंदर अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे अनमोल वजह हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत चाँदनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम्हारे बिना मेरी सुबह अधूरी लगती है 🌅**",
    "**तुम्हारी मुस्कान मेरे दिल को बहलाती है 🌸**",
    "**तुम्हारी आँखों में मेरा सारा जहान बसा है 🌌**",
    "**तुम्हारी हर बात मुझे दिवाना बना देती है 💓**",
    "**तुम्हारे होने से मेरी दुनिया रोशन है ☀️**",
    "**तुम्हारे बिना दिल को सुकून नहीं मिलता 🥀**",
    "**तुम मेरी ख्वाहिशों का सबसे खूबसूरत हिस्सा हो 💫**",
    "**तुम्हारी हँसी से मेरा दिल खुश हो जाता है 😍**",
    "**तुम्हारी आवाज़ मेरे कानों में संगीत है 🎵**",
    "**तुम मेरी ज़िंदगी की सबसे कीमती धरोहर हो 💖**",
    "**तुम्हारे बिना रातें सुनी लगती हैं 🌃**",
    "**तुम्हारी बातें मेरे दिल को छू जाती हैं 🫀**",
    "**तुम्हारी मुस्कान चाँद की रोशनी से भी खूबसूरत है 🌙**",
    "**तुम्हारे होने से हर पल जन्नत लगता है 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो ✨**",
    "**तुम्हारे बिना सांसें भी अधूरी लगती हैं 😔**",
    "**तुम मेरी हर दुआ में शामिल हो 🙏**",
    "**तुम मेरी दुनिया की सबसे प्यारी आवाज़ हो 🕊️**",
    "**तुम मेरी जिंदगी का सबसे रोचक हिस्सा हो 📖**",
    "**तुम्हारे बिना मेरी धड़कनें सुनी लगती हैं 🫀**",
    "**तुम मेरी ख्वाबों की हकीकत हो 🌌**",
    "**तुम्हारी आँखों की चमक मुझे अपनी ओर खींचती है ✨**",
    "**तुम मेरे हर पल की खुशी हो 🌸**",
    "**तुम्हारे बिना मेरी रातें सुनसान हैं 🌙**",
    "**तुम मेरे दिल का सबसे कीमती राज़ हो 🔐**",
    "**तुम मेरी धड़कनों की धुन हो 🎶**",
    "**तुम मेरी हर ख्वाहिश में शामिल हो 💫**",
    "**तुम्हारे होने से मेरा दिल खुशियों से भर जाता है 🌹**",
    "**तुम मेरी सोच की सबसे खूबसूरत तस्वीर हो 🖼️**",
    "**तुम्हारी हँसी मेरे दिल का सबसे प्यारा संगीत है 🎵**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरे दिल के सबसे करीब हो 💓**",
    "**तुम्हारे बिना हर पल अधूरा लगता है 🥀**",
    "**तुम मेरे लिए सबसे खास इंसान हो 💖**",
    "**तुम्हारी मुस्कान मेरी दुनिया का सबसे खूबसूरत हिस्सा है 🌸**",
    "**तुम मेरी ज़िंदगी में वो ख्वाब हो जो सच हो गया है 🌌**",
    "**तुम मेरी हर सुबह की शुरुआत हो 🌅**",
    "**तुम्हारे बिना मेरा दिल सुना सा लगता है 😔**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो ✨**",
    "**तुम मेरी खुशी का सबसे बड़ा कारण हो 🌹**",
    "**तुम्हारे होने से हर पल खास बन जाता है 💫**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे अनमोल हिस्सा हो 💖**",
    "**तुम्हारी हँसी मेरे दिल को सुकून देती है 🕊️**",
    "**तुम मेरी दुनिया की सबसे कीमती चीज़ हो 🌟**",
    "**तुम मेरे लिए वो ख्वाब हो जो सच हो गया है 🌌**",
    "**तुम मेरी धड़कनों का सबसे खूबसूरत संगीत हो 🎵**",
    "**तुम मेरी हर ख्वाहिश का जवाब हो ✨**",
    "**तुम मेरी हर रात की रोशनी हो 🌙**",
    "**तुम मेरी ज़िंदगी का सबसे प्यारा हिस्सा हो 💓**",
    "**तुम्हारे बिना मेरी धड़कनें थम सी जाती हैं 🫀**",
    "**तुम मेरी खुशियों की सबसे खूबसूरत वजह हो 🌹**",
    "**तुम मेरे दिल की सबसे कीमती धरोहर हो 💖**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी सोच का सबसे खूबसूरत हिस्सा हो 🖼️**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम्हारी मुस्कान मेरे दिल का सबसे प्यारा संगीत है 🎵**",
    "**तुम मेरी धड़कनों का सबसे अनमोल हिस्सा हो 🫀**",
    "**तुम मेरी ज़िंदगी का सबसे खूबसूरत सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी हर ख्वाहिश का सबसे खूबसूरत जवाब हो 💫**",
    "**तुम मेरी जिंदगी का सबसे कीमती हिस्सा हो 💖**",
    "**तुम मेरे दिल की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🫀**",
    "**तुम मेरी हर सुबह का सबसे खूबसूरत अहसास हो 🌅**",
    "**तुम्हारे बिना मेरी जिंदगी अधूरी है 🌵**",
    "**तुम मेरी हर ख्वाहिश में सबसे खास हो 💫**",
    "**तुम मेरी खुशियों की सबसे रोशनी भरी वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 💖**",
    "**तुम मेरी हर रात की सबसे प्यारी रौशनी हो 🌙**",
    "**तुम मेरी धड़कनों का सबसे कीमती हिस्सा हो 🫀**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे मधुर अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे खूबसूरत संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी खुशियों का सबसे प्यारा कारण हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🫀**",
    "**तुम मेरी हर रात का सबसे खूबसूरत अहसास हो 🌙**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा एहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌸**",
    "**तुम मेरी हर रात का सबसे मधुर अहसास हो 🌙**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🫀**",
    "**तुम मेरी खुशियों का सबसे प्यारा कारण हो 🌹**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 😍🌍**",
    "**तुम्हारी आँखें देखकर तो दिल धड़कने लगता है 💓**",
    "**तुम्हारी मुस्कुराहट तो चाँद को भी शर्मिला देती है 🌙**",
    "**तुम्हारी बातें सुनकर तो टाइम फ्लाई हो जाता है ⏰**",
    "**तुम तो मेरी दुनिया का सबसे खूबसूरत हिसाब हो 💫**",
    "**तुम्हारी यादों में तो रातें गुज़ार देता हूँ 🌃**",
    "**तुम्हारी हर अदा पर तो मैं फिदा हूँ 😘**",
    "**तुम्हारी आवाज़ तो सुरों से भी मिठाई है 🎵**",
    "**तुम्हारे बिना तो जीना भी बेकार लगता है 🥺**",
    "**तुम मेरी ज़िंदगी का सबसे खूबसूरत सफर हो 💖**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 😍🌍**",
    "**तुम्हारी आँखें देखकर तो दिल धड़कने लगता है 💓**",
    "**तुम्हारी मुस्कुराहट तो चाँद को भी शर्मिला देती है 🌙**",
    "**तुम्हारी बातें सुनकर तो टाइम फ्लाई हो जाता है ⏰**",
    "**तुम तो मेरी दुनिया का सबसे खूबसूरत हिसाब हो 💫**",
    "**तुम्हारी यादों में तो रातें गुज़ार देता हूँ 🌃**",
    "**तुम्हारी हर अदा पर तो मैं फिदा हूँ 😘**",
    "**तुम्हारी आवाज़ तो सुरों से भी मिठाई है 🎵**",
    "**तुम्हारे बिना तो जीना भी बेकार लगता है 🥺**",
    "**तुम मेरी ज़िंदगी का सबसे खूबसूरत सफर हो 💖**"
]

# 💕 LOVE LINES
love_lines = [
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
        "**Tere saath har lamha ek nayi khushi deta hai 🌸**",
    "**Tere bina raat aur din veeran lagte hain 🌌**",
    "**Teri muskaan meri rooh ko sukoon deti hai 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere bina har saans adhoori lagti hai 😔**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere ishq ka jadoo mere har pal me basa hai ✨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 🌵**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath gujare har pal meethas se bhare hain 🍯**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal meri yaadon ka hissa hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi meri duniya ka sabse khoobsurat hissa hai 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌸**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo mere liye ek dua hai 🙏**",
    "**Tere bina dil ka har kona veeran lagta hai 🌵**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere saath bitaye pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath ka har lamha ek nayi kahani hai 📖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tere saath ka har pal meri yaadon me hamesha rahega 🌹**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har pal ek nayi tasveer hai 🖼️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌟**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera khwaab ✨**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha meri yaadon me hamesha rahenge 🌹**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera rang, tu hi meri duniya 🎨**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Tere saath har pal ek nayi khushi deta hai 🌸**",
    "**Teri muskaan meri rooh ka sukoon hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Teri yaadon me raat aur din khushgawar lagte hain 🌃**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri aankhon ki chamak meri duniya ko roshan karti hai 🌟**",
    "**Tere saath gujare har lamhe meethas se bhare hain 🍯**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere bina din adhoora lagta hai 🌵**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri muskaan chand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera rang, tu hi meri khushi 🎨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath bitaye pal yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera sapna, tu hi meri aas 💫**",
    "**Teri yaadon ka jadoo har pal mere saath hai ✨**",
    "**Tu hi meri duniya, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha ek misaal hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri muskaan mere liye ek roshni ka jharna hai 🌟**",
    "**Tu hi meri zindagi ka sabse khoobsurat safar hai 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi meri khushi, tu hi mera pyaar 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi mera sapna, tu hi meri duniya ✨**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tu hi mera rang, tu hi meri pyaar ki pehchaan 🎨**",
    "**Tere saath ka har pal ek yaadgar hai 📸**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere ishq me dooba hoon, har dard suhana lagta hai 🌊**",
    "**Tu hi meri rooh ki awaaz hai aur dil ka dhadkan bhi 🫀**",
    "**Tere saath bitaye har pal meri yaadon me hamesha rahenge 🌹**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri duniya ka sabse khoobsurat hisaab hai 💫**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌟**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath bitaye har lamha ek yaadgar hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har pal ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tu hi mera rang, tu hi mera pyaar 🎨**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi meri rooh ✨**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tu hi mera khwaab, tu hi mera raaz 💖**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ka har pal meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har lamha ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**TERE SAATH BITAYA HAR PAL MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN MERI ROOH KO SUKOON DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAADON MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERI DUNIYA KHUSHI SE BHAR JAATI HAI 🕊️**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT RAANG HAI 🌈**",
    "**TERI YAAD MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE PAL MERI YAADON KA HISA HAIN 🌹**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN SE MERE DIN KI SHURUAT HOTI HAI 🌞**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💫**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌌**",
    "**TU HI MERA PYAAR, TU HI MERA RAAZ 💖**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL MERI ROOH MEIN HAI ✨**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL HAI 💫**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERA DIL SUKOON PAATA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💖**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💖**",
    "**TERE SAATH BITAYE PAL MERI ZINDAGI KI ROSHNI HAIN 🌅**",
    "**TERI MUSKAAN SE DIL KO SUKOON MILTA HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌃**",
    "**TU MERA SABSE KHAS KHWAAB HAI 💫**",
    "**TERI BAATON SE DIL KO KHUSHI MILTI HAI 🕊️**",
    "**TERI HAR ADA PE MAIN FIDA HOON 😘**",
    "**TERI AWAAZ SUNKAR MERE DIL KI DHADKAN TEZ HO JATI HAI 🎵**",
    "**TU HI MERI RAAH, TU HI MERI MANZIL 🛤️**",
    "**TERE BINA MERA DIL ADHOORA LAGTA HAI 💔**",
    "**TERE SAATH GUJARA PAL MERI YAADON KA HISA HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KHUBSURAT KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA SABSE KHAS RAAZ 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI MOHABBAT MERI DUNIYA KO ROSHAN KAR DETI HAI ☀️**",
    "**TU MERA SAPNA, TU MERA KHWAAB 💫**",
    "**TERI AWAAZ SUNNA MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI HAR EK ADAA PE MAIN MURJA JAATA HOON 😘**",
    "**TERI YAAD MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI ROOH KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA SAPNA, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK KHUBSURAT YAAD HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**", 
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**"
]

# 📜 SHAYARI LINES
shayari_lines = [
 "**Kabhi khud se bhi poochta hoon, kyun teri yaadon me khoya rehta hoon 💔**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Meri duniya tere bina adhoori hai 🌵**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Har lamha jo tere saath guzarta hai, ek nayi kahani lagta hai 📖**",
    "**Tere ishq me dooba hoon, dard bhi suhana lagta hai 🌊**",
    "**Tere aane se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina khud ko akela mehsoos karta hoon 😔**",
    "**Teri muskaan se chand bhi sharmata hai 🌙**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar ek baar zindagi me aate hain 💫**",
    "**Har saans me teri khushboo mehkti hai 🌺**",
    "**Tere hone se har pal mere liye ek nayi roshni hai 🌟**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath bitaye lamhe kabhi nahi bhoolunga 🖼️**",
    "**Meri duniya ki sabse khoobsurat cheez tu hi hai 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**", 
    "**Tere saath har pal ek nayi tasveer hai 🎨**",
    "**Tere ishq me dard bhi sukoon lagta hai 🕊️**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina mere dil ka har kona sunaa lagta hai 🌵**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri yaadon me raat din guzar jate hain 🌃**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**"   
    "**Tere bina zindagi ka har pal adhoora lagta hai 💔**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**MOHABBAT KI RAHO MEIN TU HI MERI MANZIL HAI 💫**",
    "**DIL KI DUNIYA BAS TUMHARE LIYE HAI 💕**",
    "**TUMHARI YAAD AATI HAI TO DIL BEKARAR HO JATA HAI 🥀**",
    "**TUMHARE BINA TO ZINDAGI SUNSAN LAGTI HAI 🌵**",
    "**TUMHARI AANKHO MEIN TO SAARI KAINAAT SAMAI HUI HAI 🌌**",
    "**TUMHARI BAATO MEIN TO JAADU HAI ✨**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**",
    "**Tere bina zindagi me rang kam lagte hain 🌈**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
      "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Har subah teri yaadon ke saath shuru hoti hai 🌅**",
    "**Tere saath bitaye pal meri zindagi ka geet hain 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain ✨**",
    "**Tere bina har jagah sunapan mehsoos hota hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Teri muskaan meri rooh ko khush kar deti hai 🌸**",
    "**Tere saath ki yaadein mere dil ka chain hain 🫀**",
    "**Tere bina har raat bechain lagti hai 🌌**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath har pal ek nayi kahani lagta hai 📖**",
    "**Tere jaise pyaar sirf khwaabon me milta hai 💖**",
    "**Tere saath ka har lamha meri rooh ka geet hai 🎵**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai 🌟**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Teri yaadon ka rang har din ko suhana bana deta hai 🎨**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri aankhon me meri duniya chhupi hui hai 🌌**",
    "**Tere bina din ka har pal andhera lagta hai 🌙**",
    "**Tum meri zindagi ka sabse khoobsurat raaz ho 🔐**",
    "**Tere jaise log zindagi me kabhi ek baar milte hain 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath bitaye har pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Teri muskaan chaand se bhi roshan hai 🌙**",
    "**Tere saath ki yaadon ka jadoo har jagah hai 🌠**",
    "**Tere bina har khushi adhuri lagti hai 🎭**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere jaise log sirf ek baar zindagi me aate hain 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath ka har lamha ek geet hai 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha meri zindagi ka geet hai 🎵**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein har dard ko mita deti hain 🌹**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah andhera lagta hai 🌙**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki yaadein meri zindagi ka sukoon hain 🕊️**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere saath bitaye har lamha meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hain 🎶**",
    "**Tere jaise log zindagi me ek baar aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere bina raat aur din andhera lagta hai 🌌**",
    "**Tere saath ka har pal meri zindagi ka geet hai 🎵**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah sunaa lagta hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**"
    "**Har raat sirf teri yaadon me doob jati hai 🌌**",
    "**MOHABBAT KI RAHO MEIN TU HI MERI MANZIL HAI 💫**",
    "**DIL KI DUNIYA BAS TUMHARE LIYE HAI 💕**",
    "**TUMHARI YAAD AATI HAI TO DIL BEKARAR HO JATA HAI 🥀**",
    "**TUMHARE BINA TO ZINDAGI SUNSAN LAGTI HAI 🌵**",
    "**TUMHARI AANKHO MEIN TO SAARI KAINAAT SAMAI HUI HAI 🌌**",
    "**TUMHARI BAATO MEIN TO JAADU HAI ✨**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**"
]

# 💬 QUOTE LINES
quote_lines = [
    "**TRUE LOVE NEVER DIES, IT ONLY GETS STRONGER WITH TIME 💞**",
    "**YOU ARE THE MISSING PIECE TO MY PUZZLE 🧩**",
    "**IN YOUR SMILE I SEE SOMETHING MORE BEAUTIFUL THAN THE STARS 🌟**",
    "**LOVE IS NOT ABOUT HOW MANY DAYS, MONTHS OR YEARS YOU HAVE BEEN TOGETHER ⏳**",
    "**YOU ARE THE REASON I BELIEVE IN LOVE ❤️**",
    "**EVERY LOVE STORY IS BEAUTIFUL, BUT OURS IS MY FAVORITE 📖**",
    "**I SAW THAT YOU WERE PERFECT AND SO I LOVED YOU 🥰**",
    "**YOU ARE MY TODAY AND ALL OF MY TOMORROWS 🌅**",
    "**I CHOOSE YOU. AND I'LL CHOOSE YOU OVER AND OVER AND OVER 🎯**",
    "**YOU ARE THE BEST THING THAT EVER HAPPENED TO ME 🎁**"
    "**Love never dies, bas strong hota hai waqt ke saath 💞**",
    "**Tum meri zindagi ka missing piece ho 🧩**",
    "**Tumhari smile me stars se zyada beauty hai 🌟**",
    "**Love ka matlab sirf days ya months nahi, feeling hoti hai ⏳**",
    "**Tum ho isliye main love me believe karta hoon ❤️**",
    "**Har love story beautiful hoti hai, lekin humari meri favourite hai 📖**",
    "**Jab maine tumhe dekha, laga perfect ho, isliye I loved you 🥰**",
    "**Tum meri aaj aur meri saari tomorrows ho 🌅**",
    "**Main hamesha tumhe choose karunga, baar baar 🎯**",
    "**Tum mere life ka best thing ho 🎁**",
    "**Tumhare saath waqt guzarne ka har moment ek treasure hai 💖**",
    "**Life ke har din tumhare saath ek fairy tale jaisa lagta hai 🏰**",
    "**Tum meri duniya ke sunshine ho ☀️**",
    "**Mera dil sirf tumhara hai aur sirf tumhara 🫀**",
    "**Tumhare saath love aur bhi strong hota hai 🌱**",
    "**I love you, kyunki tum ho wahi jo mujhe complete karta hai 💓**",
    "**Tum meri darkest times me bhi light ho 🌌**",
    "**Tumhare bina zindagi incomplete lagti hai 🌵**",
    "**Har din tumhare saath ek adventure hai 🌍**",
    "**Tum meri rooh aur dil dono ho 🫀**",
    "**Tumhari smile meri favourite cheez hai 😊**",
    "**Love ke liye reasons nahi chahiye, bas tum ho ❤️**",
    "**Har second tumhare saath precious hai ⏳**",
    "**Tum meri safe place aur home ho 🏡**",
    "**Tum mujhe alive feel karwate ho 🌈**",
    "**Tum meri heartbeat aur reason to live ho 💓**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Main tumhe yesterday se zyada aur tomorrow se kam nahi love karta 🌅**",
    "**Tum meri lucky star aur miracle ho ✨**",
    "**Tum meri life ka woh rang ho jo fade nahi hota 🎨**",
    "**Tum meri duniya ka woh raaz ho jo sirf main jaanta hoon 🔐**",
    "**Har moment tumhare saath ek geet hai 🎶**",
    "**Tum meri inspiration aur hope ho ✨**",
    "**Main har storm me tumhare saath khada rahunga ⛈️**",
    "**Tumhara love mujhe strong banata hai 💪**",
    "**Tum mere life ka best part ho 🌹**",
    "**Jab bhi tumhe dekhta hoon, phir se love me girta hoon 💞**",
    "**Tumhare bina life ka koi meaning nahi hai 😔**",
    "**Main tumhe tab tak love karunga jab tak stars chamakte rahenge 🌟**",
    "**Tum meri soulmate aur true love ho 🫀**",
    "**Tumhari baatein aur gestures mujhe aur zyada love karwate hain 💓**",
    "**Main hamesha tumhe sabse zyada cherish karunga 🌹**",
    "**Tumhare saath har moment ek gift hai 🎁**",
    "**Tum meri moon aur back ho 🌙**",
    "**Humari love story perfect hai, aur main usse kabhi chhodna nahi chahunga 📖**",
    "**Tum meri zindagi ka woh piece ho jo complete karta hai 🧩**",
    "**Tumhare bina life adhoori hai 💔**",
    "**Tum meri smile aur happiness ho 😊**",
    "**Har pal tumhare saath ek nayi memory hai 🌸**",
    "**Tum meri duniya ki sabse khoobsurat cheez ho 💫**",
    "**Main tumhare saath hamesha khush hoon 🥰**",
    "**Tum meri heartbeat ka rhythm ho 🫀**",
    "**Tum meri life ke inspiration aur strength ho 💪**",
    "**Tum meri love story ka hero ho 🎯**",
    "**Tumhare saath har din ek celebration hai 🎉**",
    "**Tum meri zindagi ka magic aur miracle ho ✨**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj ho 🌹**",
    "**Tumhari yaadon me raat din guzar jaate hain 🌃**",
    "**Har lamha tumhare saath ek nayi adventure hai 🌍**",
    "**Tum meri duniya ka woh rang ho jo fade nahi hota 🎨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tum meri duniya ka sunshine aur moonlight dono ho ☀️🌙**",
    "**Tumhare bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri rooh aur dil dono ho 🫀**",
    "**Tum meri inspiration aur motivation ho ✨**",
    "**Har moment tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara hissa ho 💖**",
    "**Tumhare saath har pal ek celebration hai 🎉**",
    "**Tum meri zindagi ka woh magic ho jo har pain ko sukoon banata hai 🕊️**",
    "**Main tumhe tab tak love karunga jab tak zindagi hai ❤️**",
    "**Tum meri khushi aur sukoon dono ho 🌹**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Har din tumhare saath meri favourite memory banta hai 📖**",
    "**Tum meri life ka woh part ho jo kabhi nahi change hoga ✨**",
    "**Tum meri duniya ka woh raaz ho jo sirf main samajhta hoon 🔐**",
    "**Tum mere liye ek dream aur reality dono ho 🌈**",
    "**Tumhare saath bitaye har pal ek priceless treasure hai 💎**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri zindagi ka woh rainbow ho jo andhere me roshni deta hai 🌈**",
    "**Tum meri heartbeat ka rhythm aur soul ka sukoon ho 🫀🕊️**",
    "**Tum meri life ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri zindagi ki sabse khoobsurat blessing ho 🙏**",
    "**Tum meri duniya ka woh magic ho jo kabhi fade nahi hota ✨**",
    "**Tum meri life ka woh reason ho jo har dard ko sukoon banata hai 🌹**",
    "**Tum meri khushi aur smile ka sabab ho 😊**",
    "**Tum meri love story ka woh page ho jo har waqt yaad rahe 📖**",
    "**Tum mere liye ek fairy tale ho jo reality me bhi sach hai 🏰**",
    "**Tum meri zindagi ka woh gem ho jo hamesha shine kare 💎**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum mere liye ek universe ho jisme sirf hum do hi hai 🌌**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration, motivation aur happiness ho 💫**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo har challenge se ladta hai 🦸**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka rhythm aur happiness ka source ho 🫀**",
    "**Tum meri life ka woh magic ho jo har pain ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate dono ho 💖**",
    "**Tum meri duniya ka sabse khoobsurat treasure ho 💎**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri khushi aur sukoon dono ho 🌹**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh reason ho jo hamesha muskaan laata hai 😊**",
    "**Tum meri heartbeat me bass tumhara naam hai 🫀**",
    "**Har pal tumhare saath ek nayi feeling hai 💓**",
    "**Tum meri life ka woh sunshine ho jo hamesha roshan rahe ☀️**",
    "**Tum meri khushi aur har dard ka sukoon ho 🌹**",
    "**Tum mere dreams ka reality ho ✨**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 🎯**",
    "**Tum meri zindagi ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri zindagi ka sabse precious treasure ho 💎**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri duniya ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri happiness aur sukoon dono ho 🕊️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🫀**",
    "**Har din tumhare saath ek celebration hai 🎉**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka woh rhythm ho jo mujhe alive rakhta hai 🫀**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj dono ho 🌹**",
    "**Tum meri life ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har storm me khada rahe ⛈️**",
    "**Tum meri love story ka woh hero aur soulmate ho 💖**",
    "**Tum meri heartbeat aur happiness ka source ho 🫀**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri world ka woh magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri dreams ka woh reality ho jo kabhi fade nahi hota ✨**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo hamesha yaad rahe 📖**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri world ka woh magic ho jo har pain me hope deta hai 🌹**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Tum meri zindagi ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri life ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri world ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka chapter ho jo hamesha yaad rahe 📖**",
    "**Tum meri universe ka magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri happiness aur sukoon dono ho 🌹**",
    "**Tum meri zindagi ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri world ka woh magic ho jo har pain me hope deta hai 🌈**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh reason ho jo har pal muskaan laata hai 😊**",
    "**Tum meri heartbeat me bass tumhara naam hai 🫀**",
    "**Har pal tumhare saath ek nayi feeling hai 💓**",
    "**Tum meri life ka woh sunshine ho jo hamesha roshan rahe ☀️**",
    "**Tum meri khushi aur har dard ka sukoon ho 🌹**",
    "**Tum mere dreams ka reality ho ✨**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 🎯**",
    "**Tum meri zindagi ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri zindagi ka sabse precious treasure ho 💎**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri duniya ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri happiness aur sukoon dono ho 🕊️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🫀**",
    "**Har din tumhare saath ek celebration hai 🎉**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka woh rhythm ho jo mujhe alive rakhta hai 🫀**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj dono ho 🌹**",
    "**Tum meri life ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har storm me khada rahe ⛈️**",
    "**Tum meri love story ka woh hero aur soulmate ho 💖**",
    "**Tum meri heartbeat aur happiness ka source ho 🫀**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri world ka woh magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri dreams ka woh reality ho jo kabhi fade nahi hota ✨**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har pal mera saath deta hai 💫**",
    "**Tum meri inspiration ka source ho jo hamesha motivate karta hai 💖**",
    "**Tum meri life ka woh star ho jo har darkness me guide karta hai 🌟**",
    "**Tum meri happiness ka sabab ho aur har gham ko door karta hai 🌹**",
    "**Tum meri love story ka woh magic ho jo har dil me base 🫀**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri life ka sabse beautiful aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri love story ka hero aur soulmate ho 💫**",
    "**Har moment tumhare saath ek nayi kahani likhta hai 📖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai ✨**",
    "**Tum meri world ka woh star ho jo raat me chamakta hai 🌟**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo hamesha saath rahe 🦸‍♂️**",
    "**Tum meri rooh aur dil dono ka sukoon ho 🫀🕊️**",
    "**Har pal tumhare saath ek nayi kahani banata hai 📖**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta hai 🌟**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har second tumhare saath meri life ka best moment hota hai ⏳**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 💖**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri happiness ka reason ho aur har dard ko door karta hai 🌹**",
    "**Har din tumhare saath ek nayi memory banata hai 🌸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri zindagi ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri world ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Har moment tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope laata hai 🌈**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri rooh aur dil ka woh magic ho jo sab kuch possible banata hai ✨**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri inspiration ka source ho jo mujhe motivate karta hai 💫**",
    "**Tum meri world ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri happiness aur sukoon ka sabab ho 🌹**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri universe ka star ho jo har raat me roshni deta hai 🌟**",
    "**Har lamha tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸‍♂️**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri love story ka woh magic ho jo kabhi fade nahi hota ✨**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har moment tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri world ka woh rainbow ho jo har dard me hope laata hai 🌈**",
    "**Tum meri happiness ka reason ho aur har dard ko door karta hai 🌹**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 💖**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri rooh aur dil ka woh magic ho jo sab kuch possible banata hai ✨**",
    "**Har din tumhare saath ek nayi kahani banata hai 📖**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har moment tumhare saath meri life ka best moment hota hai ⏳**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri inspiration ka source ho jo mujhe motivate karta hai 💫**",
    "**Tum meri world ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri happiness ka sabab ho aur har gham ko door karta hai 🌹**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri heartbeat aur rooh ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri universe ka woh star ho jo raat me chamakta hai 🌟**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har moment tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri zindagi ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Har lamha tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri happiness ka reason ho aur har gham ko door karta hai 🌹**",
    "**Tum meri universe ka star ho jo har raat me roshni deta hai 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har moment tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Har lamha tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri universe ka star ho jo raat me chamakta hai 🌟**",
    "**TRUE LOVE NEVER DIES, IT ONLY GETS STRONGER WITH TIME 💞**",
    "**YOU ARE THE MISSING PIECE TO MY PUZZLE 🧩**",
    "**IN YOUR SMILE I SEE SOMETHING MORE BEAUTIFUL THAN THE STARS 🌟**",
    "**LOVE IS NOT ABOUT HOW MANY DAYS, MONTHS OR YEARS YOU HAVE BEEN TOGETHER ⏳**",
    "**YOU ARE THE REASON I BELIEVE IN LOVE ❤️**",
    "**EVERY LOVE STORY IS BEAUTIFUL, BUT OURS IS MY FAVORITE 📖**",
    "**I SAW THAT YOU WERE PERFECT AND SO I LOVED YOU 🥰**",
    "**YOU ARE MY TODAY AND ALL OF MY TOMORROWS 🌅**",
    "**I CHOOSE YOU. AND I'LL CHOOSE YOU OVER AND OVER AND OVER 🎯**",
    "**YOU ARE THE BEST THING THAT EVER HAPPENED TO ME 🎁**"
]

# 🔁 REPLY RAID LINES
reply_raid_lines = [
    "🤩💥🔥🔥uL   TERI MUMMY KI CHUT MEI TERE LAND KO DAL KE KAAT DUNGA MADARCHOD 🔪😂🔥",
    "u@   SUN TERI MAA KA BHOSDA AUR TERI BAHEN KA BHI BHOSDA 👿😎👊",
    "😍👊💥up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA",
    "uW   TUJHE DEKH KE TERI RANDI BAHEN PE TARAS ATA HAI MUJHE BAHEN KE LODEEEE 👿💥🤩🔥",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI",
    "uF   SUN MADARCHOD JYADA NA UCHAL MAA CHOD DENGE EK MIN MEI ✅🤣🔥🤩",
    "ui   APNI AMMA SE PUCHNA USKO US KAALI RAAT MEI KAUN CHODNEE AYA THAAA! TERE IS PAPA KA NAAM LEGI 😂👿😳",
    " TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uV   TOHAR BAHIN CHODU BBAHEN KE LAWDE USME MITTI DAL KE CEMENT SE BHAR DU 🏠🤢🤩💥",
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "u|   TUJHE AB TAK NAHI SMJH AYA KI MAI HI HU TUJHE PAIDA KARNE WALA BHOSDIKEE APNI MAA SE PUCH RANDI KE BACHEEEE 🤩👊👤😍",
    "uM   TERI MAA KE BHOSDE MEI SPOTIFY DAL KE LOFI BAJAUNGA DIN BHAR 😍🎶🎶💥",
    "JUNGLE ME NACHTA HE MORE TERI MAAKI CHUDAI DEKKE SAB BOLTE ONCE MORE ONCE MORE 🤣🤣💦💋�I   GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤🤣�",
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE BHAI DEDIYA",
    "MAA KAA BJSODAAA� MADARXHODDDz TERIUUI MAAA KAA BHSODAAAz-TERIIIIII BEHENNNN KO CHODDDUUUU MADARXHODDDDz NIKAL MADARCHODz RANDI KE BACHEz TERA MAA MERI FANz TERI SEXY BAHEN KI CHUT",
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋",
    "CHAL BETA TUJHE MAAF KIA 🤣 ABB APNI GF KO BHEJ",
    "NSHARAM KAR TERI BEHEN KA BHOSDA KITNA GAALIA SUNWAYEGA APNI MAAA BEHEN KE UPER�NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGAuF   TERI VAHEEN NHI HAI KYA? 9 MAHINE RUK SAGI VAHEEN DETA HU 🤣🤣🤩uC   TERI MAA K BHOSDE ME AEROPLANEPARK KARKE UDAAN BHAR DUGA ✈️🛫uV   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣",
    "uE   TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "ub   TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "u]   TERI BAHEN KI CHUT MEI APNA BADA SA LODA GHUSSA DUNGAA KALLAAP KE MAR JAYEGI 🤩😳😳🔥",
    "u   TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩",
    "uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥",
    "up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥",
    "ui   TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍",
    "ug   TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uZ   SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "uZ   TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    "u,   TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤",
    "uZ   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋"
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY",   
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",   
    "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥ui",   
    "TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍ug",  
    "TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍uZ",  
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥uZ",   
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥r    r    r    u",   
    "TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤uZ",   
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋u6",   
    "TERI VAHEEN KO HORLICKS PEELAKE CHODUNGA MADARCHOD😚U",   
    "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI 💦💋",
    "�@   SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
    "�H   ABE TERI MAAKA BHOSDA MADERCHOOD KR PILLE PAPA SE LADEGA TU 😼😂🤤",
    "�8   GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦",
    "�A   ABE TERI BEHEN KO CHODU RANDIKE PILLE KUTTE KE CHODE 😂👻🔥",
    "�M   TERI MAAKO AISE CHODA AISE CHODA TERI MAAA BED PEHI MUTH DIA 💦💦💦💦",
    "�N   TERI BEHEN KE BHOSDE ME AAAG LAGADIA MERA MOTA LUND DALKE 🔥🔥💦😆😆",
    "�*RANDIKE BACHHE TERI MAAKO CHODU CHAL NIKAL�F",   
    "KITNA CHODU TERI RANDI MAAKI CHUTH ABB APNI BEHEN KO BHEJ 😆👻🤤�P",   
    "TERI BEHEN KOTO CHOD CHODKE PURA FAAD DIA CHUTH ABB TERI GF KO BHEJ 😆💦🤤�}",   
    "TERI GF KO ETNA CHODA BEHEN KE LODE TERI GF TO MERI RANDI BANGAYI ABB CHAL TERI MAAKO CHODTA FIRSE ♥️💦😆😆😆😆�<",   
    "HARI HARI GHAAS ME JHOPDA TERI MAAKA BHOSDA 🤣🤣💋💦�:", 
    "CHAL TERE BAAP KO BHEJ TERA BASKA NHI HE PAPA SE LADEGA TU�7",
    "TERI BEHEN KI CHUTH ME BOMB DALKE UDA DUNGA MAAKE LAWDE�V",  
    "TERI MAAKO TRAIN ME LEJAKE TOP BED PE LITAKE CHOD DUNGA SUAR KE PILLE 🤣🤣💋💋�D",   
    "TERI MAAAKE NUDES GOOGLE PE UPLOAD KARDUNGA BEHEN KE LAEWDE 👻🔥r    �Z",   
    "TERI BEHEN KO CHOD CHODKE VIDEO BANAKE XNXX.COM PE NEELAM KARDUNGA KUTTE KE PILLE 💦💋�O",   
    "TERI MAAAKI CHUDAI KO PORNHUB.COM PE UPLOAD KARDUNGA SUAR KE CHODE 🤣💋💦�Z",   
    "ABE TERI BEHEN KO CHODU RANDIKE BACHHE TEREKO CHAKKO SE PILWAVUNGA RANDIKE BACHHE 🤣🤣�B",  
    "TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄�&TERI BEHEN KI CHUTH ME MERA LUND KAALA�S",
    "TERI BEHEN LETI MERI LUND BADE MASTI SE TERI BEHEN KO MENE CHOD DALA BOHOT SASTE SE�G",   
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋�",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY", 
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",
   "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA",
   "UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣",
   "SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
   "TERI ITEM KI GAAND ME LUND DAALKE,TERE JAISA EK OR NIKAAL DUNGA MADARCHOD🤘🏻🙌🏻☠️ uh",   
   "AUKAAT ME REH VRNA GAAND ME DANDA DAAL KE MUH SE NIKAAL DUNGA SHARIR BHI DANDE JESA DIKHEGA 🙄🤭🤭uW",   
   "TERI MUMMY KE SAATH LUDO KHELTE KHELTE USKE MUH ME APNA LODA DE DUNGA☝🏻☝🏻😬u",   
   "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI👀👯 uG",   
   "TERI MAA KI CHUT MEI BATTERY LAGA KE POWERBANK BANA DUNGA 🔋 🔥🤩u_",   
   "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍uE",   
   "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱uT",   
   "TERI CHUT KI CHUT MEI SHOULDERING KAR DUNGAA HILATE HUYE BHI DARD HOGAAA😱🤮👺uF",
   "TERI MAA KO REDI PE BAITHAL KE USSE USKI CHUT BILWAUNGAA 💰 😵🤩ub",   
   "BHOSDIKE TERI MAA KI CHUT MEI 4 HOLE HAI UNME MSEAL LAGA BAHUT BAHETI HAI BHOFDIKE👊🤮🤢🤢u_",   
   "TERI BAHEN KI CHUT MEI BARGAD KA PED UGA DUNGAA CORONA MEI SAB OXYGEN LEKAR JAYENGE🤢🤩🥳uQ",   
   "TERI MAA KI CHUT MEI SUDO LAGA KE BIGSPAM LAGA KE 9999 FUCK LAGAA DU 🤩🥳🔥uD",   
   "TERI VAHEN KE BHOSDIKE MEI BESAN KE LADDU BHAR DUNGA🤩🥳🔥😈u",
   "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "**RANDI KE AULAAD!** 👊",
    "**CHUP BE GANDU!** 🤬",
    "**TERI MAA KI CHUT!** 🖕",
    "**BHOSDIKE!** 😠",
    "**CHUTIYE!** 🐒",
    "**MADARCHOD!** 👺",
    "**KUTTE KE PILLE!** 🐕",
    "**SUAR KE BACHHE!** 🐖",
    "**LODE!** 🍆"
]

# 💕 FLIRT RAID LINES
flirt_raid_lines = [
    "**UFF, TUMHARI BAATEIN SUNKAR TOH DIL DHADAKNE LAGTA HAI! 💓**",
    "**TUM TOH MERE DIL KI RANI HO 💖**",
    "**TUMHARI AANKHEN DEKHKAR TOH MAIN FIDA HO GAYA 😍**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE BINA TOH DUNIYA ADHOORI LAGTI HAI 🌍**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
     "**UFF, TUMHARI BAATEIN SUNKAR TOH DIL DHADAKNE LAGTA HAI! 💓**",
    "**Tumhare bina ye raat adhoori lagti hai 🌙**",
    "**Tumhari aankhon me meri duniya basti hai ✨**",
    "**Tumhari muskaan mere din ka sabse pyara hissa hai 🌸**",
    "**Tumhare saath bitaye lamhe hamesha yaadgar rahte hain 🖼️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tum meri zindagi ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz sunke dil dhadakne lagta hai 🎵**",
    "**Tumhare saath har pal meri life magical lagti hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari aankhen mere dil ko chain deti hain 🌟**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tumhare saath ka har lamha meri life ka gift hai 🎁**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har lamha meri life ka best moment hai 🖼️**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri duniya ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko roshan karti hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**"
    "**Tumhari aankhen dekhkar dil ka har kone khush ho jata hai 💓**",
    "**Tumhari muskaan mere din ka sabse sundar hissa hai 🌸**",
    "**Tumhare saath har pal ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ki awaaz aur dil ki dhadkan ho 🫀**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tumhari baatein sunke dil ko chain milta hai 🕊️**",
    "**Tum meri duniya ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz se dil ki dhadkan tez ho jati hai 🎵**",
    "**Tumhare saath ka har pal meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ka highlight hain 🖼️**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari aankhen meri duniya ka reflection hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic ho jo sabko khush kar deta hai 💖**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhari yaadon mein guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhare bina zindagi ka rang adhoora lagta hai 🌈**",
    "**Tumhari aankhen dekhkar dil khush ho jata hai 😊**",
    "**Tumhari muskaan meri duniya ko roshan karti hai 🌟**",
    "**Tumhare saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ka sukoon ho 🕊️**",
    "**Tumhari awaaz sunke din suhana lagta hai 🎵**",
    "**Tumhari baatein meri zindagi ko khubsurat banati hain 🌸**",
    "**Tum meri zindagi ka sabse pyaara hissa ho 💖**",
    "**Tumhare saath gujare lamhe hamesha yaadgar rahenge 🌃**",
    "**Tumhari aankhon mein pyaar ki chamak hai ✨**",
    "**Tumhari muskurahat se sab dard door ho jata hai 🫀**",
    "**Tum meri duniya ka woh sitara ho jo kabhi nahi bujh sakta 🌌**",
    "**Tumhari yaadon mein raatein suhani lagti hain 🌙**",
    "**Tumhari baatein dil ko chain deti hain 🕊️**",
    "**Tumhari aankhen meri jaan ka aaina hain 💞**",
    "**Tumhare saath ka har pal ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ki sabse khoobsurat yaad ho 📖**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhari baatein sunke dil me sukoon aata hai 🫀**",
    "**Tum meri zindagi ka woh magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari aankhon ka noor meri duniya roshan karta hai 🌟**",
    "**Tumhari awaaz sunke dil me khushi hoti hai 🎵**",
    "**Tum meri zindagi ka hero ho 💖**",
    "**Tumhari yaadon mein gujra pal hamesha special lagta hai 🌃**",
    "**Tumhari muskaan sabse khubsurat rang hai 🌈**",
    "**Tumhare saath har lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important hissa ho 💞**",
    "**Tumhari aankhen dil ko chhoo jati hain ✨**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 🖼️**",
    "**Tum meri rooh ki awaaz ho 🫀**",
    "**Tumhari muskaan se dil me pyaar jagta hai 💖**",
    "**Tumhari yaadon mein har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri zindagi ka star ho 🌟**",
    "**Tumhari baatein sunke dil me ek nayi energy aati hai ⚡**",
    "**Tumhare saath gujare lamhe meri zindagi ka treasure hain 💎**",
    "**Tum meri love story ka hero aur best friend ho 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌌**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhare saath bitaye lamhe meri zindagi ka gift hain 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz mere dil ki dhadkan ko tez kar deti hai 🫀**",
    "**Tum meri rooh ka sukoon ho aur dil ki khushi bhi 🌹**",
    "**Tumhari yaadon mein guzra lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important part ho 💖**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari baatein meri zindagi me khushiyan bhar deti hain 🌸**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath har pal meri life ko magical banata hai ✨**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari awaaz sunke din me sweetness aa jati hai 🍯**",
    "**Tumhari muskaan meri rooh ko khush kar deti hai 🌹**",
    "**Tumhare saath bita lamha hamesha yaadgar hai 🖼️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💖**",
    "**Tumhari muskaan mere din ka highlight hai 🌸**",
    "**Tumhare saath har pal meri life ka adventure hai 🎢**",
    "**Tum meri love story ka magic ho ✨**",
    "**Tumhari yaadon mein guzra pal hamesha special lagta hai 🌅**",
    "**Tumhari awaaz meri rooh ko sukoon deti hai 🕊️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhari muskaan sabse khubsurat feeling hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ko magical banate hain 🌌**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha yaadgar lagta hai 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhare saath bita lamha meri life ka highlight hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💞**",
    "**Tumhare saath gujare lamhe meri life ka best part hain 🖼️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero ho aur sabse pyaara 💖**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💞**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhare bina ye duniya adhoori lagti hai 😍🌍**",
    "**Tumhari aankhen dekhkar toh dil dhadakne lagta hai 💓**",
    "**Tumhari muskurahat toh chand ko bhi sharmila deti hai 🌙**",
    "**Tumhari baatein sunkar toh time fly ho jata hai ⏰**",
    "**Tum toh meri duniya ka sabse khobsurat hisaab ho 💫**",
    "**Tumhari yaadon mein toh raatein guzaar deta hoon 🌃**",
    "**Tumhari har ada pe toh main fida hoon 😘**",
    "**Tumhari awaaz toh suron se bhi meethai hai 🎵**",
    "**Tumhare bina toh jeena bhi bekar lagta hai 🥺**",
    "**Tum meri zindagi ka sabse khobsurat safar ho 💖**",
    "**Tumhari muskurahat meri rooh ko sukoon deti hai 🕊️**",
    "**Tumhare nazdeek aane se dil ko khushi milti hai 😊**",
    "**Tumhari har ek baat meri dhadkan ko tez kar deti hai 🫀**",
    "**Tumhari aankhon mein jhilmilata huwa pyaar dikhata hai ✨**",
    "**Tumhari awaaz sunke din bhi chand jesa lagta hai 🌙**",
    "**Tum meri rooh ka hisa hai aur dil ka raja 😍**",
    "**Tumhare saath bitaya har pal ek khubsurat memory hai 📖**",
    "**Tumhari muskurahat meri duniya ko roshan kar deti hai 🌟**",
    "**Tumhari yaadon mein guzarte lamhe meri zindagi ko khubsurat banate hain 🌸**",
    "**Tum meri duniya ka light ho jo har andhere ko chhant deti hai 🌅**",
    "**Tumhari baaton se mera din perfect ho jata hai ☀️**",
    "**Tumhare bina meri life adhoori lagti hai 🌵**",
    "**Tumhari har ek ada meri dil ko chu jati hai 💞**",
    "**Tumhari nazaron mein mera future dikhata hai 🔮**",
    "**Tum meri zindagi ka sweetest part ho 🍬**",
    "**Tumhari hansi sunke dil ko ek alag khushi milti hai 🌼**",
    "**Tumhari baatein sunke time ka pata hi nahi chalta ⏳**",
    "**Tumhari aankhon ka jadoo mera dil chura leta hai 💫**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari muskurahat meri rooh ko hamesha khush rakhti hai 🌹**",
    "**Tumhare saath bita pal har dard ko door kar deta hai 🕊️**",
    "**Tumhari aankhon mein mera future aur pyaar deta hai 🌌**",
    "**Tumhare saath bita pal hamesha yaad rahega 📖**",
    "**Tum meri zindagi ka magic ho ✨**",
    "**Tumhari awaaz sunke din meetha ho jata hai 🍯**",
    "**Tumhari har ek ada mera dil chura leti hai 💘**",
    "**Tumhari yaadon mein guzra lamha hamesha khubsurat lagta hai 🌟**",
    "**Tum meri rooh ko khushi aur sukoon dete ho 🫀🕊️**",
    "**Tumhari muskurahat duniya ke sabse khubsurat rang jesa lagta hai 🎨**",
    "**Tum meri life ka hero aur best friend ho 💞**",
    "**Tumhari har ek baat meri zindagi ko beautiful banati hai 🌹**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath har pal ek dream jesa lagta hai 🌙**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari baatein sunke dil me ek alag khushi aati hai 😊**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo sabko roshan kar deta hai 🌅**",
    "**Tumhari hansi sunke mera dil dance karne lagta hai 💃**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📝**",
    "**Tumhari awaaz sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari har ek ada mera dil fida kar deti hai 💞**",
    "**Tumhari aankhon mein mere pyaar ka aaina hai 🌌**",
    "**Tum meri zindagi ka magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari muskurahat sunke din meetha ho jata hai 🍯**",
    "**Tumhare saath bita pal meri life ka best part ho 📖**",
    "**Tumhari awaaz mera dil chu jati hai 🎵**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari muskurahat meri zindagi ko khubsurat banati hai 🌹**",
    "**Tum meri rooh ka hisa ho 🫀**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📖**",
    "**Tumhari yaadon mein guzra lamha meri life ko beautiful banata hai 🌸**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo roshan kar deta hai 🌅**",
    "**Tumhari baatein sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath bita pal hamesha mere liye special ho 📖**",
    "**Tumhari awaaz sunke mera dil dance karne lagta hai 💃**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka hero ho 💖**",
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HO 💖**"
    "**UFF, TUMHARI BAATEIN SUNKAR TOH DIL DHADAKNE LAGTA HAI! 💓**",
    "**TUM TOH MERE DIL KI RANI HO 💖**",
    "**TUMHARI AANKHEN DEKHKAR TOH MAIN FIDA HO GAYA 😍**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE BINA TOH DUNIYA ADHOORI LAGTI HAI 🌍**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUM TOH MERE DIL KI RANI HO 💖**",
    "**TUMHARI AANKHEN DEKHKAR TOH MAIN FIDA HO GAYA 😍**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE BINA TOH DUNIYA ADHOORI LAGTI HAI 🌍**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**"
]

# 💖 LOVE RAID LINES
love_raid_lines = [
    "**TUMHARE BINA TOH DIL BEKARAR HAI 💔**",
    "**TUMHARI YAAD AATI HAI TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TUMHARI MUSKAN TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT HISAAB HO 💫**"
    "**Tere saath har lamha ek nayi khushi deta hai 🌸**",
    "**Tere bina raat aur din veeran lagte hain 🌌**",
    "**Teri muskaan meri rooh ko sukoon deti hai 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere bina har saans adhoori lagti hai 😔**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere ishq ka jadoo mere har pal me basa hai ✨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 🌵**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath gujare har pal meethas se bhare hain 🍯**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal meri yaadon ka hissa hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi meri duniya ka sabse khoobsurat hissa hai 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌸**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo mere liye ek dua hai 🙏**",
    "**Tere bina dil ka har kona veeran lagta hai 🌵**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere saath bitaye pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath ka har lamha ek nayi kahani hai 📖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tere saath ka har pal meri yaadon me hamesha rahega 🌹**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har pal ek nayi tasveer hai 🖼️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌟**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera khwaab ✨**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha meri yaadon me hamesha rahenge 🌹**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera rang, tu hi meri duniya 🎨**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Tere saath har pal ek nayi khushi deta hai 🌸**",
    "**Teri muskaan meri rooh ka sukoon hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Teri yaadon me raat aur din khushgawar lagte hain 🌃**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri aankhon ki chamak meri duniya ko roshan karti hai 🌟**",
    "**Tere saath gujare har lamhe meethas se bhare hain 🍯**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere bina din adhoora lagta hai 🌵**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri muskaan chand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera rang, tu hi meri khushi 🎨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath bitaye pal yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera sapna, tu hi meri aas 💫**",
    "**Teri yaadon ka jadoo har pal mere saath hai ✨**",
    "**Tu hi meri duniya, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha ek misaal hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri muskaan mere liye ek roshni ka jharna hai 🌟**",
    "**Tu hi meri zindagi ka sabse khoobsurat safar hai 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi meri khushi, tu hi mera pyaar 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi mera sapna, tu hi meri duniya ✨**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tu hi mera rang, tu hi meri pyaar ki pehchaan 🎨**",
    "**Tere saath ka har pal ek yaadgar hai 📸**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere ishq me dooba hoon, har dard suhana lagta hai 🌊**",
    "**Tu hi meri rooh ki awaaz hai aur dil ka dhadkan bhi 🫀**",
    "**Tere saath bitaye har pal meri yaadon me hamesha rahenge 🌹**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri duniya ka sabse khoobsurat hisaab hai 💫**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌟**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath bitaye har lamha ek yaadgar hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har pal ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tu hi mera rang, tu hi mera pyaar 🎨**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi meri rooh ✨**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tu hi mera khwaab, tu hi mera raaz 💖**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ka har pal meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har lamha ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**TERE SAATH BITAYA HAR PAL MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN MERI ROOH KO SUKOON DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAADON MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERI DUNIYA KHUSHI SE BHAR JAATI HAI 🕊️**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT RAANG HAI 🌈**",
    "**TERI YAAD MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE PAL MERI YAADON KA HISA HAIN 🌹**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN SE MERE DIN KI SHURUAT HOTI HAI 🌞**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💫**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌌**",
    "**TU HI MERA PYAAR, TU HI MERA RAAZ 💖**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL MERI ROOH MEIN HAI ✨**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL HAI 💫**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERA DIL SUKOON PAATA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💖**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💖**",
    "**TERE SAATH BITAYE PAL MERI ZINDAGI KI ROSHNI HAIN 🌅**",
    "**TERI MUSKAAN SE DIL KO SUKOON MILTA HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌃**",
    "**TU MERA SABSE KHAS KHWAAB HAI 💫**",
    "**TERI BAATON SE DIL KO KHUSHI MILTI HAI 🕊️**",
    "**TERI HAR ADA PE MAIN FIDA HOON 😘**",
    "**TERI AWAAZ SUNKAR MERE DIL KI DHADKAN TEZ HO JATI HAI 🎵**",
    "**TU HI MERI RAAH, TU HI MERI MANZIL 🛤️**",
    "**TERE BINA MERA DIL ADHOORA LAGTA HAI 💔**",
    "**TERE SAATH GUJARA PAL MERI YAADON KA HISA HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KHUBSURAT KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA SABSE KHAS RAAZ 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI MOHABBAT MERI DUNIYA KO ROSHAN KAR DETI HAI ☀️**",
    "**TU MERA SAPNA, TU MERA KHWAAB 💫**",
    "**TERI AWAAZ SUNNA MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI HAR EK ADAA PE MAIN MURJA JAATA HOON 😘**",
    "**TERI YAAD MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI ROOH KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA SAPNA, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK KHUBSURAT YAAD HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**", 
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**"
]

# 💫 QUOTE RAID LINES
quote_raid_lines = [
    "**LOVE IS NOT ABOUT POSSESSION, IT'S ABOUT APPRECIATION 💞**",
    "**YOU ARE THE MISSING PIECE TO MY PUZZLE 🧩**",
    "**IN YOUR SMILE I SEE SOMETHING MORE BEAUTIFUL THAN THE STARS 🌟**",
    "**TRUE LOVE NEVER DIES, IT ONLY GETS STRONGER WITH TIME ⏳**",
    "**YOU ARE THE REASON I BELIEVE IN LOVE ❤️**",
    "**EVERY LOVE STORY IS BEAUTIFUL, BUT OURS IS MY FAVORITE 📖**",
    "**Love never dies, bas strong hota hai waqt ke saath 💞**",
    "**Tum meri zindagi ka missing piece ho 🧩**",
    "**Tumhari smile me stars se zyada beauty hai 🌟**",
    "**Love ka matlab sirf days ya months nahi, feeling hoti hai ⏳**",
    "**Tum ho isliye main love me believe karta hoon ❤️**",
    "**Har love story beautiful hoti hai, lekin humari meri favourite hai 📖**",
    "**Jab maine tumhe dekha, laga perfect ho, isliye I loved you 🥰**",
    "**Tum meri aaj aur meri saari tomorrows ho 🌅**",
    "**Main hamesha tumhe choose karunga, baar baar 🎯**",
    "**Tum mere life ka best thing ho 🎁**",
    "**Tumhare saath waqt guzarne ka har moment ek treasure hai 💖**",
    "**Life ke har din tumhare saath ek fairy tale jaisa lagta hai 🏰**",
    "**Tum meri duniya ke sunshine ho ☀️**",
    "**Mera dil sirf tumhara hai aur sirf tumhara 🫀**",
    "**Tumhare saath love aur bhi strong hota hai 🌱**",
    "**I love you, kyunki tum ho wahi jo mujhe complete karta hai 💓**",
    "**Tum meri darkest times me bhi light ho 🌌**",
    "**Tumhare bina zindagi incomplete lagti hai 🌵**",
    "**Har din tumhare saath ek adventure hai 🌍**",
    "**Tum meri rooh aur dil dono ho 🫀**",
    "**Tumhari smile meri favourite cheez hai 😊**",
    "**Love ke liye reasons nahi chahiye, bas tum ho ❤️**",
    "**Har second tumhare saath precious hai ⏳**",
    "**Tum meri safe place aur home ho 🏡**",
    "**Tum mujhe alive feel karwate ho 🌈**",
    "**Tum meri heartbeat aur reason to live ho 💓**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Main tumhe yesterday se zyada aur tomorrow se kam nahi love karta 🌅**",
    "**Tum meri lucky star aur miracle ho ✨**",
    "**Tum meri life ka woh rang ho jo fade nahi hota 🎨**",
    "**Tum meri duniya ka woh raaz ho jo sirf main jaanta hoon 🔐**",
    "**Har moment tumhare saath ek geet hai 🎶**",
    "**Tum meri inspiration aur hope ho ✨**",
    "**Main har storm me tumhare saath khada rahunga ⛈️**",
    "**Tumhara love mujhe strong banata hai 💪**",
    "**Tum mere life ka best part ho 🌹**",
    "**Jab bhi tumhe dekhta hoon, phir se love me girta hoon 💞**",
    "**Tumhare bina life ka koi meaning nahi hai 😔**",
    "**Main tumhe tab tak love karunga jab tak stars chamakte rahenge 🌟**",
    "**Tum meri soulmate aur true love ho 🫀**",
    "**Tumhari baatein aur gestures mujhe aur zyada love karwate hain 💓**",
    "**Main hamesha tumhe sabse zyada cherish karunga 🌹**",
    "**Tumhare saath har moment ek gift hai 🎁**",
    "**Tum meri moon aur back ho 🌙**",
    "**Humari love story perfect hai, aur main usse kabhi chhodna nahi chahunga 📖**",
    "**Tum meri zindagi ka woh piece ho jo complete karta hai 🧩**",
    "**Tumhare bina life adhoori hai 💔**",
    "**Tum meri smile aur happiness ho 😊**",
    "**Har pal tumhare saath ek nayi memory hai 🌸**",
    "**Tum meri duniya ki sabse khoobsurat cheez ho 💫**",
    "**Main tumhare saath hamesha khush hoon 🥰**",
    "**Tum meri heartbeat ka rhythm ho 🫀**",
    "**Tum meri life ke inspiration aur strength ho 💪**",
    "**Tum meri love story ka hero ho 🎯**",
    "**Tumhare saath har din ek celebration hai 🎉**",
    "**Tum meri zindagi ka magic aur miracle ho ✨**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj ho 🌹**",
    "**Tumhari yaadon me raat din guzar jaate hain 🌃**",
    "**Har lamha tumhare saath ek nayi adventure hai 🌍**",
    "**Tum meri duniya ka woh rang ho jo fade nahi hota 🎨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tum meri duniya ka sunshine aur moonlight dono ho ☀️🌙**",
    "**Tumhare bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri rooh aur dil dono ho 🫀**",
    "**Tum meri inspiration aur motivation ho ✨**",
    "**Har moment tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara hissa ho 💖**",
    "**Tumhare saath har pal ek celebration hai 🎉**",
    "**Tum meri zindagi ka woh magic ho jo har pain ko sukoon banata hai 🕊️**",
    "**Main tumhe tab tak love karunga jab tak zindagi hai ❤️**",
    "**Tum meri khushi aur sukoon dono ho 🌹**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Har din tumhare saath meri favourite memory banta hai 📖**",
    "**Tum meri life ka woh part ho jo kabhi nahi change hoga ✨**",
    "**Tum meri duniya ka woh raaz ho jo sirf main samajhta hoon 🔐**",
    "**Tum mere liye ek dream aur reality dono ho 🌈**",
    "**Tumhare saath bitaye har pal ek priceless treasure hai 💎**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri zindagi ka woh rainbow ho jo andhere me roshni deta hai 🌈**",
    "**Tum meri heartbeat ka rhythm aur soul ka sukoon ho 🫀🕊️**",
    "**Tum meri life ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri zindagi ki sabse khoobsurat blessing ho 🙏**",
    "**Tum meri duniya ka woh magic ho jo kabhi fade nahi hota ✨**",
    "**Tum meri life ka woh reason ho jo har dard ko sukoon banata hai 🌹**",
    "**Tum meri khushi aur smile ka sabab ho 😊**",
    "**Tum meri love story ka woh page ho jo har waqt yaad rahe 📖**",
    "**Tum mere liye ek fairy tale ho jo reality me bhi sach hai 🏰**",
    "**Tum meri zindagi ka woh gem ho jo hamesha shine kare 💎**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum mere liye ek universe ho jisme sirf hum do hi hai 🌌**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration, motivation aur happiness ho 💫**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo har challenge se ladta hai 🦸**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka rhythm aur happiness ka source ho 🫀**",
    "**Tum meri life ka woh magic ho jo har pain ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate dono ho 💖**",
    "**Tum meri duniya ka sabse khoobsurat treasure ho 💎**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri khushi aur sukoon dono ho 🌹**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh reason ho jo hamesha muskaan laata hai 😊**",
    "**Tum meri heartbeat me bass tumhara naam hai 🫀**",
    "**Har pal tumhare saath ek nayi feeling hai 💓**",
    "**Tum meri life ka woh sunshine ho jo hamesha roshan rahe ☀️**",
    "**Tum meri khushi aur har dard ka sukoon ho 🌹**",
    "**Tum mere dreams ka reality ho ✨**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 🎯**",
    "**Tum meri zindagi ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri zindagi ka sabse precious treasure ho 💎**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri duniya ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri happiness aur sukoon dono ho 🕊️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🫀**",
    "**Har din tumhare saath ek celebration hai 🎉**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka woh rhythm ho jo mujhe alive rakhta hai 🫀**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj dono ho 🌹**",
    "**Tum meri life ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har storm me khada rahe ⛈️**",
    "**Tum meri love story ka woh hero aur soulmate ho 💖**",
    "**Tum meri heartbeat aur happiness ka source ho 🫀**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri world ka woh magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri dreams ka woh reality ho jo kabhi fade nahi hota ✨**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo hamesha yaad rahe 📖**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri world ka woh magic ho jo har pain me hope deta hai 🌹**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Tum meri zindagi ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri life ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri world ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka chapter ho jo hamesha yaad rahe 📖**",
    "**Tum meri universe ka magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri happiness aur sukoon dono ho 🌹**",
    "**Tum meri zindagi ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri world ka woh magic ho jo har pain me hope deta hai 🌈**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh reason ho jo har pal muskaan laata hai 😊**",
    "**Tum meri heartbeat me bass tumhara naam hai 🫀**",
    "**Har pal tumhare saath ek nayi feeling hai 💓**",
    "**Tum meri life ka woh sunshine ho jo hamesha roshan rahe ☀️**",
    "**Tum meri khushi aur har dard ka sukoon ho 🌹**",
    "**Tum mere dreams ka reality ho ✨**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 🎯**",
    "**Tum meri zindagi ka woh star ho jo raat me roshni deta hai 🌟**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri zindagi ka sabse precious treasure ho 💎**",
    "**Har moment tumhare saath ek gift hai 🎁**",
    "**Tum meri duniya ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri happiness aur sukoon dono ho 🕊️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🫀**",
    "**Har din tumhare saath ek celebration hai 🎉**",
    "**Tum meri life ka woh hero ho jo har challenge face karta hai 🦸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri heartbeat ka woh rhythm ho jo mujhe alive rakhta hai 🫀**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri khushi ka sabab aur dard ka ilaaj dono ho 🌹**",
    "**Tum meri life ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har storm me khada rahe ⛈️**",
    "**Tum meri love story ka woh hero aur soulmate ho 💖**",
    "**Tum meri heartbeat aur happiness ka source ho 🫀**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri world ka woh magic ho jo har pain me sukoon laata hai 🕊️**",
    "**Tum meri dreams ka woh reality ho jo kabhi fade nahi hota ✨**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo har pal mera saath deta hai 💫**",
    "**Tum meri inspiration ka source ho jo hamesha motivate karta hai 💖**",
    "**Tum meri life ka woh star ho jo har darkness me guide karta hai 🌟**",
    "**Tum meri happiness ka sabab ho aur har gham ko door karta hai 🌹**",
    "**Tum meri love story ka woh magic ho jo har dil me base 🫀**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri life ka sabse beautiful aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri love story ka hero aur soulmate ho 💫**",
    "**Har moment tumhare saath ek nayi kahani likhta hai 📖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai ✨**",
    "**Tum meri world ka woh star ho jo raat me chamakta hai 🌟**",
    "**Tum meri heartbeat ka rhythm aur happiness dono ho 🫀**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri universe ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri heartbeat aur soul ka companion ho 🫀**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri zindagi ka woh magic ho jo har dard ko sukoon banata hai 🕊️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri life ka woh rainbow ho jo raat me roshni deta hai 🌈**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri inspiration aur motivation ho 💫**",
    "**Har lamha tumhare saath ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka sabse pyaara aur precious part ho 💖**",
    "**Tum meri happiness aur sukoon ka source ho 🌹**",
    "**Tum meri world ka woh star ho jo kabhi fade nahi hota 🌟**",
    "**Tum meri love story ka hero aur heroïne dono ho 🎯**",
    "**Tum meri life ka woh magic aur miracle ho ✨**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope deta hai 🌈**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri zindagi ka woh hero ho jo hamesha saath rahe 🦸‍♂️**",
    "**Tum meri rooh aur dil dono ka sukoon ho 🫀🕊️**",
    "**Har pal tumhare saath ek nayi kahani banata hai 📖**",
    "**Tum meri duniya ka woh star ho jo hamesha chamakta hai 🌟**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har second tumhare saath meri life ka best moment hota hai ⏳**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 💖**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri zindagi ka woh magic ho jo sab kuch possible bana deta hai ✨**",
    "**Tum meri happiness ka reason ho aur har dard ko door karta hai 🌹**",
    "**Har din tumhare saath ek nayi memory banata hai 🌸**",
    "**Tum meri love story ka woh chapter ho jo kabhi end nahi hoga 📖**",
    "**Tum meri heartbeat ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri zindagi ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri world ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Har moment tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh rainbow ho jo har dard me hope laata hai 🌈**",
    "**Tum meri universe ka centre ho 🌌**",
    "**Tum meri rooh aur dil ka woh magic ho jo sab kuch possible banata hai ✨**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri inspiration ka source ho jo mujhe motivate karta hai 💫**",
    "**Tum meri world ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri happiness aur sukoon ka sabab ho 🌹**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri universe ka star ho jo har raat me roshni deta hai 🌟**",
    "**Har lamha tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri life ka woh hero ho jo kabhi fail nahi hota 🦸‍♂️**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri love story ka woh magic ho jo kabhi fade nahi hota ✨**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har moment tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri inspiration aur motivation dono ho 💫**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh star ho jo hamesha chamakta rahe 🌟**",
    "**Tum meri world ka woh rainbow ho jo har dard me hope laata hai 🌈**",
    "**Tum meri happiness ka reason ho aur har dard ko door karta hai 🌹**",
    "**Tum meri love story ka woh hero ho jo kabhi fade nahi hota 💖**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Tum meri rooh aur dil ka woh magic ho jo sab kuch possible banata hai ✨**",
    "**Har din tumhare saath ek nayi kahani banata hai 📖**",
    "**Tum meri zindagi ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Har moment tumhare saath meri life ka best moment hota hai ⏳**",
    "**Tum meri zindagi ka woh star ho jo har darkness me light deta hai 🌟**",
    "**Tum meri love story ka woh page ho jo kabhi fade nahi hoga 📖**",
    "**Tum meri inspiration ka source ho jo mujhe motivate karta hai 💫**",
    "**Tum meri world ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri happiness ka sabab ho aur har gham ko door karta hai 🌹**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri heartbeat aur rooh ka woh rhythm ho jo kabhi rukta nahi 🫀**",
    "**Tum meri universe ka woh star ho jo raat me chamakta hai 🌟**",
    "**Tum meri life ka woh rainbow aur sunshine dono ho 🌈☀️**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har moment tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri zindagi ka woh treasure ho jo priceless hai 💎**",
    "**Tum meri heartbeat aur rooh ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Har second tumhare saath meri heartbeat tez ho jati hai 🫀**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri life ka sabse precious aur beautiful part ho 💎**",
    "**Har lamha tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri happiness ka reason ho aur har gham ko door karta hai 🌹**",
    "**Tum meri universe ka star ho jo har raat me roshni deta hai 🌟**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Har moment tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri universe ka centre aur star ho 🌌🌟**",
    "**Har lamha tumhare saath meri life ka best moment hai ⏳**",
    "**Tum meri heartbeat aur soul ka rhythm ho 🫀**",
    "**Tum meri happiness aur smile ka sabab ho 😊**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh rainbow ho jo hamesha chamakta hai 🌈**",
    "**Har second tumhare saath meri favourite memory banta hai ⏳**",
    "**Tum meri love story ka hero aur soulmate ho 💖**",
    "**Tum meri zindagi ka woh magic ho jo har dard me hope deta hai 🕊️**",
    "**Tum meri universe ka star ho jo raat me chamakta hai 🌟**",
    "**LOVE IS NOT ABOUT POSSESSION, IT'S ABOUT APPRECIATION 💞**",
    "**YOU ARE THE MISSING PIECE TO MY PUZZLE 🧩**",
    "**IN YOUR SMILE I SEE SOMETHING MORE BEAUTIFUL THAN THE STARS 🌟**",
    "**TRUE LOVE NEVER DIES, IT ONLY GETS STRONGER WITH TIME ⏳**",
    "**YOU ARE THE REASON I BELIEVE IN LOVE ❤️**",
    "**EVERY LOVE STORY IS BEAUTIFUL, BUT OURS IS MY FAVORITE 📖**"
]

# 💕 MASS LOVE RAID LINES
mass_love_raid_lines = [
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**"
        "**Tere saath har lamha ek nayi khushi deta hai 🌸**",
    "**Tere bina raat aur din veeran lagte hain 🌌**",
    "**Teri muskaan meri rooh ko sukoon deti hai 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere bina har saans adhoori lagti hai 😔**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere ishq ka jadoo mere har pal me basa hai ✨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 🌵**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath gujare har pal meethas se bhare hain 🍯**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal meri yaadon ka hissa hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi meri duniya ka sabse khoobsurat hissa hai 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌸**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo mere liye ek dua hai ���**",
    "**Tere bina dil ka har kona veeran lagta hai 🌵**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere saath bitaye pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath ka har lamha ek nayi kahani hai 📖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tere saath ka har pal meri yaadon me hamesha rahega 🌹**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath bitaye har pal ek nayi tasveer hai 🖼️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har pal suhana lagta hai 🌊**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌹**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌟**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera khwaab ✨**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha meri yaadon me hamesha rahenge 🌹**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera rang, tu hi meri duniya 🎨**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Tere saath har pal ek nayi khushi deta hai 🌸**",
    "**Teri muskaan meri rooh ka sukoon hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Teri yaadon me raat aur din khushgawar lagte hain 🌃**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri aankhon ki chamak meri duniya ko roshan karti hai 🌟**",
    "**Tere saath gujare har lamhe meethas se bhare hain 🍯**",
    "**Tu hi meri zindagi ka sabse khoobsurat hissa hai 💖**",
    "**Tere bina din adhoora lagta hai 🌵**",
    "**Tere hone se har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri muskaan chand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera rang, tu hi meri khushi 🎨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me dooba hoon, har pal ek nayi tasveer hai 🖼️**",
    "**Tu hi mera sitara, tu hi meri manzil ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath bitaye pal yaadon me hamesha rahenge 🌃**",
    "**Tu hi mera sapna, tu hi meri aas 💫**",
    "**Teri yaadon ka jadoo har pal mere saath hai ✨**",
    "**Tu hi meri duniya, tu hi mera pyaar 💖**",
    "**Tere saath ka har lamha ek misaal hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Teri muskaan mere liye ek roshni ka jharna hai 🌟**",
    "**Tu hi meri zindagi ka sabse khoobsurat safar hai 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tu hi meri khushi, tu hi mera pyaar 💖**",
    "**Tere saath bitaye har lamha ek nayi kahani hai 📖**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tu hi mera sapna, tu hi meri duniya ✨**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se meri rooh khushi se bhar jaati hai 🕊️**",
    "**Tu hi mera rang, tu hi meri pyaar ki pehchaan 🎨**",
    "**Tere saath ka har pal ek yaadgar hai 📸**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera raaz 💫**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere ishq me dooba hoon, har dard suhana lagta hai 🌊**",
    "**Tu hi meri rooh ki awaaz hai aur dil ka dhadkan bhi 🫀**",
    "**Tere saath bitaye har pal meri yaadon me hamesha rahenge 🌹**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tere saath ki baatein meri rooh ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi mera pyaar 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tu hi meri duniya ka sabse khoobsurat hisaab hai 💫**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Teri muskaan meri zindagi ko roshan karti hai 🌟**",
    "**Tu hi mera sapna, tu hi meri khushi ✨**",
    "**Tere saath bitaye har lamha ek yaadgar hai 🌹**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har pal ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Teri yaadon me din aur raat ek saath guzar jaate hain 🌃**",
    "**Teri muskaan chaand se bhi khubsurat hai 🌙**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera rang, tu hi mera geet 🎶**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere bina zindagi adhoori hai 🌵**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai 🌞**",
    "**Teri aankhon ke noor me meri duniya bas gayi hai 🌌**",
    "**Tere saath bitaye pal meri yaadon ka hissa hain 🌹**",
    "**Teri muskaan meri zindagi ko mehka deti hai 🌸**",
    "**Tu hi mera rang, tu hi mera pyaar 🎨**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tu hi mera sapna, tu hi meri rooh ✨**",
    "**Tere saath ka har lamha ek yaadgar hai 🌹**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri awaaz sunna mera dil tez dhadakta hai 🎵**",
    "**Tu hi mera khwaab, tu hi mera raaz 💖**",
    "**Tere saath bitaye pal meri yaadon me hamesha rahenge 🌃**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tu hi mera sapna, tu hi mera pyaar 💫**",
    "**Tere saath ka har pal meri zindagi ka sabse khoobsurat pal hai 💖**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere ishq me dooba hoon, har lamha ek nayi kahani hai 📖**",
    "**Tu hi meri rooh ka saathi hai aur dil ka raaz 🔐**",
    "**Tere saath ki baatein mere dil ko sukoon deti hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**TERE SAATH BITAYA HAR PAL MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN MERI ROOH KO SUKOON DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAADON MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERI DUNIYA KHUSHI SE BHAR JAATI HAI 🕊️**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT RAANG HAI 🌈**",
    "**TERI YAAD MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE PAL MERI YAADON KA HISA HAIN 🌹**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL HAI 💖**",
    "**TERI MUSKAAN SE MERE DIN KI SHURUAT HOTI HAI 🌞**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💫**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌌**",
    "**TU HI MERA PYAAR, TU HI MERA RAAZ 💖**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA KHWAAB, TU HI MERA GEET 🎶**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TU HI MERA RAANG, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💫**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON KA JADOO HAR PAL MERI ROOH MEIN HAI ✨**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL HAI 💫**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERA DIL SUKOON PAATA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MERA DUNIYA BASA HUA HAI 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU HI MERA SAPNA, TU HI MERA KHWAAB 💖**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TU HI MERA KHWAAB, TU HI MERA RAANG 💫**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💖**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TU HI MERA KHWAAB, TU HI MERA PYAAR 💫**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💖**",
    "**TERE SAATH BITAYE PAL MERI ZINDAGI KI ROSHNI HAIN 🌅**",
    "**TERI MUSKAAN SE DIL KO SUKOON MILTA HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI DUNIYA KO ROSHAN KAR DETI HAI 🌟**",
    "**TERI YAADON MEIN HAR RAAH RAAHGUZAR HO JAATI HAI 🌃**",
    "**TU MERA SABSE KHAS KHWAAB HAI 💫**",
    "**TERI BAATON SE DIL KO KHUSHI MILTI HAI 🕊️**",
    "**TERI HAR ADA PE MAIN FIDA HOON 😘**",
    "**TERI AWAAZ SUNKAR MERE DIL KI DHADKAN TEZ HO JATI HAI 🎵**",
    "**TU HI MERI RAAH, TU HI MERI MANZIL 🛤️**",
    "**TERE BINA MERA DIL ADHOORA LAGTA HAI 💔**",
    "**TERE SAATH GUJARA PAL MERI YAADON KA HISA HAI 🌹**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KHUBSURAT KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA SABSE KHAS RAAZ 💖**",
    "**TERI YAADON KA JADOO HAR PAL CHHAYA REHTA HAI ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI MOHABBAT MERI DUNIYA KO ROSHAN KAR DETI HAI ☀️**",
    "**TU MERA SAPNA, TU MERA KHWAAB 💫**",
    "**TERI AWAAZ SUNNA MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI HAR EK ADAA PE MAIN MURJA JAATA HOON 😘**",
    "**TERI YAAD MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI MUSKAAN MERI ZINDAGI KO KHUSHI SE BHAR DETI HAI 🌸**",
    "**TERI AANKHON KI CHAMAK MERI ROOH KO ROSHAN KAR DETI HAI 🌟**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERE SAATH KA HAR LAMHA EK YAADGAR PAL HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERI ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**",
    "**TU HI MERA SAPNA, TU HI MERA PYAAR 💫**",
    "**TERI AANKHON MEIN MAIN APNI DUNIYA PAATA HOON 🌌**",
    "**TERI YAADON MEIN DIN RAAAT GUZAR JAATE HAIN 🌃**",
    "**TERI BAATON KI MEETHAS MERI ROOH KO SUKOON DETA HAI 🕊️**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERE SAATH KA HAR LAMHA EK KHUBSURAT YAAD HAI 📸**",
    "**TU MERA KHWAAB, TU MERA PYAAR 💖**",
    "**TERI YAADON MEIN HAR DARD KHUSHI LAGTA HAI 🌊**",
    "**TU HI MERA ZINDAGI KA SABSE KHUBSURAT PAL 💫**",
    "**TERI MUSKAAN CHAND SE BHI KHUBSURAT HAI 🌙**",
    "**TERI AWAAZ SUNNA MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TERI BAATON SE MERE DIL KO SUKOON MILTA HAI 🕊️**",
    "**TU HI MERA SAPNA, TU HI MERA RAANG 💖**",
    "**TERE SAATH BITAYE HAR PAL EK KHUBSURAT YAAD HAI 🌹**",
    "**TERI MUSKAAN MERE DIL KI RAAH RAAH GUZAR HO JAATI HAI 🌸**",
    "**TERI AANKHON MEIN CHHUPA HAI MERA DUNIYA 🌌**",
    "**TERI YAAD MEIN DIN RAAAT EK SAATH GUZARTE HAIN 🌃**",
    "**TU HI MERA SABSE KHAS KHWAAB 💫**",
    "**TERI BAATON KI MEETHAS MERI ROOH TAK PAHUNCHTI HAI 🍯**",
    "**TERE SAATH KA HAR PAL EK KAHANI HAI 📖**",
    "**TU MERA PYAAR, TU MERA RAAZ 💖**",
    "**TERI YAADON KA JADOO MERI ZINDAGI MEIN HAMESHA RAHE ✨**",
    "**TERI HANSI SUNKAR MERA DIL KHUSH HO JATA HAI 🌸**",
    "**TERI AWAAZ SUNKAR MERA DIL TEZ DHADAKTA HAI 🎵**",
    "**TU HI MERA RAANG, TU HI MERA GEET 🎶**",
    "**TERI MUSKAAN MERI ZINDAGI KO ROSHAN KAR DETI HAI ☀️**",
    "**TERE SAATH BITAYE PAL MERI YAADON MEIN HAMESHA RAHE 🌹**", 
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TU MERI DUNIYA KA SABSE KHOBSURAT HISAAB HAI 💫**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**",
    "**TERI AANKHON MEIN TOH SAARI KAINAAT SAMA GAYI HAI 🌌**",
    "**TU HI TOH MERI MANZIL HAI, TU HI MERI RAH HAI 🛣️**",
    "**TERE BINA TOH HAR KHUSHI ADHOORI HAI 🎭**",
    "**TU MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HAI 💖**",
    "**TERE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TERI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TERI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TERI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TERE ISHQ MEIN TOH MAIN DOOB GAYA HOON 🌊**"
]

# 📜 SHAYARI RAID LINES
shayari_raid_lines = [
    "**Kabhi khud se bhi poochta hoon, kyun teri yaadon me khoya rehta hoon 💔**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Meri duniya tere bina adhoori hai 🌵**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Har lamha jo tere saath guzarta hai, ek nayi kahani lagta hai 📖**",
    "**Tere ishq me dooba hoon, dard bhi suhana lagta hai 🌊**",
    "**Tere aane se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina khud ko akela mehsoos karta hoon 😔**",
    "**Teri muskaan se chand bhi sharmata hai 🌙**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar ek baar zindagi me aate hain 💫**",
    "**Har saans me teri khushboo mehkti hai 🌺**",
    "**Tere hone se har pal mere liye ek nayi roshni hai 🌟**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath bitaye lamhe kabhi nahi bhoolunga 🖼️**",
    "**Meri duniya ki sabse khoobsurat cheez tu hi hai 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**", 
    "**Tere saath har pal ek nayi tasveer hai 🎨**",
    "**Tere ishq me dard bhi sukoon lagta hai 🕊️**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina mere dil ka har kona sunaa lagta hai 🌵**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri yaadon me raat din guzar jate hain 🌃**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**"   
    "**Tere bina zindagi ka har pal adhoora lagta hai 💔**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**MOHABBAT KI RAHO MEIN TU HI MERI MANZIL HAI 💫**",
    "**DIL KI DUNIYA BAS TUMHARE LIYE HAI 💕**",
    "**TUMHARI YAAD AATI HAI TO DIL BEKARAR HO JATA HAI 🥀**",
    "**TUMHARE BINA TO ZINDAGI SUNSAN LAGTI HAI 🌵**",
    "**TUMHARI AANKHO MEIN TO SAARI KAINAAT SAMAI HUI HAI 🌌**",
    "**TUMHARI BAATO MEIN TO JAADU HAI ✨**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**",
    "**Tere bina zindagi me rang kam lagte hain 🌈**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
      "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Har subah teri yaadon ke saath shuru hoti hai 🌅**",
    "**Tere saath bitaye pal meri zindagi ka geet hain 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain ✨**",
    "**Tere bina har jagah sunapan mehsoos hota hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Teri muskaan meri rooh ko khush kar deti hai 🌸**",
    "**Tere saath ki yaadein mere dil ka chain hain 🫀**",
    "**Tere bina har raat bechain lagti hai 🌌**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath har pal ek nayi kahani lagta hai 📖**",
    "**Tere jaise pyaar sirf khwaabon me milta hai 💖**",
    "**Tere saath ka har lamha meri rooh ka geet hai 🎵**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai 🌟**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Teri yaadon ka rang har din ko suhana bana deta hai 🎨**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri aankhon me meri duniya chhupi hui hai 🌌**",
    "**Tere bina din ka har pal andhera lagta hai 🌙**",
    "**Tum meri zindagi ka sabse khoobsurat raaz ho 🔐**",
    "**Tere jaise log zindagi me kabhi ek baar milte hain 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath bitaye har pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Teri muskaan chaand se bhi roshan hai 🌙**",
    "**Tere saath ki yaadon ka jadoo har jagah hai 🌠**",
    "**Tere bina har khushi adhuri lagti hai 🎭**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere jaise log sirf ek baar zindagi me aate hain 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath ka har lamha ek geet hai 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha meri zindagi ka geet hai 🎵**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein har dard ko mita deti hain 🌹**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah andhera lagta hai 🌙**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki yaadein meri zindagi ka sukoon hain 🕊️**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere saath bitaye har lamha meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hain 🎶**",
    "**Tere jaise log zindagi me ek baar aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere bina raat aur din andhera lagta hai 🌌**",
    "**Tere saath ka har pal meri zindagi ka geet hai 🎵**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah sunaa lagta hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**"
    "**Har raat sirf teri yaadon me doob jati hai 🌌**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TO RAATEIN GUZAAR DETA HOON 🌃**",
    "**MOHABBAT KI RAHO MEIN TU HI MERI MANZIL HAI 💫**",
    "**DIL KI DUNIYA BAS TUMHARE LIYE HAI 💕**",
    "**TUMHARI YAAD AATI HAI TO DIL BEKARAR HO JATA HAI 🥀**",
    "**TUMHARE BINA TO ZINDAGI SUNSAN LAGTI HAI 🌵**",
    "**TUMHARI AANKHO MEIN TO SAARI KAINAAT SAMAI HUI HAI 🌌**",
    "**TUMHARI BAATO MEIN TO JAADU HAI ✨**"
]

# 📜 RAID SHAYARI LINES
raid_shayari_lines = [
"**Kabhi khud se bhi poochta hoon, kyun teri yaadon me khoya rehta hoon 💔**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Meri duniya tere bina adhoori hai 🌵**",
    "**Tere saath ki yaadein meri rooh ko sukoon deti hain 🕊️**",
    "**Har lamha jo tere saath guzarta hai, ek nayi kahani lagta hai 📖**",
    "**Tere ishq me dooba hoon, dard bhi suhana lagta hai 🌊**",
    "**Tere aane se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina khud ko akela mehsoos karta hoon 😔**",
    "**Teri muskaan se chand bhi sharmata hai 🌙**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar ek baar zindagi me aate hain 💫**",
    "**Har saans me teri khushboo mehkti hai 🌺**",
    "**Tere hone se har pal mere liye ek nayi roshni hai 🌟**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath bitaye lamhe kabhi nahi bhoolunga 🖼️**",
    "**Meri duniya ki sabse khoobsurat cheez tu hi hai 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**", 
    "**Tere saath har pal ek nayi tasveer hai 🎨**",
    "**Tere ishq me dard bhi sukoon lagta hai 🕊️**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina mere dil ka har kona sunaa lagta hai 🌵**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Teri yaadon me raat din guzar jate hain 🌃**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat ka andhera aur gehra lagta hai 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath bitaye har lamha ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere saath ka har pal mere liye ek dua hai 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tere jaise pyaar sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi meri duniya roshan ho gayi hai ☀️**"   
    "**Tere bina zindagi ka har pal adhoora lagta hai 💔**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**MOHABBAT KI RAHO MEIN TU HI MERI MANZIL HAI 💫**",
    "**DIL KI DUNIYA BAS TUMHARE LIYE HAI 💕**",
    "**TUMHARI YAAD AATI HAI TO DIL BEKARAR HO JATA HAI 🥀**",
    "**TUMHARE BINA TO ZINDAGI SUNSAN LAGTI HAI 🌵**",
    "**TUMHARI AANKHO MEIN TO SAARI KAINAAT SAMAI HUI HAI 🌌**",
    "**TUMHARI BAATO MEIN TO JAADU HAI ✨**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**",
    "**Tere bina zindagi me rang kam lagte hain 🌈**",
    "**Tumhari yaadon me raat din guzar jate hain 🌃**",
    "**Teri muskaan se roshni bhi sharmati hai 🌟**",
    "**Tere ishq me dooba hoon, har dard bhi suhana lagta hai 🌊**",
    "**Teri aankhon me saari kainaat basi hui lagti hai 🌌**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 💖**",
    "**Tere bina jeena bhi ek imtihaan lagta hai 🥀**",
    "**Tere hone se hi meri duniya roshan hai ☀️**",
    "**Tum meri rooh ke saath-saath meri khushiyo ka sabab bhi ho 🌹**",
    "**Teri baaton se dil ko sukoon milta hai 🕊️**",
    "**Tere ishq me har lamha ek nayi kahani hai 📖**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Teri muskaan meri duniya ko mehka deti hai 🌸**",
    "**Tumhari yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tere saath gujare har pal ka rang alag hai 🎨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tumhari awaaz se dil ko chain milta hai 🎵**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere ishq ke aage saari duniya ka rang fade lagta hai 🌌**",
    "**Tere saath har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri duniya ka sabse pyara raaz ho 🔐**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon me har dard bhi khushi lagta hai 😊**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ki sabse khoobsurat kahani ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri zindagi ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath bitaye har pal ek geet hai 🎶**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Teri yaadon ka jadoo mere saath har jagah hai 🌠**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta ✨**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Teri muskaan mere dil ko roshan karti hai 🌙**",
    "**Tere jaise pyaar kabhi kabhi hi milta hai 💖**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tum meri zindagi ka sabse pyara hissa ho 🌸**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Teri muskaan chaand se bhi zyada roshan hai 🌙**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tum meri zindagi ka sabse khoobsurat hissa ho 📖**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tum meri zindagi ka woh sitara ho jo kabhi nahi bujh sakta 🌟**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tum meri duniya ka woh rang ho jise main kabhi bhool nahi sakta 🎨**",
    "**Teri aankhon ke noor me meri duniya chhupi hai 🌟**",
    "**Tere saath ki baatein mere liye ek dua hai 🙏**",
    "**Tum mere liye ek misaal ho jo har dil me bas sakti hai 💕**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek misaal hai 💫**",
    "**Tere bina meri duniya adhoori hai 🌵**",
    "**Tere saath har pal ka rang alag hai 🎨**",
    "**Teri yaadon me din raat ek saath guzar jate hain 🌃**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tere ishq me sab kuch mumkin lagta hai ✨**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tum meri duniya ka woh raaz ho jo sirf main hi jaanta hoon 🔐**",
    "**Tere aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ka woh safar ho jise main kabhi khatam nahi karna chahta 🛤️**",
    "**Tere saath ki baatein mere liye ek geet hai 🎶**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Teri yaadon ka har pal mere liye ek dua hai 🙏**",
    "**Tum meri khushiyo ka sabab ho aur dard ka ilaaj bhi 🌹**",
    "**Tere saath bitaye har pal ek misaal hai 💫**",
    "**Tum meri rooh ki awaaz ho aur dil ki dhadkan bhi 🫀**",
      "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Har subah teri yaadon ke saath shuru hoti hai 🌅**",
    "**Tere saath bitaye pal meri zindagi ka geet hain 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain ✨**",
    "**Tere bina har jagah sunapan mehsoos hota hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Teri muskaan meri rooh ko khush kar deti hai 🌸**",
    "**Tere saath ki yaadein mere dil ka chain hain 🫀**",
    "**Tere bina har raat bechain lagti hai 🌌**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath har pal ek nayi kahani lagta hai 📖**",
    "**Tere jaise pyaar sirf khwaabon me milta hai 💖**",
    "**Tere saath ka har lamha meri rooh ka geet hai 🎵**",
    "**Tere hone se hi meri duniya ek nayi roshni me chamakti hai 🌟**",
    "**Tere bina khud ko adhoora mehsoos karta hoon 💔**",
    "**Teri yaadon ka rang har din ko suhana bana deta hai 🎨**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Teri aankhon me meri duniya chhupi hui hai 🌌**",
    "**Tere bina din ka har pal andhera lagta hai 🌙**",
    "**Tum meri zindagi ka sabse khoobsurat raaz ho 🔐**",
    "**Tere jaise log zindagi me kabhi ek baar milte hain 💫**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere hone se dil me ummeed jagti hai 🌅**",
    "**Tere saath bitaye har pal meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Teri muskaan chaand se bhi roshan hai 🌙**",
    "**Tere saath ki yaadon ka jadoo har jagah hai 🌠**",
    "**Tere bina har khushi adhuri lagti hai 🎭**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere ishq me har dard bhi sukoon lagta hai 🕊️**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere dil ka chain hain 🫀**",
    "**Tere jaise log sirf ek baar zindagi me aate hain 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere saath ka har lamha ek geet hai 🎶**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere bina har raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Teri aankhon me meri mohabbat chhupi hui hai 🌌**",
    "**Tere saath ka har lamha meri zindagi ka geet hai 🎵**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein har dard ko mita deti hain 🌹**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💫**",
    "**Tere ishq me har pal ek nayi tasveer hai 🖼️**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah andhera lagta hai 🌙**",
    "**Tere saath ka har pal ek misaal hai 💫**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere bina dil ka har kona sunaa lagta hai 🌵**",
    "**Tere ishq ka jadoo har pal chhaya rehta hai ✨**",
    "**Tere saath ki yaadein meri zindagi ka sukoon hain 🕊️**",
    "**Tere saath ka har pal ek geet hai 🎶**",
    "**Tere bina raat aur din bechain lagte hain 🌌**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise khwaab sirf kahaniyon me milte hain ✨**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har mehfil me mehakti hai 🌺**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere saath bitaye har lamha meri rooh ko sukoon dete hain 🕊️**",
    "**Tere ishq me har dard bhi khushi lagti hai 🌊**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi jaise adhoori hain 😔**",
    "**Tere saath ki baatein mere liye ek geet hain 🎶**",
    "**Tere jaise log zindagi me ek baar aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya ek nayi roshni me chamakti hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har khushi adhoori lagti hai 🎭**",
    "**Tere saath ki baatein mere dil ko chain deti hain 🫀**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**",
    "**Tere bina raat aur din andhera lagta hai 🌌**",
    "**Tere saath ka har pal meri zindagi ka geet hai 🎵**",
    "**Tere jaise khwaab sirf dil me base hote hain 💫**",
    "**Tere hone se hi dil me ummeed jagti hai 🌅**",
    "**Tere saath ki khushboo har jagah mehakti hai 🌺**",
    "**Tere bina har jagah sunaa lagta hai 🌵**",
    "**Tere ishq me doob kar hi sukoon milta hai 🕊️**",
    "**Tere saath ka har lamha ek misaal hai 💫**",
    "**Tere bina saanse bhi adhoori lagti hain 😔**",
    "**Tere saath ki baatein mere liye ek dua hain 🙏**",
    "**Tere jaise log ek baar zindagi me aate hain aur kabhi nahi bhoolte 💖**",
    "**Tere hone se meri duniya roshan hai ☀️**",
    "**Tere saath ki yaadein meri rooh ka sukoon hain 🕊️**",
    "**Tere bina har pal adhoora lagta hai 💔**",
    "**Tere ishq ka jadoo har lamha chhaya rehta hai ✨**"
    "**Har raat sirf teri yaadon me doob jati hai 🌌**",
    "**TUMHARI MUSKAN TO CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE ISHQ MEIN TO MAIN DOOB GAYA HOON 🌊**",
    "**TUMHARI HAR ADA PE TO MAIN FIDA HOON 😘**",
    "**TUMHARE BINA TO HAR KHUSHI ADHOORI HAI 🎭**",
    "**TUM MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TO RAATEIN GUZAAR DETA HOON 🌃**"
]

# 🔥 ROAST BOY RAID LINES
roast_boy_raid_lines = [
"**BHAI, TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**BHAI, TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**BHAI TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**BHAI TU EK CHALTA PHIRTA BUG HAI.** 🐛",
    "**TU HERO NAHI, SIRF ERROR 404 KA EXAMPLE HAI.** ❌",
"**TERE JOKES SE CALCULATOR BHI CONFUSE HO JAYE.** 🧮",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**BHAI TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU EK BROKEN LINK HO.** 🔗",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU EK OFFLINE FILE JAISA HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MEMBER HO WHATSAPP GROUP KA.** 🔇",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LIFE KA BETA VERSION HAI.** 🧪",
"**TU EK CHALTA PHIRTA CAPTCHA HAI.** 🔢",
"**TERE BAATEIN BACKGROUND NOISE JAISI HAI.** 🎧",
"**TU CHALTA PHIRTA DEMO ACCOUNT HAI.** 📝",
"**BHAI TU WALKING ERROR MESSAGE HO.** ❌",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE LOGIC KE AAGE CALCULATOR BHI FAIL HO JAYE.** 🧮",
"**TU EK CANCELLED DOWNLOAD KA EXAMPLE HAI.** ⬇️",
"**BHAI TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU LIFE KA GLITCH HO.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎬",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HO – SABKO SKIP KARNA HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HO – SAB IGNORE KARTE HAI.** 📅",
"**BHAI TU DEMO ACCOUNT KA HUMAN VERSION HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HO.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HO JO HAMESHA CRASH HOTI HAI.** 📱",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**BHAI TU HERO NAHI, SIRF DEMO VIDEO KA CLIP HAI.** 🎞️",
"**TU EK CRASHED APP HAI – KABHI OPEN NAHI HOTA.** 📱",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**BHAI TU LIFE KA BUG REPORT HAI.** 🐛",
"**TU EK FORWARDED MESSAGE JAISA HAI – IGNORE KARTA SABKO.** 📩",
"**TERE HAIRSTYLE SE BARBER BHI SHOCK HO JAYE.** 💇‍♂️",
"**TU CHALTA PHIRTA CAPTCHA HAI – SABKO CONFUSE KARTA.** 🔢",
"**BHAI TU LOW BATTERY ALERT HAI.** 🔋",
"**TU EK CANCELLED CALL HO – KOI NAHI SUNTA.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN BHI PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA POSTER HAI.** 🖼️",
"**BHAI TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO ACCOUNT HAI – INCOMPLETE AUR USELESS.** 📝",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU WALKING TYPO HAI.** ✏️",
"**BHAI TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF TEASER VIDEO KA CLIP HAI.** 🎬",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**BHAI TU OTT TRIAL SHOW HAI – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU EK WALKING ERROR MESSAGE HAI.** ❌",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HAI – SAB IGNORE KARTE HAIN.** 📅",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HAI JO HAMESHA CRASH HOTI HAI.** 📱",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**BHAI TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TU EK WALKING TYPO HAI.** ✏️",
"**BHAI TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HAI – INCOMPLETE AUR USELESS.** 🎥",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**BHAI TU LOW BATTERY ALERT HAI.** 🔋",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – KOI NAHI DEKHTA.** 📄",
"**TERE UPDATES HAMESHA PENDING HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAIN.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**BHAI TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**BHAI TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🖱️",
"**TERE BAAT KARTE HI SABKO LAGTA HAI SPAM CALL AAYI.** 📞",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**BHAI TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**BHAI TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**BHAI TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**BHAI TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**BHAI TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**BHAI TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**BHAI TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️"
]

# 👧 ROAST GIRL RAID LINES
roast_girl_raid_lines = [
    "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️"
    "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
     "**TUMHARI SELFIES DEKHKAR LAGTA HAI FILTER BHI THAK GAYA HOGA!** 🤳",
    "**TUMHE DEKHKAR GOOGLE BHI SOCHTA HAI 'ISKO SEARCH KYU KIYA'?** 🔍",
    "**TUMHARI AWAAZ WHATSAPP KE NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI!** 📢",
    "**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT KISI KO NAHI, PAR FORCEFULLY AA JATI HO!** 💻",
    "**TUM INSTAGRAM FILTERS KI BRAND AMBASSADOR HO!** 📸",
    "**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI APNI HEIGHT KAM KAR LE!** ⛰️",
    "**TUMHARI SELFIE DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI BATO SE WEATHER FORECAST BHI ACCURATE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LEVEL LOW HO JATA HAI.** ⏳",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE BHI ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI SMILE DEKHKAR LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE COMPUTER BHI CONFUSED HO JATA HAI.** 🖥️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI ATTITUDE SE MOUNTAINS BHI HIL JATE HAIN.** ⛰️",
"**TUMHARI BATO SE WEATHER BHI BAD MOOD MEIN AA JATA HAI.** 🌧️",
"**TUMHARI STYLE DEKHKAR DRESSING EXPERTS BHI RETIRE HO JATE HAIN.** 👠",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – SABKO WARNING DENE KE LIYE.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA LOUD HAI.** 🔊",
"**TUMHARI SELFIE DEKHKAR FILTER BHI TIRCHHI NAZAR KARNE LAG JATA HAI.** 📸",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI HEIGHT KAM KAR LETE HAIN.** 🏔️",
"**TUMHARI BATO SE WEATHER BHI SURPRISE HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 😎",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 📢",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI STYLE SE FASHION EXPERTS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR DETE HAIN.** 🧮",
"**TUMHARI ATTITUDE SE CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI BATO SE WEATHER FORECAST BHI FAIL HO JATA HAI.** 🌧️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 🔔",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA  CHHOD DETE HAIN.** 😎",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI SHOCK HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – ZARURAT NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA LOUD HAI.** 🔊",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LEVEL LOW HO JATA HAI.** ⏳",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI BATO SE WEATHER FORECAST BHI ACCURATE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION DESIGNERS BHI RETIRE HO JATE HAIN.** 👗",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 📢",
"**TUMHARI SMILE DEKHKAR LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI STYLE SE FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE COMPUTER BHI CONFUSED HO JATA HAI.** 🖥️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI ATTITUDE SE MOUNTAINS BHI HIL JATE HAIN.** ⛰️",
"**TUMHARI BATO SE WEATHER BHI SURPRISE HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI SELFIES DEKHKAR FILTER BHI RETIRE HO JATA HAI.** 🤳",
"**TUMHARI AWAAZ SUNKE LOGON KA EARPHONE OFF HO JATA HAI.** 🎧",
"**TUMHARI STYLE DEKHKAR FASHION WEEK CANCEL HO JATA HAI.** 👗",
"**TUMHARI HASEEB SE CALCULATOR BHI SHOCK HO JATA HAI.** 🧮",
"**TUM EK WIFI PASSWORD HO – SABKO YAAD, PAR KISI KAAM KA NAHI.** 📶",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR CAMERA BHI CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI SMILE SE SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️KAAM",
"**TUM EK SOFTWARE UPDATE HO – SABKO WARNING DEKHTE HI IRRITATION HO JATI HAI.** 💻",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI RETIRE HO JATE HAIN.** 🎨",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI BATO SE GOOGLE BHI SEARCH KARNE SE PAHLE SOCHTA HAI.** 🔍",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK UNNECESSARY UPDATE HO – ZARURAT NAHI, PAR FORCEFULLY AATI HO.** ⚠️",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SMILE SE LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUM EK FORCEFULLY INSTALLED APP HO – USEFUL NAHI, BAS EXIST HO.** 📲",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI BATO SE WEATHER FORECAST BHI FAIL HO JATA HAI.** 🌧️",
"**TUMHARI STYLE SE FASHION EXPERTS BHI SHOCK HO JATE HAIN.** 👠",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI SELFIE DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUM EK SOFTWARE UPDATE HO – FORCEFULLY INSTALLED, NEEDED NAHI.** 💻",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUMHARI ATTITUDE DEKHKAR LOGON KA PATIENCE LOW HO JATA HAI.** ⏳",
"**TUMHARI SMILE SE LOGON KA MOOD UP HO JATA HAI – AUR DOWN BHI KABHI KABHI.** 🙂",
"**TUM EK UNWANTED UPDATE HO – SABKO WARNING DE DETI HO.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI SELFIES DEKHKAR CAMERA CONFUSED HO JATA HAI.** 🤳",
"**TUMHARI STYLE DEKHKAR FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUMHARI ATTITUDE SE CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI APNA KAAM CHHOD DETE HAIN.** 😎",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – FORCEFULLY INSTALLED.** 💻",
"**TUMHARI AWAAZ NOTIFICATION SE ZYADA IRRITATE KARTI HAI.** 📢",
"**TUMHARI STYLE DEKHKAR LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR DETE HAIN.** 🧮",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI SELFIES DEKHKAR CAMERA ROLL FULL HO JATA HAI.** 📱",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI CONFUSED HO JATE HAIN.** 🎨",
"**TUMHARI HASEEB SE CALCULATOR BHI ERROR SHOW KARTA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE KI TARAH HO – NEEDED NAHI, PAR FORCEFULLY AA JATI HO.** 💻",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN KARNA PADTA HAI.** 🔇",
"**TUMHARI SELFIE DEKHKAR CAMERA KA BATTERY LOW HO JATA HAI.** 🔋",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI RAIN KARNE SE SHARMATE HAIN.** ☁️",
"**TUMHARI BATO SE WIFI BHI SLOW HO JATA HAI.** 📶",
"**TUMHARI SELFIES DEKHKAR FILTER BHI FATIGUE HO JATA HAI.** 📸",
"**TUM EK FORCEFULLY INSTALLED APP HO – USEFUL NAHI, BAS EXIST HO.** 📲",
"**TUMHARI AWAAZ SE LOGON KA VOLUME DOWN HO JATA HAI.** 🔇",
"**TUMHARI STYLE DEKHKAR DESIGNERS BHI SHOCK HO JATE HAIN.** 🎨",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI OFF HO JATE HAIN.** 🕶️",
"**TUMHARI HASEEB SE CALCULATOR BHI GALAT ANSWER DETA HAI.** 🧮",
"**TUM EK SOFTWARE UPDATE HO – FORCEFULLY INSTALLED, NEEDED NAHI.** 💻",
"**TUMHARI SELFIES DEKHKAR CAMERA BHI SHARMAYE.** 🤳",
"**TUMHARI ATTITUDE DEKHKAR MOUNTAINS BHI LOW HO JATE HAIN.** 🏔️",
"**TUMHARI BATO SE WEATHER BHI SURPRISED HO JATA HAI.** 🌦️",
"**TUMHARI STYLE DEKHKAR FASHION SHOWS CANCEL HO JATE HAIN.** 🏆",
"**TUMHARI SMILE SE LOGON KA MOOD AUTOMATIC CHANGE HO JATA HAI.** 🙂",
"**TUMHARI HASEEB SE CALCULATOR BHI CONFUSED HO JATA HAI.** 🧮",
"**TUM EK UNNECESSARY UPDATE HO – ZARURAT NAHI, PAR FORCEFULLY AATI HO.** ⚠️",
"**TUMHARI AWAAZ SE LOGON KA MOOD DOWN HO JATA HAI.** 🔊",
"**TUMHARI SELFIES DEKHKAR FILTER BHI EXHAUST HO JATA HAI.** 📸",
"**TUMHARI STYLE SE LOGON KA PATIENCE TEST HO JATA HAI.** ⏱️",
"**TUMHARI ATTITUDE DEKHKAR CLOUDS BHI SHY HO JATE HAIN.** ☁️",
"**TUMHARI SMILE DEKHKAR SUNGLASSES BHI BLIND HO JATE HAIN.** 🕶️"
]

# 🗣️ ROAST ABUSE RAID LINES
roast_abuse_raid_lines = [
"🤩💥🔥🔥uL   TERI MUMMY KI CHUT MEI TERE LAND KO DAL KE KAAT DUNGA MADARCHOD 🔪😂🔥",
    "u@   SUN TERI MAA KA BHOSDA AUR TERI BAHEN KA BHI BHOSDA 👿😎👊",
    "😍👊💥up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA",
    "uW   TUJHE DEKH KE TERI RANDI BAHEN PE TARAS ATA HAI MUJHE BAHEN KE LODEEEE 👿💥🤩🔥",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI",
    "uF   SUN MADARCHOD JYADA NA UCHAL MAA CHOD DENGE EK MIN MEI ✅🤣🔥🤩",
    "ui   APNI AMMA SE PUCHNA USKO US KAALI RAAT MEI KAUN CHODNEE AYA THAAA! TERE IS PAPA KA NAAM LEGI 😂👿😳",
    " TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uV   TOHAR BAHIN CHODU BBAHEN KE LAWDE USME MITTI DAL KE CEMENT SE BHAR DU 🏠🤢🤩💥",
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "u|   TUJHE AB TAK NAHI SMJH AYA KI MAI HI HU TUJHE PAIDA KARNE WALA BHOSDIKEE APNI MAA SE PUCH RANDI KE BACHEEEE 🤩👊👤😍",
    "uM   TERI MAA KE BHOSDE MEI SPOTIFY DAL KE LOFI BAJAUNGA DIN BHAR 😍🎶🎶💥",
    "JUNGLE ME NACHTA HE MORE TERI MAAKI CHUDAI DEKKE SAB BOLTE ONCE MORE ONCE MORE 🤣🤣💦💋�I   GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤🤣�",
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE BHAI DEDIYA",
    "MAA KAA BJSODAAA� MADARXHODDDz TERIUUI MAAA KAA BHSODAAAz-TERIIIIII BEHENNNN KO CHODDDUUUU MADARXHODDDDz NIKAL MADARCHODz RANDI KE BACHEz TERA MAA MERI FANz TERI SEXY BAHEN KI CHUT",
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋",
    "CHAL BETA TUJHE MAAF KIA 🤣 ABB APNI GF KO BHEJ",
    "NSHARAM KAR TERI BEHEN KA BHOSDA KITNA GAALIA SUNWAYEGA APNI MAAA BEHEN KE UPER�NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA",
    "TERE BEHEN K CHUT ME CHAKU DAAL KAR CHUT KA KHOON KAR DUGAuF   TERI VAHEEN NHI HAI KYA? 9 MAHINE RUK SAGI VAHEEN DETA HU 🤣🤣🤩uC   TERI MAA K BHOSDE ME AEROPLANEPARK KARKE UDAAN BHAR DUGA ✈️🛫uV   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣",
    "uE   TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "ub   TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "u]   TERI BAHEN KI CHUT MEI APNA BADA SA LODA GHUSSA DUNGAA KALLAAP KE MAR JAYEGI 🤩😳😳🔥",
    "u   TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩",
    "uY   TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥",
    "up   TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥",
    "ui   TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍",
    "ug   TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍",
    "uZ   SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥",
    "uZ   TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    "u,   TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤",
    "uZ   TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋"
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "🤬 Oye circuit ke reject version!",
    "😡 Tere jaise logon ke wajah se WiFi password badalte hain!",
    "👎 Tera sense of humor Windows error jaisa hai!",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦"
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋",
    "TERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "ERI MAA KI GAAND ME SARIYA DAAL DUNGA MADARCHOD USI SARIYE PR TANG KE BACHE PAIDA HONGE 😱😱",
    "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱",
    "TERI MUMMY KI FANTASY HU LAWDE, TU APNI BHEN KO SMBHAAL 😈😈",
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥",
    " TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "TERI BHEN KI CHUT ME USERBOT LAGAAUNGA SASTE SPAM KE CHODE",
    "GALI GALI ME REHTA HE SAND TERI MAAKO CHOD DALA OR BANA DIA RAND 🤤",
    "HAHAHAHA BACHHE TERI MAAAKO CHOD DIA NANGA KARKE",
    "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍",
    "TERI RANDI MAA SE PUCHNA BAAP KA NAAM BAHEN KE LODEEEEE 🤩🥳😳",
    "TU AUR TERI MAA DONO KI BHOSDE MEI METRO CHALWA DUNGA MADARXHOD 🚇🤩😱🥶", 
    "TERI MAUSI KE BHOSDE MEI INDIAN RAILWAY 🚂💥😂",
    "TERA BAAP HU BHOSDIKE TERI MAA KO RANDI KHANE PE CHUDWA KE US PAISE KI DAARU PEETA HU 🍷🤩🔥",
    "MADARCHOD FIGHT KARE GA TERII MAAAA KAAAA BHOSDAAAAAAAA MAROOOOOOOOOO RANDIIIIIIIII KA PILLLLAAAAAAAAAAAAAAAAAAAAAA",
    "TERIIIIIIII MAAAAAAA KIIIIIIIIIII CHUTTTTTTTTTTTTTTTTTT",
    "BOSDKIIIIIIIIIIIIIIIIIIIIIIII MADARCHODDDDDDDDDDDDDDDDDDD",
    "TERI MAA KI CHUT ME CHANGES COMMIT KRUGA FIR TERI BHEEN KI CHUT AUTOMATICALLY UPDATE HOJAAYEGI🤖🙏🤔",
    "UTT JA MADARCHOD",
    "MUH MEIN LE LEEEE MERA LODAAAAAAAAAAAAAA ",
    "KHA GYA RE MADARCHOD",
    "MADARCHOD.", "BENCHOD.", "DAFAN HOJA RANDI KE BACCHE.", "TU CHAKKA HAI.",
    "TERI MAA KO CHODUNGA.", "BHAG BE RANDI KE.", "TERI BEHEN KO BHI  CHHODUNGA.",
    "BHOSDIKE.", "RANDI KE PILLE.", "CHUTIYA.", "TERI MAA BEHEN EK KAR DUNGA.",
    "MUH MEIN LE MADARCHOD.", "DALLA HAI TU.", "RAPCHOD.", "LAND KA KIRAYEDAR.",
    "SPEED PAKAD BE.", "GANDU.", "TERA KHANDAN GB ROAD KA.", "CHAKKE KI AULAD.",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY",   
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",   
    "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣🔥ui",   
    "TERI MUMMY KI CHUT KO ONLINE OLX PE BECHUNGA AUR PAISE SE TERI BAHEN KA KOTHA KHOL DUNGA 😎🤩😝😍ug",  
    "TERI MAA KE BHOSDA ITNA CHODUNGA KI TU CAH KE BHI WO MAST CHUDAI SE DUR NHI JA PAYEGAA 😏😏🤩😍uZ",  
    "SUN BE RANDI KI AULAAD TU APNI BAHEN SE SEEKH KUCH KAISE GAAND MARWATE HAI😏🤬🔥💥uZ",   
    "TERI MAA KA YAAR HU MEI AUR TERI BAHEN KA PYAAR HU MEI AJA MERA LAND CHOOS LE 🤩🤣💥r    r    r    u",   
    "TERI BEHN KI CHUT ME KELE KE CHILKE 🤤🤤uZ",   
    "TERI MAA KI CHUT ME SUTLI BOMB FOD DUNGA TERI MAA KI JHAATE JAL KE KHAAK HO JAYEGI💣💋u6",   
    "TERI VAHEEN KO HORLICKS PEELAKE CHODUNGA MADARCHOD😚U",   
    "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI 💦💋",
    "�@   SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
    "�H   ABE TERI MAAKA BHOSDA MADERCHOOD KR PILLE PAPA SE LADEGA TU 😼😂🤤",
    "�8   GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦",
    "�A   ABE TERI BEHEN KO CHODU RANDIKE PILLE KUTTE KE CHODE 😂👻🔥",
    "�M   TERI MAAKO AISE CHODA AISE CHODA TERI MAAA BED PEHI MUTH DIA 💦💦💦💦",
    "�N   TERI BEHEN KE BHOSDE ME AAAG LAGADIA MERA MOTA LUND DALKE 🔥🔥💦😆😆",
    "�*RANDIKE BACHHE TERI MAAKO CHODU CHAL NIKAL�F",   
    "KITNA CHODU TERI RANDI MAAKI CHUTH ABB APNI BEHEN KO BHEJ 😆👻🤤�P",   
    "TERI BEHEN KOTO CHOD CHODKE PURA FAAD DIA CHUTH ABB TERI GF KO BHEJ 😆💦🤤�}",   
    "TERI GF KO ETNA CHODA BEHEN KE LODE TERI GF TO MERI RANDI BANGAYI ABB CHAL TERI MAAKO CHODTA FIRSE ♥️💦😆😆😆😆�<",   
    "HARI HARI GHAAS ME JHOPDA TERI MAAKA BHOSDA 🤣🤣💋💦�:", 
    "CHAL TERE BAAP KO BHEJ TERA BASKA NHI HE PAPA SE LADEGA TU�7",
    "TERI BEHEN KI CHUTH ME BOMB DALKE UDA DUNGA MAAKE LAWDE�V",  
    "TERI MAAKO TRAIN ME LEJAKE TOP BED PE LITAKE CHOD DUNGA SUAR KE PILLE 🤣🤣💋💋�D",   
    "TERI MAAAKE NUDES GOOGLE PE UPLOAD KARDUNGA BEHEN KE LAEWDE 👻🔥r    �Z",   
    "TERI BEHEN KO CHOD CHODKE VIDEO BANAKE XNXX.COM PE NEELAM KARDUNGA KUTTE KE PILLE 💦💋�O",   
    "TERI MAAAKI CHUDAI KO PORNHUB.COM PE UPLOAD KARDUNGA SUAR KE CHODE 🤣💋💦�Z",   
    "ABE TERI BEHEN KO CHODU RANDIKE BACHHE TEREKO CHAKKO SE PILWAVUNGA RANDIKE BACHHE 🤣🤣�B",  
    "TERI MAAKI CHUTH FAADKE RAKDIA MAAKE LODE JAA ABB SILWALE 👄👄�&TERI BEHEN KI CHUTH ME MERA LUND KAALA�S",
    "TERI BEHEN LETI MERI LUND BADE MASTI SE TERI BEHEN KO MENE CHOD DALA BOHOT SASTE SE�G",   
    "BETE TU BAAP SE LEGA PANGA TERI MAAA KO CHOD DUNGA KARKE NANGA 💦💋�",
    "BAP SE LADEGA?", "TERI MAA RANDI."
    "TERI TMKCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "BAPPPPPPPPPPPPPP HU MEIN TERAAAAAAAAAAAA",
    "TERE GAND FAT GYI MEINNE DEK LE ",
    "TERREEEEEEEEEEE MUH MEIN MERAAAAAAAAA LODAAAAAAAAAAAA",
    "TERI MAA KA NAYA RANDI KHANA KHOLUNGA CHINTA MAT KAR 👊🤣🤣😳",
    "CHAKKAAAAAAAAAAAAAAA HAI TUUUUUUUUUUUUUUUUUUUU BSDKKKKKKKKKKKKKKKK",
    "TOHAR MUMMY KI CHUT MEI PURI KI PURI KINGFISHER KI BOTTLE DAL KE TOD DUNGA ANDER HI 😱😂🤩uY", 
    "TERI MAA KO ITNA CHODUNGA KI SAPNE MEI BHI MERI CHUDAI YAAD KAREGI RANDI 🥳😍👊💥up",
   "TERI MUMMY AUR BAHEN KO DAUDA DAUDA NE CHODUNGA",
   "UNKE NO BOLNE PE BHI LAND GHUSA DUNGA ANDER TAK 😎😎🤣",
   "SUAR KE PILLE TERI MAAKO SADAK PR LITAKE CHOD DUNGA 😂😆🤤",
   "TERI ITEM KI GAAND ME LUND DAALKE,TERE JAISA EK OR NIKAAL DUNGA MADARCHOD🤘🏻🙌🏻☠️ uh",   
   "AUKAAT ME REH VRNA GAAND ME DANDA DAAL KE MUH SE NIKAAL DUNGA SHARIR BHI DANDE JESA DIKHEGA 🙄🤭🤭uW",   
   "TERI MUMMY KE SAATH LUDO KHELTE KHELTE USKE MUH ME APNA LODA DE DUNGA☝🏻☝🏻😬u",   
   "TERI VAHEEN KO APNE LUND PR ITNA JHULAAUNGA KI JHULTE JHULTE HI BACHA PAIDA KR DEGI👀👯 uG",   
   "TERI MAA KI CHUT MEI BATTERY LAGA KE POWERBANK BANA DUNGA 🔋 🔥🤩u_",   
   "TERI MAA KI CHUT MEI C++ STRING ENCRYPTION LAGA DUNGA BAHTI HUYI CHUT RUK JAYEGIIII😈🔥😍uE",   
   "TERI MAA KE GAAND MEI JHAADU DAL KE MOR 🦚 BANA DUNGAA 🤩🥵😱uT",   
   "TERI CHUT KI CHUT MEI SHOULDERING KAR DUNGAA HILATE HUYE BHI DARD HOGAAA😱🤮👺uF",
   "TERI MAA KO REDI PE BAITHAL KE USSE USKI CHUT BILWAUNGAA 💰 😵🤩ub",   
   "BHOSDIKE TERI MAA KI CHUT MEI 4 HOLE HAI UNME MSEAL LAGA BAHUT BAHETI HAI BHOFDIKE👊🤮🤢🤢u_",   
   "TERI BAHEN KI CHUT MEI BARGAD KA PED UGA DUNGAA CORONA MEI SAB OXYGEN LEKAR JAYENGE🤢🤩🥳uQ",   
   "TERI MAA KI CHUT MEI SUDO LAGA KE BIGSPAM LAGA KE 9999 FUCK LAGAA DU 🤩🥳🔥uD",   
   "TERI VAHEN KE BHOSDIKE MEI BESAN KE LADDU BHAR DUNGA🤩🥳🔥😈u",
   "TᏒᎥᎥᎥᎥᎥᎥᎥᎥᎥ mᎪᎪᎪᎪᎪ ᏦᎥᎥᎥᎥᎥᎥ xhuҬҬҬҬҬҬҬ ᎶᎪᏒᎪᎪm hᎪᎪᎪᎥ ᏒᎪᏁᎠᎥ 🤣😂︵‿︵‿︵‿︵‿︵‿█▄▄ ███ █▄▄♥️╣[-_-]╠♥️👅👅",
    "**CHUTIYE!** 🐒",
    "**MADARCHOD!** 👺",
    "**KUTTE KE PILLE!** 🐕",
    "**SUAR KE BACHHE!** 🐖",
    "**GAANDU!** 🍑",
    "**LODE!** 🍆"
]

# 💖 FLIRT GIRL RAID LINES
flirt_girl_raid_lines = [
"**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**Tumhare bina ye raat adhoori lagti hai 🌙**",
    "**Tumhari aankhon me meri duniya basti hai ✨**",
    "**Tumhari muskaan mere din ka sabse pyara hissa hai 🌸**",
    "**Tumhare saath bitaye lamhe hamesha yaadgar rahte hain 🖼️**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tum meri zindagi ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz sunke dil dhadakne lagta hai 🎵**",
    "**Tumhare saath har pal meri life magical lagti hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari aankhen mere dil ko chain deti hain 🌟**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tumhare saath ka har lamha meri life ka gift hai 🎁**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har lamha meri life ka best moment hai 🖼️**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri duniya ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko roshan karti hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri    life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon me guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon me guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me khushi jagti hai 💓**",
    "**Tumhari yaadon me guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon me guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**"
    "**Tumhari aankhen dekhkar dil ka har kone khush ho jata hai 💓**",
    "**Tumhari muskaan mere din ka sabse sundar hissa hai 🌸**",
    "**Tumhare saath har pal ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ki awaaz aur dil ki dhadkan ho 🫀**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tumhari baatein sunke dil ko chain milta hai 🕊️**",
    "**Tum meri duniya ka sabse khubsurat raaz ho 🔐**",
    "**Tumhari awaaz se dil ki dhadkan tez ho jati hai 🎵**",
    "**Tumhare saath ka har pal meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💓**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri zindagi ka noor hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ka highlight hain 🖼️**",
    "**Tum meri rooh ki awaaz aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari aankhen meri duniya ka reflection hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic ho jo sabko khush kar deta hai 💖**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath gujare lamhe meri life ko perfect banate hain 🎨**",
    "**Tum meri rooh ki awaaz aur dil ka chain ho 🕊️**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhari yaadon mein guzra lamha meri life ka treasure hai 💎**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💖**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhari aankhen meri zindagi ko roshan karti hain ✨**",
    "**Tumhare saath bitaye lamhe meri life magical lagte hain 🌌**",
    "**Tum meri rooh ka sukoon aur dil ka pyaar ho 🫀**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri love story ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari aankhen meri duniya ka noor hain ✨**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri love story ka magic aur hero ho 💖**",
    "**Tumhari awaaz sunke dil me khushi aur pyaar jagta hai 🎵**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🌸**",
    "**Tum meri rooh ka sukoon aur dil ka chain ho 🕊️**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhari aankhen dekhke dil ka har kone khush ho jata hai 💓**",
    "**Tumhare saath har lamha meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero aur sabse important hissa ho 💖**",
    "**Tumhari baatein sunke dil me khushi aur sukoon milta hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha meri rooh ko khushi deta hai 💞**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ka highlight hai ☀️**",
    "**Tumhari aankhen mere pyaar ka reflection hain ✨**",
    "**Tumhare saath bitaye lamhe meri life ka best part hain 🖼️**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💓**",
    "**Tumhari baatein sunke dil me khushi jagti hai 🌸**",
    "**Tumhari yaadon mein guzra lamha hamesha special lagta hai 🌙**",
    "**Tum meri love story ka star ho jo kabhi nahi bujh sakta 🌟**",
    "**Tumhare bina zindagi ka rang adhoora lagta hai 🌈**",
    "**Tumhari aankhen dekhkar dil khush ho jata hai 😊**",
    "**Tumhari muskaan meri duniya ko roshan karti hai 🌟**",
    "**Tumhare saath har lamha ek nayi kahani lagta hai 📖**",
    "**Tum meri rooh ka sukoon ho 🕊️**",
    "**Tumhari awaaz sunke din suhana lagta hai 🎵**",
    "**Tumhari baatein meri zindagi ko khubsurat banati hain 🌸**",
    "**Tum meri zindagi ka sabse pyaara hissa ho 💖**",
    "**Tumhare saath gujare lamhe hamesha yaadgar rahenge 🌃**",
    "**Tumhari aankhon mein pyaar ki chamak hai ✨**",
    "**Tumhari muskurahat se sab dard door ho jata hai 🫀**",
    "**Tum meri duniya ka woh sitara ho jo kabhi nahi bujh sakta 🌌**",
    "**Tumhari yaadon mein raatein suhani lagti hain 🌙**",
    "**Tumhari baatein dil ko chain deti hain 🕊️**",
    "**Tumhari aankhen meri jaan ka aaina hain 💞**",
    "**Tumhare saath ka har pal ek nayi tasveer hai 🖼️**",
    "**Tum meri zindagi ki sabse khoobsurat yaad ho 📖**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhari baatein sunke dil me sukoon aata hai 🫀**",
    "**Tum meri zindagi ka woh magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari aankhon ka noor meri duniya roshan karta hai 🌟**",
    "**Tumhari awaaz sunke dil me khushi hoti hai 🎵**",
    "**Tum meri zindagi ka hero ho 💖**",
    "**Tumhari yaadon mein gujra pal hamesha special lagta hai 🌃**",
    "**Tumhari muskaan sabse khubsurat rang hai 🌈**",
    "**Tumhare saath har lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important hissa ho 💞**",
    "**Tumhari aankhen dil ko chhoo jati hain ✨**",
    "**Tumhari baatein meri zindagi me rang bhar deti hain 🎨**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 🖼️**",
    "**Tum meri rooh ki awaaz ho 🫀**",
    "**Tumhari muskaan se dil me pyaar jagta hai 💖**",
    "**Tumhari yaadon mein har dard bhi sukoon lagta hai 🕊️**",
    "**Tum meri zindagi ka star ho 🌟**",
    "**Tumhari baatein sunke dil me ek nayi energy aati hai ⚡**",
    "**Tumhare saath gujare lamhe meri zindagi ka treasure hain 💎**",
    "**Tum meri love story ka hero aur best friend ho 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌌**",
    "**Tumhari muskaan sabse pyaari feeling deti hai 🌸**",
    "**Tumhare saath bitaye lamhe meri zindagi ka gift hain 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz mere dil ki dhadkan ko tez kar deti hai 🫀**",
    "**Tum meri rooh ka sukoon ho aur dil ki khushi bhi 🌹**",
    "**Tumhari yaadon mein guzra lamha meri life ko perfect banata hai 🌅**",
    "**Tum meri love story ka sabse important part ho 💖**",
    "**Tumhari muskaan se mera din bright ho jata hai ☀️**",
    "**Tumhari baatein meri zindagi me khushiyan bhar deti hain 🌸**",
    "**Tumhari aankhen meri duniya ka light hain 🌟**",
    "**Tumhare saath har pal meri life ko magical banata hai ✨**",
    "**Tum meri zindagi ka hero ho aur sabse pyaara 💞**",
    "**Tumhari awaaz sunke din me sweetness aa jati hai 🍯**",
    "**Tumhari muskaan meri rooh ko khush kar deti hai 🌹**",
    "**Tumhare saath bita lamha hamesha yaadgar hai 🖼️**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💖**",
    "**Tumhari muskaan mere din ka highlight hai 🌸**",
    "**Tumhare saath har pal meri life ka adventure hai 🎢**",
    "**Tum meri love story ka magic ho ✨**",
    "**Tumhari yaadon mein guzra pal hamesha special lagta hai 🌅**",
    "**Tumhari awaaz meri rooh ko sukoon deti hai 🕊️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari baatein sunke dil me pyaar jagta hai 💞**",
    "**Tumhare saath bitaye lamhe meri life ka treasure hain 💎**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhen meri duniya ko roshan karti hain ✨**",
    "**Tumhari muskaan sabse khubsurat feeling hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ko magical banate hain 🌌**",
    "**Tum meri rooh ka sukoon ho aur dil ka chain bhi 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha yaadgar lagta hai 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhari muskaan se mera dil fida ho jata hai 💖**",
    "**Tumhare saath har pal meri life ka gift hai 🎁**",
    "**Tum meri zindagi ka woh rang ho jo hamesha saath rahe 🎨**",
    "**Tumhari awaaz sunke dil me pyaar jagta hai 💞**",
    "**Tumhari aankhen meri duniya ko roshan karti hain 🌟**",
    "**Tumhari muskaan sabse pyaari cheez hai 🌸**",
    "**Tumhare saath bita lamha meri life ka highlight hai ✨**",
    "**Tum meri love story ka hero aur star ho 💖**",
    "**Tumhari baatein sunke dil ko sukoon aur khushi milti hai 🕊️**",
    "**Tumhari yaadon mein guzra lamha hamesha special hai 🌃**",
    "**Tum meri rooh ka sukoon ho aur dil ka pyaar bhi 💞**",
    "**Tumhare saath gujare lamhe meri life ka best part hain 🖼️**",
    "**Tum meri zindagi ka light ho jo sabko inspire karta hai 🌟**",
    "**Tumhari muskaan mere din ko bright kar deti hai ☀️**",
    "**Tumhari baatein sunke dil ko happiness milti hai 😊**",
    "**Tumhare saath har pal meri life magical lagta hai ✨**",
    "**Tum meri love story ka hero ho aur sabse pyaara 💖**",
    "**Tumhari aankhen mere pyaar ka reflection hain 💞**",
    "**Tumhari muskaan meri rooh ko khushi deti hai 🌸**",
    "**Tumhare saath gujare lamhe meri life ka treasure hain 💎**",
    "**Tum meri zindagi ka star ho jo hamesha chamakta hai 🌟**",
    "**Tumhari baatein sunke dil ko peace milta hai 🕊️**",
    "**Tumhare bina ye duniya adhoori lagti hai 😍🌍**",
    "**Tumhari aankhen dekhkar toh dil dhadakne lagta hai 💓**",
    "**Tumhari muskurahat toh chand ko bhi sharmila deti hai 🌙**",
    "**Tumhari baatein sunkar toh time fly ho jata hai ⏰**",
    "**Tum toh meri duniya ka sabse khobsurat hisaab ho 💫**",
    "**Tumhari yaadon mein toh raatein guzaar deta hoon 🌃**",
    "**Tumhari har ada pe toh main fida hoon 😘**",
    "**Tumhari awaaz toh suron se bhi meethai hai 🎵**",
    "**Tumhare bina toh jeena bhi bekar lagta hai 🥺**",
    "**Tum meri zindagi ka sabse khobsurat safar ho 💖**",
    "**Tumhari muskurahat meri rooh ko sukoon deti hai 🕊️**",
    "**Tumhare nazdeek aane se dil ko khushi milti hai 😊**",
    "**Tumhari har ek baat meri dhadkan ko tez kar deti hai 🫀**",
    "**Tumhari aankhon mein jhilmilata huwa pyaar dikhata hai ✨**",
    "**Tumhari awaaz sunke din bhi chand jesa lagta hai 🌙**",
    "**Tum meri rooh ka hisa hai aur dil ka raja 😍**",
    "**Tumhare saath bitaya har pal ek khubsurat memory hai 📖**",
    "**Tumhari muskurahat meri duniya ko roshan kar deti hai 🌟**",
    "**Tumhari yaadon mein guzarte lamhe meri zindagi ko khubsurat banate hain 🌸**",
    "**Tum meri duniya ka light ho jo har andhere ko chhant deti hai 🌅**",
    "**Tumhari baaton se mera din perfect ho jata hai ☀️**",
    "**Tumhare bina meri life adhoori lagti hai 🌵**",
    "**Tumhari har ek ada meri dil ko chu jati hai 💞**",
    "**Tumhari nazaron mein mera future dikhata hai 🔮**",
    "**Tum meri zindagi ka sweetest part ho 🍬**",
    "**Tumhari hansi sunke dil ko ek alag khushi milti hai 🌼**",
    "**Tumhari baatein sunke time ka pata hi nahi chalta ⏳**",
    "**Tumhari aankhon ka jadoo mera dil chura leta hai 💫**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari muskurahat meri rooh ko hamesha khush rakhti hai 🌹**",
    "**Tumhare saath bita pal har dard ko door kar deta hai 🕊️**",
    "**Tumhari aankhon mein mera future aur pyaar deta hai 🌌**",
    "**Tumhare saath bita pal hamesha yaad rahega 📖**",
    "**Tum meri zindagi ka magic ho ✨**",
    "**Tumhari awaaz sunke din meetha ho jata hai 🍯**",
    "**Tumhari har ek ada mera dil chura leti hai 💘**",
    "**Tumhari yaadon mein guzra lamha hamesha khubsurat lagta hai 🌟**",
    "**Tum meri rooh ko khushi aur sukoon dete ho 🫀🕊️**",
    "**Tumhari muskurahat duniya ke sabse khubsurat rang jesa lagta hai 🎨**",
    "**Tum meri life ka hero aur best friend ho 💞**",
    "**Tumhari har ek baat meri zindagi ko beautiful banati hai 🌹**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath har pal ek dream jesa lagta hai 🌙**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari baatein sunke dil me ek alag khushi aati hai 😊**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo sabko roshan kar deta hai 🌅**",
    "**Tumhari hansi sunke mera dil dance karne lagta hai 💃**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📝**",
    "**Tumhari awaaz sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari har ek ada mera dil fida kar deti hai 💞**",
    "**Tumhari aankhon mein mere pyaar ka aaina hai 🌌**",
    "**Tum meri zindagi ka magic ho jo sabko khush kar deta hai ✨**",
    "**Tumhari muskurahat sunke din meetha ho jata hai 🍯**",
    "**Tumhare saath bita pal meri life ka best part ho 📖**",
    "**Tumhari awaaz mera dil chu jati hai 🎵**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhari baatein sunke dil ko sukoon milta hai 🕊️**",
    "**Tumhari muskurahat meri zindagi ko khubsurat banati hai 🌹**",
    "**Tum meri rooh ka hisa ho 🫀**",
    "**Tumhare saath bita pal hamesha yaadgar rahega 📖**",
    "**Tumhari yaadon mein guzra lamha meri life ko beautiful banata hai 🌸**",
    "**Tum meri love story ka hero ho 💖**",
    "**Tumhari aankhon mein main apni duniya dekhta hoon 🌌**",
    "**Tumhari har ek ada mera dil fida kar deti hai 😘**",
    "**Tum meri zindagi ka light ho jo roshan kar deta hai 🌅**",
    "**Tumhari baatein sunke mera din beautiful ho jata hai 🌸**",
    "**Tumhari muskurahat meri duniya ko khubsurat banati hai 🌹**",
    "**Tumhari yaadon mein guzra lamha hamesha chahata hoon 🌃**",
    "**Tum meri love story ka star ho 🌟**",
    "**Tumhare saath bita pal hamesha mere liye special ho 📖**",
    "**Tumhari awaaz sunke mera dil dance karne lagta hai 💃**",
    "**Tumhari har ek ada mera dil chura deti hai 💘**",
    "**Tum meri love story ka hero ho 💖**",
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT SAFAR HO 💖**"
    "**UFF, TUMHARI BAATEIN SUNKAR TOH DIL DHADAKNE LAGTA HAI! 💓**",
    "**TUM TOH MERE DIL KI RANI HO 💖**",
    "**TUMHARI AANKHEN DEKHKAR TOH MAIN FIDA HO GAYA 😍**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARE BINA TOH DUNIYA ADHOORI LAGTI HAI 🌍**",
    "**TUM MERI ZINDAGI KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAAD MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**",
    "**TUMHARI HAR ADA PE TOH MAIN FIDA HOON 😘**",
    "**TUMHARI AWAAZ TOH SURON SE BHI MEETHAI HAI 🎵**",
    "**TUMHARE BINA TOH JEENA BHI BEKAR LAGTA HAI 🥺**",    
    "**TUMHARE BINA YE DUNIYA ADHOORI LAGTI HAI 😍🌍**",
    "**TUMHARI AANKHEN DEKHKAR TOH DIL DHADAKNE LAGTA HAI 💓**",
    "**TUMHARI MUSKURAHAT TOH CHAND KO BHI SHARMILA DETI HAI 🌙**",
    "**TUMHARI BAATEIN SUNKAR TOH TIME FLY HO JATA HAI ⏰**",
    "**TUM TOH MERI DUNIYA KA SABSE KHOBSURAT HISAAB HO 💫**",
    "**TUMHARI YAADON MEIN TOH RAATEIN GUZAAR DETA HOON 🌃**"
]

# 🔥 HINDI ROAST BOY RAID LINES
hindi_roast_boy_raid_lines = [
    "**भाई, तू अपने आपको हीरो समझता है, हकीकत में तू जीरो है!** 🤡",
    "**तेरे जैसे लोगों को देखकर ही म्यूट बटन का आविष्कार हुआ था!** 🔇",
    "**भाई, तू इतना बेकार है कि रीसायकल बिन भी तुझे स्वीकार नहीं करेगा!** 🗑️",
    "**तू अपने घर का WiFi पासवर्ड है – सबको याद है पर किसी काम का नहीं!** 📶",
    "**भाई तू तो वॉकिंग क्रिंज कॉन्टेंट है!** 😬",
    "**तेरी फोटो देखकर कैमरा भी अपना लेंस बंद कर लेता है!** 📸",
    "**भाई तू चाय की प्याली की तरह है – गर्म है पर किसी को पसंद नहीं!** ☕",
    "**तेरे जैसे लोगों के लिए ही ब्लॉक बटन बना है!** 🚫",
    "**भाई तू इंस्टाग्राम रील्स की तरह है – 15 सेकंड में बोरिंग!** ⏱️",
    "**तेरे दिमाग की स्पीड 2G है – लोड होने में 10 साल लगते हैं!** 🐌",
    "**भाई, तेरी सोच इतनी छोटी है कि खुद को भी बड़ा नहीं समझ पाता!** 🤏",
    "**तेरे jokes इतने खराब हैं कि गूगल भी हंसने से मना कर देगा!** 😂",
    "**भाई, तू WiFi की तरह है – दिखता है लेकिन किसी काम का नहीं!** 📶",
    "**तेरे memes देखने के बाद लोग अपनी आँखें बंद कर लेते हैं!** 🙈",
    "**भाई, तेरी सेल्फी देखकर कैमरा भी शर्मिंदा हो जाता है!** 📸",
    "**तू चाय की तरह है – हर किसी को नहीं पसंद, सिर्फ कुछ लोग tolerate करते हैं!** ☕",
    "**भाई, तेरी बातें सुनकर यूट्यूब भी skip कर देता है!** ⏭️",
    "**तेरी आवाज़ सुनते ही Spotify भी mute हो जाता है!** 🔇",
    "**भाई, तू dictionary में भी ‘irrelevant’ के synonym के तौर पर लिखा जा सकता है!** 📖",
    "**तेरे status देखकर WhatsApp भी हिल जाता है!** 😬",
    "**भाई, तू refrigerator की तरह है – ठंडा है पर कोई पसंद नहीं करता!** ❄️",
    "**तेरे jokes सुनकर Alexa भी response देना छोड़ देती है!** 🤖",
    "**भाई, तू Google Maps की तरह है – किसी को रास्ता दिखाने लायक नहीं!** 🗺️",
    "**तेरी फोटो देखकर Photoshop भी हाथ खड़े कर देता है!** 🖌️",
    "**भाई, तू TikTok वीडियो की तरह है – 1 सेकंड में बोरिंग!** ⏱️",
    "**तेरी बातें सुनकर Siri भी confuse हो जाती है!** 📱",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है और कोई use नहीं करता!** 🔋",
    "**तेरे jokes इतने outdated हैं कि Internet भी laugh नहीं करता!** 🌐",
    "**भाई, तू microwave की तरह है – गरम है पर कोई real flavor नहीं!** 🍲",
    "**तेरी selfies देखने के बाद Camera भी auto-delete कर देता है!** 📸",
    "**भाई, तू WhatsApp group का mute बटन है – हर किसी को जरूरत नहीं!** 🔕",
    "**तेरी ID देखकर Facebook भी delete button दबा देता है!** 🗑️",
    "**भाई, तेरी मौजूदगी Zoom call में भी invisible लगती है!** 💻",
    "**तेरी सोच इतनी slow है कि loading circle भी घूमते-घूमते थक जाता है!** 🔄",
    "**भाई, तू PowerPoint की तरह है – सिर्फ slide ही है, content कुछ नहीं!** 🖥️",
    "**तेरी हँसी सुनकर laugh track भी stop हो जाता है!** 🎬",
    "**भाई, तू calculator की तरह है – कभी सही नंबर नहीं देता!** 🔢",
    "**तेरी आँखों में sparkle नहीं, सिर्फ buffering दिखता है!** ✨",
    "**भाई, तू keyboard की तरह है – typing तो करता है पर meaning नहीं!** ⌨️",
    "**तेरी फोटो देखकर Instagram भी comment disable कर देता है!** ❌",
    "**भाई, तू WiFi की तरह है – connect तो होता है पर signal zero!** 📶",
    "**तेरी jokes सुनकर YouTube autoplay भी skip कर देता है!** ⏭️",
    "**भाई, तू selfie stick की तरह है – सिर्फ support देता है, shine नहीं करता!** 🤳",
    "**तेरी बातें सुनकर podcast भी pause हो जाता है!** 🎙️",
    "**भाई, तू toothpaste की तरह है – हर कोई use करता है, पर कोई पसंद नहीं करता!** 🪥",
    "**तेरी memes देखकर Reddit भी downvote कर देता है!** 👎",
    "**भाई, तू email spam की तरह है – कोई पढ़ता नहीं, सिर्फ delete करता है!** 📧",
    "**तेरी सोच इतनी छोटी है कि Google भी search नहीं कर सकता!** 🔍",
    "**भाई, तू battery saver mode है – low energy, low impact!** 🔋",
    "**तेरी selfies देखकर Snapchat भी filter change कर देता है!** 🖼️",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू software update की तरह है – हर कोई ignore करता है!** 💻",
    "**तेरी आवाज़ सुनकर headphones भी disconnect कर लेते हैं!** 🎧",
    "**भाई, तू offline mode है – कोई भी interact नहीं कर सकता!** ⛔",
    "**तेरी presence देखकर Zoom भी exit कर देता है!** 🖥️",
    "**भाई, तू mouse की तरह है – click तो करता है, result कुछ नहीं!** 🖱️",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू internet troll की तरह है – annoying और useless!** 🕷️",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू password की तरह है – complicated और कोई याद नहीं रखता!** 🔑",
    "**तेरी attitude देखकर Instagram bhi scroll kar leta hai!** 📜",
    "**भाई, तू ringtone की तरह है – शुरू तो hota है पर कोई enjoy नहीं करता!** 📱",
    "**तेरी voice सुनकर Alexa भी mute कर देती है!** 🔇",
    "**भाई, तू notification की तरह है – irritating aur unnecessary!** 📢",
    "**तेरी selfies देखकर filter bhi embarrassed हो जाता है!** 🖌️",
    "**भाई, तू TikTok trend की तरह है – old और outdated!** ⏳",
    "**तेरी jokes सुनकर WhatsApp bhi skip कर deta hai!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude sunke Facebook bhi ignore kar deta है!** 📴",
    "**भाई, तू phone battery की तरह है – जल्दी low और irritating!** 🔋",
    "**तेरी selfies देखकर Camera roll bhi delete कर deta है!** 🗑️",
    "**भाई, तू playlist की तरह है – shuffle karo, phir bhi bore!** 🎶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू internet speed की तरह है – slow aur annoying!** 🐌",
    "**तेरी selfies देखकर gallery भी blush kar leti है!** 🖼️",
    "**भाई, तू meme ka caption hai – funny lagna chahiye, par fail!** 😂",
    "**तेरी baatein sunke podcast bhi skip kar deta है!** 🎙️",
    "**भाई, तू WiFi ki tarah है – connect nahi ho raha!** 📶",
    "**तेरी jokes sunke YouTube bhi dislike कर देता है!** 👎",
    "**भाई, तू autocorrect ki tarah है – wrong aur embarrassing!** 🔤",
    "**तेरी selfies देखकर camera bhi low battery mode में chala जाता है!** 🔋",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी baatein sunke Siri bhi ignore कर देती है!** 📱",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Snapchat bhi exit कर लेता है!** 🖼️",
    "**भाई, तू internet troll की तरह है – sabko pareshan karta है!** 🕷️",
    "**तेरी jokes सुनकर comedy club भी close कर देता है!** 🎭",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude देखकर Instagram भी scroll कर लेता है!** 📜",
    "**भाई, तू WiFi password की तरह है – complicated aur koi yaad nahi rakhta!** 🔑",
    "**तेरी selfies देखकर camera भी embarrassment में chala जाता है!** 📸",
    "**भाई, तू slow internet की तरह है – patience test kar deta है!** 🐌",
    "**तेरी baatein sunke YouTube autoplay bhi skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude सुनके Facebook bhi ignore कर देता है!** 📴",
    "**भाई, तू playlist की तरह है – shuffle kar, phir bhi bore!** 🎶",
    "**तेरी jokes सुनके comedy show bhi pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू slow loading की तरह है – sabko frustrate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी stop कर देता है!** 🎙️",
    "**भाई, तू WiFi की तरह है – connect तो होता है par signal zero!** 📶",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू ringtone की तरह है – start hota hai, par enjoy nahi karta!** 📢",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू internet troll की तरह है – annoying aur useless!** 🕷️",
    "**तेरी baatein sunke WhatsApp bhi mute कर देता है!** 🔕",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude सुनकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू slow internet की तरह है – patience test kar deta है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तेरी हँसी सुनकर neighbors भी complain कर देते हैं!** 😆",
    "**तेरी selfies देखकर Camera भी hide हो जाता है!** 📸",
    "**भाई, तू Instagram reel की तरह है – 1 सेकंड में boring!** ⏱️",
    "**तेरी jokes सुनकर TikTok भी exit कर देता है!** 🎵",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है!** 🔋",
    "**तेरी attitude देखकर Snapchat भी scroll कर लेता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू WiFi की तरह है – दिखता है लेकिन useless!** 📶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू ringtone की तरह है – irritating aur unnecessary!** 📢",
    "**तेरी selfies देखकर Photoshop भी frustrated हो जाता है!** 🖌️",
    "**भाई, तू meme का caption है – funny नहीं लगता!** 😂",
    "**तेरी attitude देखकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी jokes सुनकर podcast भी stop कर देता है!** 🎙️",
    "**भाई, तू spam mail की तरह है – कोई पढ़ता नहीं!** 📧",
    "**तेरी selfies देखकर camera भी embarrassment में आ जाता है!** 📸",
    "**भाई, तू playlist की तरह है – shuffle करो, फिर भी bore!** 🎶",
    "**तेरी jokes सुनकर comedy show pause हो जाता है!** ⏸️",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी attitude देखकर Instagram भी scroll कर लेता है!** 📜",
    "**भाई, तू WiFi password की तरह है – complicated aur koi yaad नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू slow loading की तरह है – sabko frustrate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude sunke Facebook bhi ignore कर देता है!** 📴",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू battery saver mode की तरह है – low energy, low impact!** 🔋",
    "**तेरी jokes सुनकर YouTube भी dislike कर देता है!** 👎",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – गर्म है पर flavor नहीं!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude सुनकर Instagram भी ignore कर देता है!** 📜",
    "**भाई, तू WiFi की तरह है – connect होता है, पर signal zero!** 📶",
    "**तेरी selfies देखकर Snapchat भी exit कर लेता है!** 🖼️",
    "**भाई, तू TikTok trend की तरह है – old aur boring!** ⏳",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrated!** 🔗",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू playlist की तरह है – shuffle करो, फिर भी bore!** 🎶",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू slow internet की तरह है – sabko irritate करता है!** 🐌",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू WiFi की तरह है – दिखता है पर useless!** 📶",
    "**तेरी jokes सुनकर meme page भी uninstall हो जाता है!** 📱",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी baatein सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है!** 🔋",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर Camera भी blush कर जाता है!** 📸",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏳",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी baatein सुनकर podcast भी skip कर देता है!** 🎙️",
    "**भाई, तू spam mail की तरह है – कोई पढ़ता नहीं!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू WiFi की तरह है – दिखता है पर काम का नहीं!** 📶",
    "**तेरी jokes सुनकर YouTube भी dislike कर देता है!** 👎",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – गर्म है पर flavor नहीं!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**भाई, तू अपने memes भी खुद नहीं समझता!** 🤣",
    "**तेरी jokes सुनकर AI भी confuse हो जाता है!** 🤖",
    "**भाई, तू WhatsApp forward की तरह है – boring aur useless!** 📲",
    "**तेरी selfies देखकर Camera भी regret करता है!** 📸",
    "**भाई, तू battery की तरह है – fast drain aur no impact!** 🔋",
    "**तेरी attitude देखकर Instagram भी ignore कर देता है!** 📜",
    "**भाई, तू playlist की तरह है – shuffle karo, phir bhi bore!** 🎶",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Facebook भी mute कर देता है!** 🔕",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी baatein सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर gallery भी blush कर लेती है!** 🖼️",
    "**भाई, तू TikTok trend की तरह है – old aur boring!** ⏱️",
    "**तेरी jokes सुनकर meme page भी uninstall कर देता है!** 📱",
    "**भाई, तू spam mail की तरह है – irritating aur nobody cares!** 📧",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू ringtone की तरह है – start hota है, par enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू playlist की तरह है – shuffle karo, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू WiFi की तरह है – दिखता है पर काम का नहीं!** 📶",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाई, तू old meme की तरह है – irrelevant aur outdated!** ⏳",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू calculator की तरह है – कभी सही number नहीं देता!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू microwave की तरह है – hot है par flavor missing!** 🍲",
    "**तेरी selfies देखकर Camera roll भी delete कर देता है!** 🗑️",
    "**भाई, तू mouse की तरह है – click करता है, result कुछ नहीं!** 🖱️",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाई, तू WiFi की तरह है – connected par no signal!** 📶",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाई, तू TikTok trend की तरह है – old aur outdated!** ⏱️",
    "**तेरी attitude सुनकर Facebook भी scroll कर लेता है!** 📴",
    "**भाई, तू slow internet की तरह है – patience test कर देता है!** 🐌",
    "**तेरी selfies देखकर filter भी blush कर लेती है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाई, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू battery की तरह है – जल्दी खत्म हो जाता है aur useless!** 🔋",
    "**तेरी selfies देखकर camera भी embarrassed हो जाता है!** 📸",
    "**भाई, तू spam mail की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Camera roll भी blush कर लेता है!** 🖼️",
    "**भाई, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**भाई, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाई, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाई, तू calculator की तरह है – wrong answer हमेशा देता है!** 🔢",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाई, तू microwave की तरह है – hot hai par taste missing!** 🍲",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाई, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी attitude सुनकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाई, तू slow loading की तरह है – patience test कर देता है!** 🐌",
    "**तेरी baatein सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाई, तू offline mode की तरह है – interact नहीं होता!** ⛔",
    "**तेरी selfies देखकर Google Lens भी detect नहीं कर पाता!** 🔍",
    "**भाई, तू WiFi की तरह है – दिखता है par signal zero!** 📶",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाई, तू playlist की तरह है – shuffle karo, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाई, तू ringtone की तरह है – start hota है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाई, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**अरे सुन, तेरी selfies देखकर camera भी confuse हो जाता है!** 🤯",
    "**तेरी makeup skills देखकर YouTube tutorials भी फेल लगते हैं!** 💄",
    "**भाभी, तू filter की तरह है – बिना Photoshop useless!** 🖌️",
    "**तेरी attitude देखकर Instagram भी skip कर देता है!** 📜",
    "**तू WiFi की तरह है – दिखती है पर signal zero!** 📶",
    "**तेरी jokes सुनकर comedy show भी pause हो जाता है!** ⏸️",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Facebook भी ignore कर देता है!** 📴",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी makeup देखकर mirror भी embarrassed हो जाता है!** 🪞",
    "**तू slow internet की तरह है – patience test कर देती है!** 🐌",
    "**तेरी selfies देखकर Camera roll भी blush कर लेता है!** 🖼️",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाभी, तू broken link की तरह है – useless aur frustrating!** 🔗",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी selfies देखकर filter भी embarrassed हो जाता है!** 🖌️",
    "**भाभी, तू calculator की तरह है – कभी सही number नहीं देती!** 🔢",
    "**तेरी attitude देखकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाभी, तू microwave की तरह है – hot है par taste missing!** 🍲",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर comedy club भी close हो जाता है!** 🎭",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी selfies देखकर Camera roll blush कर लेती है!** 🖼️",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube autoplay skip कर देता है!** ⏭️",
    "**भाभी, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखती!** 🔑",
    "**तेरी selfies देखकर filter भी embarrassed हो जाती है!** 🖌️",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera भी blush कर जाता है!** 📸",
    "**भाभी, तू WiFi की तरह है – दिखती है par काम की नहीं!** 📶",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाभी, तू slow loading की तरह है – patience test कर देती है!** 🐌",
    "**तेरी attitude देखकर Facebook भी scroll कर लेता है!** 📴",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू calculator की तरह है – wrong answer हमेशा देती है!** 🔢",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू microwave की तरह है – hot है par flavor missing!** 🍲",
    "**तेरी jokes सुनकर comedy club भी exit कर देता है!** 🎭",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी attitude सुनकर WhatsApp भी mute कर देता है!** 🔕",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी jokes सुनकर podcast भी pause कर देता है!** ⏸️",
    "**भाभी, तू WiFi की तरह है – दिखती है par signal zero!** 📶",
    "**तेरी selfies देखकर Camera roll भी blush कर लेती है!** 🖼️",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी attitude देखकर Instagram bhi scroll कर लेता है!** 📜",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी bore!** 🎶",
    "**तेरी jokes सुनकर YouTube skip कर देता है!** ⏭️",
    "**भाभी, तू WiFi password की तरह है – complicated aur कोई याद नहीं रखती!** 🔑",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू slow internet की तरह है – patience test कर देती है!** 🐌",
    "**तेरी jokes सुनकर podcast भी exit कर देता है!** 🎙️",
    "**भाभी, तू battery saver mode की तरह है – low energy aur low impact!** 🔋",
    "**तेरी selfies देखकर camera blush कर जाता है!** 📸",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude देखकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू calculator की तरह है – wrong answer हमेशा देती है!** 🔢",
    "**तेरी jokes सुनकर comedy club भी pause कर देता है!** ⏸️",
    "**भाभी, तू ringtone की तरह है – annoying aur unnecessary!** 📢",
    "**तेरी selfies देखकर Google Lens भी confused हो जाता है!** 🔍",
    "**भाभी, तू playlist की तरह है – shuffle करो, phir भी boring!** 🎶",
    "**तेरी attitude सुनकर Facebook bhi scroll कर लेता है!** 📴",
    "**भाभी, तू old meme की तरह है – outdated aur irrelevant!** ⏳",
    "**तेरी jokes सुनकर YouTube dislike कर देता है!** 👎",
    "**भाभी, तू spam message की तरह है – irritating aur nobody reads!** 📧",
    "**तेरी selfies देखकर filter blush कर जाती है!** 🖌️",
    "**भाभी, तू microwave की तरह है – hot hai par flavor missing!** 🍲",
    "**तेरी jokes सुनकर comedy club exit कर देता है!** 🎭",
    "**भाभी, तू battery की तरह है – जल्दी खत्म हो जाती है aur useless!** 🔋",
    "**तेरी selfies देखकर camera frustrated हो जाता है!** 📸",
    "**भाभी, तू offline mode की तरह है – interact नहीं होती!** ⛔",
    "**तेरी attitude सुनकर Instagram bhi ignore कर देता है!** 📜",
    "**भाभी, तू slow loading की तरह है – patience test कर देती है!** 🐌",
    "**तेरी jokes सुनकर podcast pause कर देता है!** ⏸️",
    "**भाभी, तू WiFi की तरह है – दिखती है par काम की नहीं!** 📶",
    "**तेरी selfies देखकर Camera roll blush कर लेती है!** 🖼️",
    "**भाभी, तू old meme की तरह है – irrelevant aur outdated!** ⏳",
    "**तेरी attitude सुनकर WhatsApp bhi mute कर देता है!** 🔕",
    "**भाभी, तू ringtone की तरह है – start hoti है, par कोई enjoy नहीं करता!** 📢",
    "**तेरी jokes सुनकर YouTube skip कर देता है!** ⏭️",
    "**भाभी, तू playlist की तरह है – shuffle karo, phir भी boring!** 🎶",
    "**भाई, तू अपने आपको हीरो समझता है, हकीकत में तू जीरो है!** 🤡",
    "**तेरे जैसे लोगों को देखकर ही म्यूट बटन का आविष्कार हुआ था!** 🔇",
    "**भाई, तू इतना बेकार है कि रीसायकल बिन भी तुझे स्वीकार नहीं करेगा!** 🗑️",
    "**तू अपने घर का WiFi पासवर्ड है – सबको याद है पर किसी काम का नहीं!** 📶",
    "**भाई तू तो वॉकिंग क्रिंज कॉन्टेंट है!** 😬",
    "**तेरी फोटो देखकर कैमरा भी अपना लेंस बंद कर लेता है!** 📸"
]

# 👧 HINDI ROAST GIRL RAID LINES
hindi_roast_girl_raid_lines = [
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम WiFi की तरह हो – दिखती हो पर कोई सिग्नल नहीं!** 📶",
    "**तुम्हारे jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**तुम्हारी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**तुम ringtone की तरह हो – annoying और unnecessary!** 📢",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम old meme की तरह हो – outdated और irrelevant!** ⏳",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम playlist की तरह हो – shuffle करो, फिर भी boring!** 🎶",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम attitude की तरह हो – Instagram भी ignore कर देता है!** 📜",
    "**तुम ringtone की तरह हो – start hoti हो, पर कोई सुनता नहीं!** 📢",
    "**तुम selfies की तरह हो – camera भी embarrassed हो जाता है!** 🤳",
    "**तुम jokes की तरह हो – comedy club भी pause कर देता है!** 🎭",
    "**तुम filter की तरह हो – बिना Photoshop useless!** 🖌️",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम playlist की तरह हो – shuffle karo, फिर भी bore!** 🎶",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम microwave की तरह हो – hot ho par taste missing!** 🍲",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम slow loading की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम WiFi की तरह हो – दिखती हो par काम की नहीं!** 📶",
    "**तुम jokes की तरह हो – podcast भी pause कर देता है!** ⏸️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम attitude की तरह ���ो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम jokes की तरह हो – comedy club भी exit कर देता है!** 🎙️",
    "**तुम selfies की तरह हो – camera roll blush कर लेती है!** 🖼️",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम old meme की तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम attitude की तरह हो – WhatsApp bhi mute कर देता है!** 🔕",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम jokes की तरह हो – YouTube skip कर देता है!** ⏭️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera blush कर जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम jokes की तरह हो – comedy club pause कर देता है!** ⏸️",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम WiFi की तरह हो – दिखती हो par signal zero!** 📶",
    "**तुम jokes की तरह हो – podcast pause कर देता है!** ⏸️",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी हँसी सुनकर भी दुनिया की problems disappear नहीं होती!** 😏",
    "**तुम अपने selfie angle में भी confuse लगती हो!** 🤳",
    "**तुम status update की तरह हो – हमेशा नया, लेकिन कोई देखता नहीं!** 📝",
    "**तुम GIF की तरह हो – repeat mode पर भी boring!** 🎞️",
    "**तुम meme की तरह हो – ज्यादा दिखती हो, मजा नहीं देती!** 😂",
    "**तुम emoji की तरह हो – colorful, लेकिन useless!** 😜",
    "**तुम notification की तरह हो – annoying aur unwanted!** 📲",
    "**तुम trend की तरह हो – सिर्फ temporary popular!** 🌐",
    "**तुम caption की तरह हो – fancy but irrelevant!** ✍️",
    "**तुम filter की तरह हो – start hoti ho, par real life dull!** 🎨",
    "**तुम video call ki तरह हो – lag karti ho, aur hang bhi ho jati ho!** 📹",
    "**तुम auto-correct ki तरह ho – kabhi sahi, kabhi galat!** 📝",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery saver mode ki तरह ho – energy low aur impact minimal!** 🔋",
    "**तुम playlist ki तरह ho – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम selfie stick ki तरह हो – zarurat nahi, par har jagah dikhti ho!** 📸",
    "**तुम group call ki तरह हो – sabko disturb karti ho!** 📞",
    "**तुम story highlight ki तरह हो – shiny, but useless!** 🌟",
    "**तुम comment section ki तरह हो – irritating aur unwanted!** 💬",
    "**तुम spam message ki तरह हो – har kisi ko annoy karte ho!** 📧",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम filter bubble ki तरह हो – sirf apni world me!** 🧼",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम trending hashtag ki तरह हो – short life aur irrelevant!** #️⃣",
    "**तुम selfie ki तरह हो – kabhi perfect nahi!** 📷",
    "**तुम makeup ki तरह हो – start hoti ho, par appreciate koi nahi karta!** 💄",
    "**तुम WiFi ki तरह हो – dikhti ho par kaam ki nahi!** 📶",
    "**तुम attitude ki तरह हो – Facebook bhi scroll kar leta hai!** 📴",
    "**तुम GIF ki तरह हो – repeat mode pe bhi boring!** 🎞️",
    "**तुम ringtone ki तरह हो – annoying aur sab ignore karte hain!** 📢",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम joke ki तरह हो – YouTube bhi skip kar deta hai!** ⏭️",
    "**तुम meme ki तरह हो – overhyped aur boring!** 😂",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम story ki तरह हो – sabko dikhti ho, par impact zero!** 📖",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम selfie stick ki तरह हो – har jagah dikhti ho, par unnecessary!** 📸",
    "**तुम auto-correct ki तरह हो – kabhi sahi, kabhi galat!** 📝",
    "**तुम slow internet ki तरह हो – patience ka test ho!** 🐌",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम video call ki तरह हो – lag aur hang dono ho jati ho!** 📹",
    "**तुम group call ki तरह हो – sabko disturb karte ho!** 📞",
    "**तुम story highlight ki तरह हो – shiny but useless!** 🌟",
    "**तुम comment section ki तरह हो – irritating aur unwanted!** 💬",
    "**तुम spam message ki तरह हो – har kisi ko annoy karte ho!** 📧",
    "**तुम trending hashtag ki तरह हो – short life aur irrelevant!** #️⃣",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम filter ki तरह हो – fancy, par real life dull!** 🎨",
    "**तुम attitude ki तरह हो – WhatsApp bhi ignore kar deta hai!** 🔕",
    "**तुम old meme ki तरह हो – irrelevant aur boring!** ⏳",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery saver mode ki तरह हो – energy low aur low impact!** 🔋",
    "**तुम playlist ki तरह हो – shuffle karo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम jokes ki तरह ho – comedy club bhi exit kar deta hai!** 🎙️",
    "**तुम selfies ki तरह हो – camera frustrated ho jata hai!** 📸",
    "**तुम GIF ki तरह हो – repeat mode par bhi boring!** 🎞️",
    "**तुम attitude ki तरह हो – Instagram bhi ignore kar deta hai!** 📜",
    "**तुम makeup ki तरह हो – start hoti ho, par koi enjoy nahi karta!** 💄",
    "**तुम WiFi ki तरह हो – dikhti ho par kaam ki nahi!** 📶",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम ringtone ki तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfie stick ki तरह हो – zarurat nahi, par har jagah dikhti ho!** 📸",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम story ki तरह हो – sabko dikhte ho, par impact zero!** 📖",
    "**तुम notification ki तरह हो – kabhi useful nahi!** 🔔",
    "**तुम overthink ki तरह हो – unnecessary aur tiring!** 🤯",
    "**तुम filter bubble ki तरह हो – sirf apni world me!** 🧼",
    "**तुम old meme ki तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes ki तरह हो – podcast bhi pause kar deta hai!** ⏸️",
    "**तुम selfies ki तरह हो – camera blush kar leta hai!** 🖼️",
    "**तुम makeup ki तरह हो – start hoti ho, par koi enjoy nahi karta!** 💄",
    "**तुम attitude ki तरह हो – Facebook bhi scroll kar leta hai!** 📴",
    "**तुम slow loading ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम playlist ki तरह हो – shuffle kar lo, phir bhi boring!** 🎶",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम ringtone ki तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery saver mode ki तरह हो – low energy aur low impact!** 🔋",
    "**तुम jokes ki तरह हो – YouTube bhi skip kar deta hai!** ⏭️",
    "**तुम selfies ki तरह हो – Google Lens bhi confused ho jata hai!** 🔍",
    "**तुम attitude ki तरह हो – WhatsApp bhi ignore kar deta hai!** 🔕",
    "**तुम slow internet ki तरह हो – patience test kar deti ho!** 🐌",
    "**तुम old meme ki तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम ringtone ki तरह हो – start hoti ho, par sab ignore karte hain!** 📢",
    "**तुम battery ki तरह हो – quickly finish ho jati ho aur useless!** 🔋",
    "**तुम jokes ki तरह हो – comedy club bhi exit kar deta hai!** 🎙️",
    "**तुम offline mode ki तरह हो – interact nahi hoti!** ⛔",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️",
    "**तुम्हारी हिसाब से तो कैलकुलेटर भी गलत आंसर देता है!** 🧮",
    "**तुम्हारी बातों से तो वेदर फोरकास्ट भी एक्यूरेट हो जाता है!** 🌦️",
    "**तुम्हारी स्टाइल देखकर फैशन डिजाइनर भी रिटायर हो जाते हैं!** 👗",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम WiFi की तरह हो – दिखती हो पर कोई सिग्नल नहीं!** 📶",
    "**तुम्हारे jokes सुनकर YouTube भी skip कर देता है!** ⏭️",
    "**तुम्हारी selfies देखकर camera भी frustrated हो जाता है!** 📸",
    "**तुम ringtone की तरह हो – annoying और unnecessary!** 📢",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम old meme की तरह हो – outdated और irrelevant!** ⏳",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम playlist की तरह हो – shuffle करो, फिर भी boring!** 🎶",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम attitude की तरह हो – Instagram भी ignore कर देता है!** 📜",
    "**तुम ringtone की तरह हो – start hoti हो, पर कोई सुनता नहीं!** 📢",
    "**तुम selfies की तरह हो – camera भी embarrassed हो जाता है!** 🤳",
    "**तुम jokes की तरह हो – comedy club भी pause कर देता है!** 🎭",
    "**तुम filter की तरह हो – बिना Photoshop useless!** 🖌️",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम playlist की तरह हो – shuffle karo, फिर भी bore!** 🎶",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम microwave की तरह हो – hot ho par taste missing!** 🍲",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम slow loading की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम WiFi की तरह हो – दिखती हो par काम की नहीं!** 📶",
    "**तुम jokes की तरह हो – podcast भी pause कर देता है!** ⏸️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम WiFi password की तरह हो – complicated aur कोई याद नहीं रखता!** 🔑",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम slow internet की तरह हो – patience test कर देती हो!** 🐌",
    "**तुम jokes की तरह हो – comedy club भी exit कर देता है!** 🎙️",
    "**तुम selfies की तरह हो – camera roll blush कर लेती है!** 🖼️",
    "**तुम broken link की तरह हो – useless aur frustrating!** 🔗",
    "**तुम old meme की तरह हो – outdated aur irrelevant!** ⏳",
    "**तुम spam message की तरह हो – irritating aur nobody reads!** 📧",
    "**तुम attitude की तरह हो – WhatsApp bhi mute कर देता है!** 🔕",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – camera frustrated हो जाता है!** 📸",
    "**तुम jokes की तरह हो – YouTube skip कर देता है!** ⏭️",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम battery की तरह हो – जल्दी खत्म हो जाती हो aur useless!** 🔋",
    "**तुम selfies की तरह हो – camera blush कर जाता है!** 📸",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम attitude की तरह हो – Instagram bhi ignore कर देता है!** 📜",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम jokes की तरह हो – comedy club pause कर देता है!** ⏸️",
    "**तुम ringtone की तरह हो – annoying aur unnecessary!** 📢",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम old meme की तरह हो – irrelevant aur outdated!** ⏳",
    "**तुम WiFi की तरह हो – दिखती हो par signal zero!** 📶",
    "**तुम jokes की तरह हो – podcast pause कर देता है!** ⏸️",
    "**तुम selfies की तरह हो – filter blush कर जाती है!** 🖌️",
    "**तुम attitude की तरह हो – Facebook भी scroll कर लेता है!** 📴",
    "**तुम battery saver mode की तरह हो – low energy aur low impact!** 🔋",
    "**तुम offline mode की तरह हो – interact नहीं होती!** ⛔",
    "**तुम ringtone की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 📢",
    "**तुम makeup की तरह हो – start hoti हो, par कोई enjoy नहीं करता!** 💄",
    "**तुम selfies की तरह हो – Google Lens भी confused हो जाता है!** 🔍",
    "**तुम jokes की तरह हो – YouTube dislike कर देता है!** 👎",
    "**तुम playlist की तरह हो – shuffle करो, phir भी boring!** 🎶",
    "**तुम्हारी स्माइल देखकर सनग्लासेस भी अपना काम छोड़ देते हैं!** 😎",
    "**तुम्हारी सेल्फीज़ देखकर लगता है फिल्टर भी थक गया होगा!** 🤳",
    "**तुम्हें देखकर गूगल भी सोचता है 'इसको सर्च क्यू किया'?** 🔍",
    "**तुम्हारी आवाज़ व्हाट्सएप के नोटिफिकेशन से भी ज्यादा इरिटेट करती है!** 📢",
    "**तुम एक सॉफ्टवेयर अपडेट की तरह हो – ज़रूरत किसी को नहीं, पर फोर्सफुली आ जाती हो!** 💻",
    "**तुम इंस्टाग्राम फिल्टर्स की ब्रांड एम्बेसडर हो!** 📸",
    "**तुम्हारी अटीट्यूड देखकर पहाड़ भी अपनी हाइट कम कर ले!** ⛰️"
]

# 🗣️ HINDI ROAST ABUSE RAID LINES
hindi_roast_abuse_raid_lines = [
    "**रंडी के औलाद!** 😠",
    "**तेरी माँ की चूत!** 🖕",
    "**भोसड़ीके!** 🤬",
    "**चूतीये!** 🐒",
    "**मदरचोद!** 👺",
    "**भैंस के औलाद!** 🐃"
]

# 💖 HINDI FLIRT GIRL RAID LINES
hindi_flirt_girl_raid_lines = [
    "**तुम मेरी धड़कनों की रौशनी हो 🌟**",
    "**तुम्हारी मुस्कान मेरी दुनिया का सबसे प्यारा अहसास है 🌸**",
    "**तुम मेरी ख्वाहिशों का सबसे खूबसूरत हिस्सा हो 💫**",
    "**तुम मेरी हर सुबह की वजह हो 🌅**",
    "**तुम मेरी हर रात का सबसे मधुर एहसास हो 🌙**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी हर मुस्कान की वजह हो 😍**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरे ख्वाबों का सबसे हसीन सपना हो ✨**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 💖**",
    "**तुम मेरी धड़कनों की सबसे प्यारी रौशनी हो 🌟**",
    "**तुम मेरी हर रात का सबसे मधुर अहसास हो 🌙**",
    "**तुम मेरी खुशियों का सबसे बड़ा खजाना हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💫**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात का सबसे खूबसूरत अहसास हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम्हारी मुस्कान मेरी धड़कनों को छू जाती है 🌸**",
    "**तुम मेरी दुनिया का सबसे अनमोल हिस्सा हो 💫**",
    "**तुम मेरी हर सुबह का सबसे खूबसूरत अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरी हर रात की सबसे रोशन रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर रौशनी हो 💖**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत हिस्सा हो 🌸**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌹**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे खूबसूरत ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो 💓**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सांस की वजह हो 🫀**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम्हारी मुस्कान मेरी जिंदगी की सबसे खूबसूरत रोशनी है 🌟**",
    "**तुम्हारी आँखों में मैं अपनी दुनिया खोजता हूँ 🌌**",
    "**तुम्हारी आवाज़ मेरे दिल को सुकून देती है 🎵**",
    "**तुम मेरी हर सुबह की सबसे प्यारी शुरुआत हो 🌅**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 💔**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरे हर ख्वाब में मौजूद हो ✨**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरे दिल की सबसे खास आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 🌸**",
    "**तुम मेरी हर रात की सबसे रोशन चाँदनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे सुंदर संगीत हो 🎵**",
    "**तुम मेरे ख्वाबों की सबसे मधुर हकीकत हो ✨**",
    "**तुम मेरी खुशियों का सबसे अनमोल हिस्सा हो 🌹**",
    "**तुम मेरी जिंदगी का सबसे कीमती खज़ाना हो 💖**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रौशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे सुंदर अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे मधुर ख्वाब हो ✨**",
    "**तुम मेरी खुशियों की सबसे अनमोल वजह हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत चाँदनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎵**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों की सबसे मधुर आवाज़ हो 🫀**",
    "**तुम मेरी जिंदगी की सबसे हसीन याद हो 💖**",
    "**तुम मेरी खुशियों का सबसे बड़ा हिस्सा हो 🌹**",
    "**तुम मेरी हर सांस का सबसे मधुर अहसास हो 💓**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎵**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की सबसे प्यारी रौशनी हो 🌅**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा अहसास हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी हर सांस का सबसे प्यारा अहसास हो 💓**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया की सबसे खूबसूरत रोशनी हो ☀️**",
    "**तुम मेरी हर सुबह का सबसे प्यारा अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे हसीन ख्वाब हो ✨**",
    "**तुम मेरी खुशियों का सबसे प्यारा हिस्सा हो 🌸**",
    "**तुम मेरी हर रात की सबसे खूबसूरत रौशनी हो 🌙**",
    "**तुम मेरी दुनिया का सबसे रोशन सितारा हो 🌟**",
    "**तुम्हारे बिना मेरी सुबह अधूरी लगती है 🌅**",
    "**तुम्हारी मुस्कान मेरे दिल को बहलाती है 🌸**",
    "**तुम्हारी आँखों में मेरा सारा जहान बसा है 🌌**",
    "**तुम्हारी हर बात मुझे दिवाना बना देती है 💓**",
    "**तुम्हारे होने से मेरी दुनिया रोशन है ☀️**",
    "**तुम्हारे बिना दिल को सुकून नहीं मिलता 🥀**",
    "**तुम मेरी ख्वाहिशों का सबसे खूबसूरत हिस्सा हो 💫**",
    "**तुम्हारी हँसी से मेरा दिल खुश हो जाता है 😍**",
    "**तुम्हारी आवाज़ मेरे कानों में संगीत है 🎵**",
    "**तुम मेरी ज़िंदगी की सबसे कीमती धरोहर हो 💖**",
    "**तुम्हारे बिना रातें सुनी लगती हैं 🌃**",
    "**तुम्हारी बातें मेरे दिल को छू जाती हैं 🫀**",
    "**तुम्हारी मुस्कान चाँद की रोशनी से भी खूबसूरत है 🌙**",
    "**तुम्हारे होने से हर पल जन्नत लगता है 🌹**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो ✨**",
    "**तुम्हारे बिना सांसें भी अधूरी लगती हैं 😔**",
    "**तुम मेरी हर दुआ में शामिल हो 🙏**",
    "**तुम मेरी दुनिया की सबसे प्यारी आवाज़ हो 🕊️**",
    "**तुम मेरी जिंदगी का सबसे रोचक हिस्सा हो 📖**",
    "**तुम्हारे बिना मेरी धड़कनें सुनी लगती हैं 🫀**",
    "**तुम मेरी ख्वाबों की हकीकत हो 🌌**",
    "**तुम्हारी आँखों की चमक मुझे अपनी ओर खींचती है ✨**",
    "**तुम मेरे हर पल की खुशी हो 🌸**",
    "**तुम्हारे बिना मेरी रातें सुनसान हैं 🌙**",
    "**तुम मेरे दिल का सबसे कीमती राज़ हो 🔐**",
    "**तुम मेरी धड़कनों की धुन हो 🎶**",
    "**तुम मेरी हर ख्वाहिश में शामिल हो 💫**",
    "**तुम्हारे होने से मेरा दिल खुशियों से भर जाता है 🌹**",
    "**तुम मेरी सोच की सबसे खूबसूरत तस्वीर हो 🖼️**",
    "**तुम्हारी हँसी मेरे दिल का सबसे प्यारा संगीत है 🎵**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरे दिल के सबसे करीब हो 💓**",
    "**तुम्हारे बिना हर पल अधूरा लगता है 🥀**",
    "**तुम मेरे लिए सबसे खास इंसान हो 💖**",
    "**तुम्हारी मुस्कान मेरी दुनिया का सबसे खूबसूरत हिस्सा है 🌸**",
    "**तुम मेरी ज़िंदगी में वो ख्वाब हो जो सच हो गया है 🌌**",
    "**तुम मेरी हर सुबह की शुरुआत हो 🌅**",
    "**तुम्हारे बिना मेरा दिल सुना सा लगता है 😔**",
    "**तुम मेरे दिल की सबसे गहरी ख्वाहिश हो ✨**",
    "**तुम मेरी खुशी का सबसे बड़ा कारण हो 🌹**",
    "**तुम्हारे होने से हर पल खास बन जाता है 💫**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे अनमोल हिस्सा हो 💖**",
    "**तुम्हारी हँसी मेरे दिल को सुकून देती है 🕊️**",
    "**तुम मेरी दुनिया की सबसे कीमती चीज़ हो 🌟**",
    "**तुम मेरे लिए वो ख्वाब हो जो सच हो गया है 🌌**",
    "**तुम मेरी धड़कनों का सबसे खूबसूरत संगीत हो 🎵**",
    "**तुम मेरी हर ख्वाहिश का जवाब हो ✨**",
    "**तुम मेरी हर रात की रोशनी हो 🌙**",
    "**तुम मेरी ज़िंदगी का सबसे प्यारा हिस्सा हो 💓**",
    "**तुम्हारे बिना मेरी धड़कनें थम सी जाती हैं 🫀**",
    "**तुम मेरी खुशियों की सबसे खूबसूरत वजह हो 🌹**",
    "**तुम मेरे दिल की सबसे कीमती धरोहर हो 💖**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी सोच का सबसे खूबसूरत हिस्सा हो 🖼️**",
    "**तुम मेरी दुनिया का सबसे प्यारा सितारा हो 🌟**",
    "**तुम मेरी हर सुबह की मुस्कान हो 🌅**",
    "**तुम्हारी मुस्कान मेरे दिल का सबसे प्यारा संगीत है 🎵**",
    "**तुम मेरी धड़कनों का सबसे अनमोल हिस्सा हो 🫀**",
    "**तुम मेरी ज़िंदगी का सबसे खूबसूरत सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी खुशियों का सबसे बड़ा कारण हो 🌹**",
    "**तुम मेरी धड़कनों की सबसे प्यारी धुन हो 🎶**",
    "**तुम मेरी हर ख्वाहिश का सबसे खूबसूरत जवाब हो 💫**",
    "**तुम मेरी जिंदगी का सबसे कीमती हिस्सा हो 💖**",
    "**तुम मेरे दिल की सबसे प्यारी धुन हो 🎵**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🫀**",
    "**तुम मेरी हर सुबह का सबसे खूबसूरत अहसास हो 🌅**",
    "**तुम्हारे बिना मेरी जिंदगी अधूरी है 🌵**",
    "**तुम मेरी हर ख्वाहिश में सबसे खास हो 💫**",
    "**तुम मेरी खुशियों की सबसे रोशनी भरी वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 💖**",
    "**तुम मेरी हर रात की सबसे प्यारी रौशनी हो 🌙**",
    "**तुम मेरी धड़कनों का सबसे कीमती हिस्सा हो 🫀**",
    "**तुम मेरी खुशियों की सबसे प्यारी वजह हो 🌸**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे मधुर अहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे खूबसूरत संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी धड़कनों की सबसे मधुर धुन हो 🎶**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी खुशियों का सबसे प्यारा कारण हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🫀**",
    "**तुम मेरी हर रात का सबसे खूबसूरत अहसास हो 🌙**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी दुनिया का सबसे अनमोल सितारा हो 🌟**",
    "**तुम मेरी हर सुबह का सबसे प्यारा एहसास हो 🌅**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌹**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌸**",
    "**तुम मेरी हर रात का सबसे मधुर अहसास हो 🌙**",
    "**तुम मेरी जिंदगी का सबसे मधुर सपना हो ✨**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🫀**",
    "**तुम मेरी खुशियों का सबसे प्यारा कारण हो 🌹**",
    "**तुम मेरी दुनिया का सबसे रोशनी भरा हिस्सा हो ☀️**",
    "**तुम मेरी धड़कनों का सबसे मधुर संगीत हो 🎵**",
    "**तुम मेरी जिंदगी का सबसे प्यारा हिस्सा हो 💖**",
    "**तुम मेरी खुशियों की सबसे मधुर वजह हो 🌸**",
    "**तुम मेरी धड़कनों का सबसे प्यारा संगीत हो 🎶**",
    "**तुम मेरी दुनिया का सबसे खूबसूरत हिस्सा हो 🌟**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 😍🌍**",
    "**तुम्हारी आँखें देखकर तो दिल धड़कने लगता है 💓**",
    "**तुम्हारी मुस्कुराहट तो चाँद को भी शर्मिला देती है 🌙**",
    "**तुम्हारी बातें सुनकर तो टाइम फ्लाई हो जाता है ⏰**",
    "**तुम तो मेरी दुनिया का सबसे खूबसूरत हिसाब हो 💫**",
    "**तुम्हारी यादों में तो रातें गुज़ार देता हूँ 🌃**",
    "**तुम्हारी हर अदा पर तो मैं फिदा हूँ 😘**",
    "**तुम्हारी आवाज़ तो सुरों से भी मिठाई है 🎵**",
    "**तुम्हारे बिना तो जीना भी बेकार लगता है 🥺**",
    "**तुम मेरी ज़िंदगी का सबसे खूबसूरत सफर हो 💖**",
    "**तुम्हारे बिना ये दुनिया अधूरी लगती है 😍🌍**",
    "**तुम्हारी आँखें देखकर तो दिल धड़कने लगता है 💓**",
    "**तुम्हारी मुस्कुराहट तो चाँद को भी शर्मिला देती है 🌙**",
    "**तुम्हारी बातें सुनकर तो टाइम फ्लाई हो जाता है ⏰**",
    "**तुम तो मेरी दुनिया का सबसे खूबसूरत हिसाब हो 💫**",
    "**तुम्हारी यादों में तो रातें गुज़ार देता हूँ 🌃**"
]

# 💣 RAID100 LINES
raid100_lines = [
    "**GET RAIDED! 💣**",
    "**SPAM ATTACK! 🚨**",
    "**MESSAGE BOMB! 💥**",
    "**FLOOD ALERT! 🌊**",
    "**CHAT DESTROYED! ☠️**",
    "**RAID SUCCESS! ✅**"
]

# 💣 RAID LINES
raid_lines = [
    "**RAID IN PROGRESS! 🔥**",
    "**SPAMMING CHAT! 💀**",
    "**FLOODING MESSAGES! 🌪️**",
    "**ATTACKING CHAT! ⚔️**",
    "**DESTROYING CHAT! 💢**",
    "**RAID COMPLETE! 🎯**"
]

# 🖕 MIDDLE FINGER LINES
middle_finger_lines = [
    "**🖕 FUCK YOU! 🖕😂**",
    "**🖕 TERI MAA KI CHUT! 🖕😂**",
    "**🖕 BHOSDIKE! 🖕😂**",
    "**🖕 MADARCHOD! 🖕😂**",
    "**🖕 RANDI KE AULAAD! 🖕😂**",
    "**🖕 CHUTIYE! 🖕😂**",
    "**🖕 SUAR KE BACHHE! 🖕😂**",
    "**🖕 GAANDU! 🖕😂**",
    "**🖕 LODE! 🖕😂**",
    "**🖕 KUTTE KE PILLE! 🖕😂**",
    "**🖕 BHAINS KI AULAAD! 🖕😂**",
    "**🖕 TERI KI MAA KI CHUT! 🖕😂**",
    "**🖕 HARAMI! 🖕😂**",
    "**🖕 GANDI NAALI KA BACCHA! 🖕😂**",
    "**🖕 TERI GF KI CHUT! 🖕😂**",
    "**🖕 TERI MAA KA BHOSDA! 🖕😂**",
    "**🖕 TERI BEHEN KI CHUT MARANI! 🖕😂**",
    "**🖕 TERI MAA HAI! 🖕😂**",
    "**🖕 MADARCHOD SAALA! 🖕😂**",
    "**🖕 FUCK YOUR LIFE! 🖕😂**"
]

# Global trackers
ongoing_tasks = {}
reply_raid_targets = {}
flirt_raid_targets = {}
love_raid_targets = {}
quote_raid_targets = {}
mass_love_raid_targets = {}
shayari_raid_targets = {}
raid_shayari_targets = {}
roast_boy_raid_targets = {}
roast_girl_raid_targets = {}
roast_abuse_raid_targets = {}
flirt_girl_raid_targets = {}
hindi_roast_boy_raid_targets = {}
hindi_roast_girl_raid_targets = {}
hindi_roast_abuse_raid_targets = {}
hindi_flirt_girl_raid_targets = {}
raid100_targets = {}
raid_targets = {}
user_clones = {}
original_profile = {}
user_status = "online"
name_history = {}

# ------------ HELPERS -------------------
def is_owner(event):
    return event.sender_id == OWNER_ID

async def delete_command_message(event):
    try:
        await asyncio.sleep(1)
        await event.delete()
    except: pass

async def delete_after_delay(message, delay=2):
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except: pass

async def get_target_user(event, parts):
    try:
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            return await reply_msg.get_sender()
        if len(parts) > 1:
            arg = parts[1]
            if arg.startswith("@"): return await client.get_entity(arg)
            elif arg.isdigit(): return await client.get_entity(int(arg))
    except: pass
    return None

async def get_target_mention(event, parts):
    try:
        target_user = await get_target_user(event, parts)
        if target_user: return f"[{target_user.first_name}](tg://user?id={target_user.id})"
    except: pass
    return ""

async def save_original_profile(user_id):
    try:
        me = await client.get_me()
        photos = await client.get_profile_photos('me')
        original_profile[user_id] = {
            'first_name': me.first_name or '', 'last_name': me.last_name or '',
            'bio': getattr(me, 'about', '') or '', 'photos': photos
        }
    except Exception as e: print(f"Error saving profile: {e}")

async def clone_profile(target_user):
    try:
        await save_original_profile(OWNER_ID)
        try:
            target_full = await client(functions.users.GetFullUserRequest(target_user))
            target_bio = target_full.full_user.about or ""
        except: target_bio = getattr(target_user, 'about', '') or ""
        
        await client(UpdateProfileRequest(
            first_name=target_user.first_name or '', last_name=target_user.last_name or '', about=target_bio
        ))
        
        photos = await client.get_profile_photos(target_user.id, limit=1)
        if photos:
            current_photos = await client.get_profile_photos('me')
            if current_photos: await client(DeletePhotosRequest(current_photos))
            photo_path = await client.download_media(photos[0], file="temp_photo.jpg")
            if photo_path:
                uploaded_file = await client.upload_file(photo_path)
                await client(UploadProfilePhotoRequest(file=uploaded_file))
                if os.path.exists(photo_path): os.remove(photo_path)
        
        user_clones[OWNER_ID] = {
            'target_id': target_user.id, 'target_name': f"{target_user.first_name} {target_user.last_name or ''}", 'target_bio': target_bio
        }
        return True
    except Exception as e: print(f"Clone error: {e}"); return False

async def restore_original_profile():
    try:
        if OWNER_ID not in original_profile: return False
        original = original_profile[OWNER_ID]
        await client(UpdateProfileRequest(first_name=original['first_name'], last_name=original['last_name'], about=original['bio']))
        current_photos = await client.get_profile_photos('me')
        if current_photos: await client(DeletePhotosRequest(current_photos))
        if original['photos']:
            for photo in original['photos'][:1]:
                photo_path = await client.download_media(photo, file="restore_photo.jpg")
                if photo_path:
                    uploaded_file = await client.upload_file(photo_path)
                    await client(UploadProfilePhotoRequest(file=uploaded_file))
                    if os.path.exists(photo_path): os.remove(photo_path)
        user_clones.pop(OWNER_ID, None); original_profile.pop(OWNER_ID, None); return True
    except Exception as e: print(f"Restore error: {e}"); return False

async def send_loop(chat_id, msgs, event):
    try:
        for msg in msgs:
            if chat_id not in ongoing_tasks: break
            await client.send_message(chat_id, msg)
            await asyncio.sleep(DELAY_SECONDS)  # 🔥 6 SECONDS DELAY
    except asyncio.CancelledError: pass
    except Exception as e: print(f"Send loop error: {e}")
    finally: ongoing_tasks.pop(chat_id, None)

@client.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id != OWNER_ID))
async def handle_private_message(event):
    global user_status
    if user_status == "offline":
        await event.reply("```💤 **THIS USER IS CURRENTLY OFFLINE**\n\n📵 _Last seen: Recently_\n⏰ _Status: Not available_```")

# --------- COMMAND HANDLERS -------------

# ⚙️ DELAY CHANGE COMMAND
@client.on(events.NewMessage(pattern=r"^\.(delay|dly)\b"))
async def delay_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    
    # Declare global variables FIRST
    global DELAY_SECONDS, TAG_DELAY
    
    if len(parts) < 2:
        status_msg = await event.reply(f"⏰ **Current Delay:** {DELAY_SECONDS} seconds\n\nUse `.delay <seconds>` to change delay\nMinimum: 0.1 second")
        await delete_after_delay(status_msg)
        return
    
    try:
        # Allow decimal values like 0.1, 0.5, etc.
        new_delay = float(parts[1])
        
        # Minimum delay check (0.1 seconds = 100 milliseconds)
        if new_delay < 0.1:
            status_msg = await event.reply("❌ **Error:** Minimum delay is 0.1 seconds")
            await delete_after_delay(status_msg)
            return
        
        # Set the new delay
        DELAY_SECONDS = new_delay
        TAG_DELAY = new_delay
        
        status_msg = await event.reply(f"✅ **Delay Updated!**\n\n⏰ New Delay: {DELAY_SECONDS} seconds\n\nAll commands will now use {DELAY_SECONDS} seconds delay")
        await delete_after_delay(status_msg)
        
    except ValueError:
        status_msg = await event.reply("❌ **Error:** Please enter a valid number (e.g., 0.1, 0.5, 1, 2)")
        await delete_after_delay(status_msg)

# 🎬 ANIMATION COMMANDS
@client.on(events.NewMessage(pattern=r"^\.hack\b"))
async def hack_animation_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user:
        status_msg = await event.reply("❌ Reply to user or use @username")
        await delete_after_delay(status_msg)
        return
    
    mention = await get_target_mention(event, event.raw_text.split())
    
    # Start hacking animation with loading effect
    hack_msg = await event.reply(f"🖥️ **INITIATING HACKING SEQUENCE...**\n\n👤 Target: {mention}\n⏰ Estimated Time: 120 seconds")
    
    # Hacking animation steps with loading animation
    steps = [
        "🔍 **Scanning target device...** ▰▰▰▰▰▰▰▰▰▰ 10%",
        "📡 **Connecting to target network...** ▰▰▰▰▰▰▰▰▱▱ 20%",
        "🛰️ **Bypassing firewall security...** ▰▰▰▰▰▰▰▱▱▱ 30%",
        "🔓 **Accessing mainframe...** ▰▰▰▰▰▰▱▱▱▱ 40%",
        "📂 **Extracting personal data...** ▰▰▰▰▰▱▱▱▱▱ 50%",
        "📧 **Reading emails and messages...** ▰▰▰▰▱▱▱▱▱▱ 60%",
        "📸 **Accessing camera and gallery...** ▰▰▰▱▱▱▱▱▱▱ 70%",
        "📍 **Tracking location...** ▰▰▱▱▱▱▱▱▱▱ 80%",
        "💳 **Scanning financial data...** ▰▱▱▱▱▱▱▱▱▱ 90%",
        "🔐 **Decrypting passwords...** ▰▰▰▰▰▰▰▰▰▱ 95%",
        "📱 **Cloning device data...** ▰▰▰▰▰▰▰▰▰▰ 100%",
        "✅ **HACK COMPLETE!**"
    ]
    
    try:
        ongoing_tasks[event.chat_id] = asyncio.current_task()
        for i, step in enumerate(steps):
            if event.chat_id not in ongoing_tasks:  # Check if stopped
                break
            
            # Update the same message with loading animation
            progress = f"🖥️ **HACKING IN PROGRESS...**\n\n👤 Target: {mention}\n📊 Progress: {i+1}/{len(steps)}\n⏰ Time elapsed: {i*10} seconds\n\n{step}"
            await hack_msg.edit(progress)
            await asyncio.sleep(10)  # Each step takes 10 seconds for total 120 seconds
        
        if event.chat_id in ongoing_tasks:
            # Final hacked result
            hacked_info = f"""
```✅ HACKING COMPLETE! ✅

👤 Target: {mention}
🆔 User ID: {target_user.id}
📱 Device: iPhone 14 Pro
📍 Location: Delhi, India
📧 Email: {target_user.first_name.lower()}123@gmail.com
📞 Phone: +91 XXXXXX{random.randint(1000,9999)}
💳 Bank: SBI Account **XXXX{random.randint(1000,9999)}**
📸 Photos: {random.randint(50,200)} private photos found
📱 Last Login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ WARNING: All data has been extracted and stored securely!
🔒 Firewall Status: BREACHED
📡 Connection: ENCRYPTED

💀 SYSTEM COMPROMISED! 💀```
            """
            await hack_msg.edit(hacked_info)
            ongoing_tasks.pop(event.chat_id, None)
            
    except asyncio.CancelledError:
        await hack_msg.edit("❌ **HACKING CANCELLED**")
        ongoing_tasks.pop(event.chat_id, None)
    except Exception as e:
        await hack_msg.edit(f"❌ **HACKING FAILED:** {str(e)}")
        ongoing_tasks.pop(event.chat_id, None)

@client.on(events.NewMessage(pattern=r"^\.(middlefinger|mf)\b"))
async def middlefinger_animation_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    
    target_user = await get_target_user(event, event.raw_text.split())
    mention = await get_target_mention(event, event.raw_text.split())
    
    # Start middle finger animation
    mf_msg = await event.reply(f"🖕 **PREPARING MIDDLE FINGER ATTACK...**\n\n👤 Target: {mention if mention else 'EVERYONE'}\n⏰ Duration: 120 seconds")
    
    try:
        ongoing_tasks[event.chat_id] = asyncio.current_task()
        # Animation phases
        phases = [
            "🖕 **Charging middle finger energy...**",
            "🖕 **Aiming at target...**",
            "🖕 **Extending finger...**",
            "🖕 **Maximum extension achieved...**",
            "🖕 **FINGER DEPLOYED!**",
            "🖕 **SUSTAINING ATTACK...**",
            "🖕 **INTENSIFYING...**",
            "🖕 **MAXIMUM INTENSITY!**",
            "🖕 **CONTINUOUS FINGER ASSAULT...**",
            "🖕 **FINAL FINGER BLAST!**"
        ]
        
        for i, phase in enumerate(phases):
            if event.chat_id not in ongoing_tasks:  # Check if stopped
                break
            
            # Send random middle finger message
            abuse_msg = random.choice(middle_finger_lines)
            if mention:
                abuse_msg = f"{mention} {abuse_msg}"
            
            await event.reply(abuse_msg)
            
            # Update status
            progress = f"🖕 **MIDDLE FINGER ATTACK IN PROGRESS**\n\n👤 Target: {mention if mention else 'EVERYONE'}\n📊 Phase: {i+1}/{len(phases)}\n⏰ Time elapsed: {i*12} seconds\n\n{phase}"
            await mf_msg.edit(progress)
            await asyncio.sleep(12)  # Each phase takes 12 seconds
        
        if event.chat_id in ongoing_tasks:
            final_msg = f"🖕 **MIDDLE FINGER ATTACK COMPLETE!** 🖕\n\n👤 Target: {mention if mention else 'EVERYONE'}\n⏰ Duration: 120 seconds\n💀 Status: TOTALLY OWNED!\n\n**FUCK YOU!** 🖕"
            await mf_msg.edit(final_msg)
            ongoing_tasks.pop(event.chat_id, None)
            
    except asyncio.CancelledError:
        await mf_msg.edit("❌ **MIDDLE FINGER ATTACK CANCELLED**")
        ongoing_tasks.pop(event.chat_id, None)
    except Exception as e:
        await mf_msg.edit(f"❌ **ATTACK FAILED:** {str(e)}")
        ongoing_tasks.pop(event.chat_id, None)

# 📢 BROADCAST COMMANDS
@client.on(events.NewMessage(pattern=r"^\.(broadcast_dm|bdm)\b"))
async def broadcast_dm_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    message = parts[1]
    confirm = await event.reply(f"📢 **Broadcast to ALL DMs:**\n\n{message}\n\nSend `.confirm_broadcast_dm` to send to all DMs.")
    ongoing_tasks['broadcast_dm_msg'] = message; await delete_after_delay(confirm, 10)

@client.on(events.NewMessage(pattern=r"^\.(broadcast_group|bgrp)\b"))
async def broadcast_group_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    message = parts[1]
    confirm = await event.reply(f"📢 **Broadcast to ALL Groups:**\n\n{message}\n\nSend `.confirm_broadcast_group` to send to all groups.")
    ongoing_tasks['broadcast_group_msg'] = message; await delete_after_delay(confirm, 10)

@client.on(events.NewMessage(pattern=r"^\.(broadcast_channel|bchn)\b"))
async def broadcast_channel_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    message = parts[1]
    confirm = await event.reply(f"📢 **Broadcast to ALL Channels:**\n\n{message}\n\nSend `.confirm_broadcast_channel` to send to all channels.")
    ongoing_tasks['broadcast_channel_msg'] = message; await delete_after_delay(confirm, 10)

@client.on(events.NewMessage(pattern=r"^\.(broadcast_all|ball)\b"))
async def broadcast_all_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    message = parts[1]
    confirm = await event.reply(f"📢 **Broadcast to EVERYWHERE:**\n\n{message}\n\nSend `.confirm_broadcast_all` to send to DMs + Groups + Channels.")
    ongoing_tasks['broadcast_all_msg'] = message; await delete_after_delay(confirm, 10)

@client.on(events.NewMessage(pattern=r"^\.(broadcast_current|bcur)\b"))
async def broadcast_current_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    message = parts[1]
    await event.reply(f"📢 **Broadcast in this chat:**\n\n{message}")

# BROADCAST CONFIRMATION HANDLERS
@client.on(events.NewMessage(pattern=r"^\.(confirm_broadcast_dm|cbdm)$"))
async def confirm_broadcast_dm_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if 'broadcast_dm_msg' not in ongoing_tasks:
        msg = await event.reply("❌ No broadcast message set"); await delete_after_delay(msg); return
    message = ongoing_tasks['broadcast_dm_msg']; progress = await event.reply("📤 Broadcasting to all DMs...")
    sent = 0; failed = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot and dialog.entity.id != OWNER_ID:
            try: await client.send_message(dialog.entity.id, message); sent += 1; await asyncio.sleep(1)
            except: failed += 1
    await progress.edit(f"✅ DM Broadcast complete!\n✓ Sent: {sent}\n✗ Failed: {failed}")
    ongoing_tasks.pop('broadcast_dm_msg', None); await delete_after_delay(progress, 5)

@client.on(events.NewMessage(pattern=r"^\.(confirm_broadcast_group|cbgrp)$"))
async def confirm_broadcast_group_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if 'broadcast_group_msg' not in ongoing_tasks:
        msg = await event.reply("❌ No broadcast message set"); await delete_after_delay(msg); return
    message = ongoing_tasks['broadcast_group_msg']; progress = await event.reply("📤 Broadcasting to all groups...")
    sent = 0; failed = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group and not dialog.entity.megagroup:
            try: await client.send_message(dialog.entity.id, message); sent += 1; await asyncio.sleep(1)
            except: failed += 1
    await progress.edit(f"✅ Group Broadcast complete!\n✓ Sent: {sent}\n✗ Failed: {failed}")
    ongoing_tasks.pop('broadcast_group_msg', None); await delete_after_delay(progress, 5)

@client.on(events.NewMessage(pattern=r"^\.(confirm_broadcast_channel|cbchn)$"))
async def confirm_broadcast_channel_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if 'broadcast_channel_msg' not in ongoing_tasks:
        msg = await event.reply("❌ No broadcast message set"); await delete_after_delay(msg); return
    message = ongoing_tasks['broadcast_channel_msg']; progress = await event.reply("📤 Broadcasting to all channels...")
    sent = 0; failed = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and not dialog.is_group:
            try: await client.send_message(dialog.entity.id, message); sent += 1; await asyncio.sleep(1)
            except: failed += 1
    await progress.edit(f"✅ Channel Broadcast complete!\n✓ Sent: {sent}\n✗ Failed: {failed}")
    ongoing_tasks.pop('broadcast_channel_msg', None); await delete_after_delay(progress, 5)

@client.on(events.NewMessage(pattern=r"^\.(confirm_broadcast_all|cball)$"))
async def confirm_broadcast_all_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if 'broadcast_all_msg' not in ongoing_tasks:
        msg = await event.reply("❌ No broadcast message set"); await delete_after_delay(msg); return
    message = ongoing_tasks['broadcast_all_msg']; progress = await event.reply("📤 Broadcasting to EVERYWHERE...")
    sent_dm = 0; failed_dm = 0; sent_grp = 0; failed_grp = 0; sent_chn = 0; failed_chn = 0
    
    async for dialog in client.iter_dialogs():
        try:
            if dialog.is_user and not dialog.entity.bot and dialog.entity.id != OWNER_ID:
                await client.send_message(dialog.entity.id, message); sent_dm += 1
            elif dialog.is_group and not dialog.entity.megagroup:
                await client.send_message(dialog.entity.id, message); sent_grp += 1
            elif dialog.is_channel and not dialog.is_group:
                await client.send_message(dialog.entity.id, message); sent_chn += 1
            await asyncio.sleep(1)
        except:
            if dialog.is_user: failed_dm += 1
            elif dialog.is_group: failed_grp += 1
            elif dialog.is_channel: failed_chn += 1
    
    total_sent = sent_dm + sent_grp + sent_chn
    total_failed = failed_dm + failed_grp + failed_chn
    
    result_msg = f"""
```✅ BROADCAST COMPLETE!

📱 DMs: ✓ {sent_dm} | ✗ {failed_dm}
👥 Groups: ✓ {sent_grp} | ✗ {failed_grp}  
📢 Channels: ✓ {sent_chn} | ✗ {failed_chn}
────────────────
📊 Total: ✓ {total_sent} | ✗ {total_failed}```
    """
    await progress.edit(result_msg)
    ongoing_tasks.pop('broadcast_all_msg', None); await delete_after_delay(progress, 8)

# 🔥 ROAST COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(roast_boy|rb)\b"))
async def roast_boy_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(boys_roast)}" if mention else random.choice(boys_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 Roast started! {count} messages```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(roast_girl|rg)\b"))
async def roast_girl_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(girls_roast)}" if mention else random.choice(girls_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 Roast started! {count} messages```"); await delete_after_delay(status_msg)

# Again Raid feature - Automatically reply to specific user's messages
again_raid_users = {}  # Dictionary to store {user_id: reply_message}

@client.on(events.NewMessage(pattern=r'\.(?:ar|again_raid)(?:\s+(.+))?', outgoing=True))
async def start_again_raid(event):
    """Start again raid on a user - automatically reply to their messages"""
    
    # Check if replying to a user
    if not event.is_reply:
        await event.delete()
        msg = await event.respond("❌ Please reply to a user to start again raid!\nUsage: .ar <message>")
        await asyncio.sleep(2)
        await msg.delete()
        return
    
    # Get the replied message
    reply_msg = await event.get_reply_message()
    user_id = reply_msg.sender_id
    
    # Get the message to send as auto-reply
    raid_message = event.pattern_match.group(1)
    
    if not raid_message:
        await event.delete()
        msg = await event.respond("❌ Please provide a message to send!\nUsage: .ar <message>")
        await asyncio.sleep(2)
        await msg.delete()
        return
    
    # Add user to again_raid dictionary
    again_raid_users[user_id] = raid_message
    
    # Delete the command message
    await event.delete()
    
    # Get user info
    try:
        user = await event.client.get_entity(user_id)
        user_name = user.first_name or "User"
        username = f"@{user.username}" if user.username else f"ID: {user_id}"
    except:
        user_name = "User"
        username = f"ID: {user_id}"
    
    # Send confirmation message
    msg = await event.respond(f"✅ **Again Raid Started!**\n\n**User:** {user_name}\n**Username:** {username}\n**Auto-Reply:** `{raid_message}`\n\n⚠️ Har message par automatically reply hoga!\n⛔ Rokne ke liye: `.sar` ya `.stop_again_raid`")
    
    # Wait for 3 seconds and delete the confirmation message
    await asyncio.sleep(3)
    await msg.delete()

@client.on(events.NewMessage(pattern=r'\.(?:sar|stop_again_raid)(?:\s+(.+))?$', outgoing=True))
async def stop_again_raid(event):
    """Stop again raid on a user"""
    
    # Check if "all" command
    if event.pattern_match.group(1) == "all":
        if len(again_raid_users) == 0:
            await event.delete()
            msg = await event.respond("❌ Koi again raid active nahi hai!")
            await asyncio.sleep(2)
            await msg.delete()
            return
        
        count = len(again_raid_users)
        again_raid_users.clear()
        
        await event.delete()
        msg = await event.respond(f"✅ **Sabhi Again Raids Stopped!**\n\nTotal {count} raids band kar diye gaye.")
        await asyncio.sleep(3)
        await msg.delete()
        return
    
    # Check if replying to a user
    if not event.is_reply:
        # Show list of active raids
        if len(again_raid_users) == 0:
            await event.delete()
            msg = await event.respond("❌ Koi again raid active nahi hai!")
            await asyncio.sleep(2)
            await msg.delete()
            return
        
        await event.delete()
        
        text = "**⚠️ Active Again Raids:**\n\n"
        for uid, msg_text in again_raid_users.items():
            try:
                user = await event.client.get_entity(uid)
                name = user.first_name or "Unknown"
                text += f"• **{name}** (ID: `{uid}`) - Reply: `{msg_text[:30]}...`\n"
            except:
                text += f"• **Unknown User** (ID: `{uid}`) - Reply: `{msg_text[:30]}...`\n"
        
        text += "\n**Stop karne ke liye:**\n"
        text += "• Kisi user ko reply karke `.sar` - specific user stop\n"
        text += "• `.sar all` - sabhi raids stop"
        
        msg = await event.respond(text)
        await asyncio.sleep(5)
        await msg.delete()
        return
    
    # Get the replied message
    reply_msg = await event.get_reply_message()
    user_id = reply_msg.sender_id
    
    # Delete the command message
    await event.delete()
    
    if user_id in again_raid_users:
        # Remove user from again_raid dictionary
        del again_raid_users[user_id]
        
        # Get user info
        try:
            user = await event.client.get_entity(user_id)
            user_name = user.first_name or "User"
        except:
            user_name = "User"
        
        msg = await event.respond(f"✅ **Again Raid Stopped!**\n\nUser: {user_name} ke liye again raid band kar diya gaya.")
        await asyncio.sleep(3)
        await msg.delete()
    else:
        msg = await event.respond("❌ Ye user again raid mein nahi hai!")
        await asyncio.sleep(2)
        await msg.delete()

@client.on(events.NewMessage(incoming=True))
async def again_raid_handler(event):
    """Handle incoming messages and reply if user is in again_raid"""
    
    # Ignore if message is from self
    if event.message.out:
        return
    
    # Get my user ID
    me = await event.client.get_me()
    
    # Ignore if sender is myself
    if event.sender_id == me.id:
        return
    
    # Check if sender is in again_raid dictionary
    if event.sender_id in again_raid_users:
        raid_message = again_raid_users[event.sender_id]
        
        # Small delay to avoid flood
        await asyncio.sleep(0.1)
        
        # Reply to the message
        try:
            await event.reply(raid_message)
        except Exception as e:
            # If can't reply, remove from again_raid
            logger.error(f"Error in again_raid reply: {e}")
            if event.sender_id in again_raid_users:
                del again_raid_users[event.sender_id]
                
@client.on(events.NewMessage(pattern=r"^\.(roast_abuse|ra)\b"))
async def roast_abuse_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(abuse_roast)}" if mention else random.choice(abuse_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 Abuse roast started! {count} messages```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(flirt_girl|fg)\b"))
async def flirt_girl_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(flirt_lines)}" if mention else random.choice(flirt_lines)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```💖 Flirt started! {count} messages```"); await delete_after_delay(status_msg)

# 🔥 HINDI ROAST COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_boy|hrb)\b"))
async def hindi_roast_boy_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(hindi_boys_roast)}" if mention else random.choice(hindi_boys_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 लड़का रोस्ट शुरू! {count} मैसेज```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_girl|hrg)\b"))
async def hindi_roast_girl_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(hindi_girls_roast)}" if mention else random.choice(hindi_girls_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 लड़की रोस्ट शुरू! {count} मैसेज```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_abuse|hra)\b"))
async def hindi_roast_abuse_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(hindi_abuse_roast)}" if mention else random.choice(hindi_abuse_roast)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```🔥 गाली रोस्ट शुरू! {count} मैसेज```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(hindi_flirt_girl|hfg)\b"))
async def hindi_flirt_girl_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(); count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(hindi_flirt_lines)}" if mention else random.choice(hindi_flirt_lines)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```💖 फ्लर्ट शुरू! {count} मैसेज```"); await delete_after_delay(status_msg)

# 💣 RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid100|r100)\b"))
async def raid100_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    msg = parts[1]; msgs = [msg] * 100
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply("```💣 Raid100 started!```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(raid|rd)\b"))
async def raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit(): return
    count = min(int(parts[1]), MAX_PER_RUN); msg = parts[2]; msgs = [msg] * count
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event))
    ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```💣 Raid started! {count} messages```"); await delete_after_delay(status_msg)

# 🔁 AUTO-REPLY RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(reply_raid|rr)\b"))
async def reply_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    reply_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```🔁 Reply raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(flirt_raid|fr)\b"))
async def flirt_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    flirt_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💖 Flirt raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💖 LOVE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(love_raid|lr)\b"))
async def love_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    love_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💖 Love raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💫 QUOTE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(quote_raid|qr)\b"))
async def quote_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    quote_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💫 Quote raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💕 MASS LOVE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(mass_love_raid|mlr)\b"))
async def mass_love_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    mass_love_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💕 Mass love raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 📜 SHAYARI RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(shayari_raid|sr)\b"))
async def shayari_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    shayari_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"📜 Shayari raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 📜 RAID SHAYARI RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid_shayari_raid|rsr)\b"))
async def raid_shayari_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    raid_shayari_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```📜 Raid shayari activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 🔥 ROAST BOY RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(roast_boy_raid|rbr)\b"))
async def roast_boy_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    roast_boy_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"🔥 Roast boy raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 👧 ROAST GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(roast_girl_raid|rgr)\b"))
async def roast_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    roast_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```👧 Roast girl raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 🗣️ ROAST ABUSE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(roast_abuse_raid|rar)\b"))
async def roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    roast_abuse_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```🗣️ Roast abuse raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 💖 FLIRT GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(flirt_girl_raid|fgr)\b"))
async def flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    flirt_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```💖 Flirt girl raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 🔥 HINDI ROAST BOY RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_boy_raid|hrbr)\b"))
async def hindi_roast_boy_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_roast_boy_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"🔥 Hindi roast boy raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 👧 HINDI ROAST GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_girl_raid|hrgr)\b"))
async def hindi_roast_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_roast_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```👧 Hindi roast girl raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 🗣️ HINDI ROAST ABUSE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_abuse_raid|hrar)\b"))
async def hindi_roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_roast_abuse_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```🗣️ Hindi roast abuse raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 💖 HINDI FLIRT GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_flirt_girl_raid|hfgr)\b"))
async def hindi_flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_flirt_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```💖 Hindi flirt girl raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 💣 RAID100 RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid100_raid|r100r)\b"))
async def raid100_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    raid100_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```💣 Raid100 raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# 💣 RAID RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid_raid|rdr)\b"))
async def raid_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"```💣 Raid raid activated on {target_user.first_name}!```"); await delete_after_delay(status_msg)

# STOP RAID COMMANDS
@client.on(events.NewMessage(pattern=r"^\.(stop_reply_raid|srr)$"))
async def stop_reply_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in reply_raid_targets:
        reply_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Reply raid stopped")
    else: status_msg = await event.reply("❌ No active reply raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_flirt_raid|sfr)$"))
async def stop_flirt_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in flirt_raid_targets:
        flirt_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Flirt raid stopped")
    else: status_msg = await event.reply("❌ No active flirt raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_love_raid|slr)$"))
async def stop_love_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in love_raid_targets:
        love_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Love raid stopped")
    else: status_msg = await event.reply("❌ No active love raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_quote_raid|sqr)$"))
async def stop_quote_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in quote_raid_targets:
        quote_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Quote raid stopped")
    else: status_msg = await event.reply("❌ No active quote raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_mass_love_raid|smlr)$"))
async def stop_mass_love_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in mass_love_raid_targets:
        mass_love_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Mass love raid stopped")
    else: status_msg = await event.reply("❌ No active mass love raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_shayari_raid|ssr)$"))
async def stop_shayari_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in shayari_raid_targets:
        shayari_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Shayari raid stopped")
    else: status_msg = await event.reply("❌ No active shayari raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_raid_shayari_raid|srsr)$"))
async def stop_raid_shayari_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in raid_shayari_targets:
        raid_shayari_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Raid shayari stopped")
    else: status_msg = await event.reply("❌ No active raid shayari")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_roast_boy_raid|srbr)$"))
async def stop_roast_boy_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in roast_boy_raid_targets:
        roast_boy_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Roast boy raid stopped")
    else: status_msg = await event.reply("❌ No active roast boy raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_roast_girl_raid|srgr)$"))
async def stop_roast_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in roast_girl_raid_targets:
        roast_girl_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Roast girl raid stopped")
    else: status_msg = await event.reply("❌ No active roast girl raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_roast_abuse_raid|srar)$"))
async def stop_roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in roast_abuse_raid_targets:
        roast_abuse_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Roast abuse raid stopped")
    else: status_msg = await event.reply("❌ No active roast abuse raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_flirt_girl_raid|sfgr)$"))
async def stop_flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in flirt_girl_raid_targets:
        flirt_girl_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Flirt girl raid stopped")
    else: status_msg = await event.reply("❌ No active flirt girl raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_hindi_roast_boy_raid|shrbr)$"))
async def stop_hindi_roast_boy_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in hindi_roast_boy_raid_targets:
        hindi_roast_boy_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Hindi roast boy raid stopped")
    else: status_msg = await event.reply("❌ No active hindi roast boy raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_hindi_roast_girl_raid|shrgr)$"))
async def stop_hindi_roast_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in hindi_roast_girl_raid_targets:
        hindi_roast_girl_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Hindi roast girl raid stopped")
    else: status_msg = await event.reply("❌ No active hindi roast girl raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_hindi_roast_abuse_raid|shrar)$"))
async def stop_hindi_roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in hindi_roast_abuse_raid_targets:
        hindi_roast_abuse_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Hindi roast abuse raid stopped")
    else: status_msg = await event.reply("❌ No active hindi roast abuse raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_hindi_flirt_girl_raid|shfgr)$"))
async def stop_hindi_flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in hindi_flirt_girl_raid_targets:
        hindi_flirt_girl_raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Hindi flirt girl raid stopped")
    else: status_msg = await event.reply("❌ No active hindi flirt girl raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_raid100_raid|sr100r)$"))
async def stop_raid100_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in raid100_targets:
        raid100_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Raid100 raid stopped")
    else: status_msg = await event.reply("❌ No active raid100 raid")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_raid_raid|srdr)$"))
async def stop_raid_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.chat_id in raid_targets:
        raid_targets.pop(event.chat_id); status_msg = await event.reply("🛑 Raid raid stopped")
    else: status_msg = await event.reply("❌ No active raid raid")
    await delete_after_delay(status_msg)

# Auto-reply to targeted users
@client.on(events.NewMessage)
async def auto_reply_handler(event):
    if not event.message or event.sender_id == OWNER_ID: return
    chat_id = event.chat_id; sender_id = event.sender_id
    try:
        # Existing raids
        if chat_id in reply_raid_targets and sender_id == reply_raid_targets[chat_id]:
            await event.reply(random.choice(reply_raid_lines))
        if chat_id in flirt_raid_targets and sender_id == flirt_raid_targets[chat_id]:
            await event.reply(random.choice(flirt_raid_lines))
        
        # New raids
        if chat_id in love_raid_targets and sender_id == love_raid_targets[chat_id]:
            await event.reply(random.choice(love_raid_lines))
        if chat_id in quote_raid_targets and sender_id == quote_raid_targets[chat_id]:
            await event.reply(random.choice(quote_raid_lines))
        if chat_id in mass_love_raid_targets and sender_id == mass_love_raid_targets[chat_id]:
            await event.reply(random.choice(mass_love_raid_lines))
        if chat_id in shayari_raid_targets and sender_id == shayari_raid_targets[chat_id]:
            await event.reply(random.choice(shayari_raid_lines))
        if chat_id in raid_shayari_targets and sender_id == raid_shayari_targets[chat_id]:
            await event.reply(random.choice(raid_shayari_lines))
        if chat_id in roast_boy_raid_targets and sender_id == roast_boy_raid_targets[chat_id]:
            await event.reply(random.choice(roast_boy_raid_lines))
        if chat_id in roast_girl_raid_targets and sender_id == roast_girl_raid_targets[chat_id]:
            await event.reply(random.choice(roast_girl_raid_lines))
        if chat_id in roast_abuse_raid_targets and sender_id == roast_abuse_raid_targets[chat_id]:
            await event.reply(random.choice(roast_abuse_raid_lines))
        if chat_id in flirt_girl_raid_targets and sender_id == flirt_girl_raid_targets[chat_id]:
            await event.reply(random.choice(flirt_girl_raid_lines))
        if chat_id in hindi_roast_boy_raid_targets and sender_id == hindi_roast_boy_raid_targets[chat_id]:
            await event.reply(random.choice(hindi_roast_boy_raid_lines))
        if chat_id in hindi_roast_girl_raid_targets and sender_id == hindi_roast_girl_raid_targets[chat_id]:
            await event.reply(random.choice(hindi_roast_girl_raid_lines))
        if chat_id in hindi_roast_abuse_raid_targets and sender_id == hindi_roast_abuse_raid_targets[chat_id]:
            await event.reply(random.choice(hindi_roast_abuse_raid_lines))
        if chat_id in hindi_flirt_girl_raid_targets and sender_id == hindi_flirt_girl_raid_targets[chat_id]:
            await event.reply(random.choice(hindi_flirt_girl_raid_lines))
        if chat_id in raid100_targets and sender_id == raid100_targets[chat_id]:
            await event.reply(random.choice(raid100_lines))
        if chat_id in raid_targets and sender_id == raid_targets[chat_id]:
            await event.reply(random.choice(raid_lines))
    except: pass

# 💖 ROMANCE COMMANDS - LONG + SHORT WITH @USERNAME SUPPORT
@client.on(events.NewMessage(pattern=r"^\.(love|lv)\b"))
async def love_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    mention = await get_target_mention(event, parts)
    love_msg = await event.reply(f"{mention} {random.choice(love_lines)}" if mention else f"💖 {random.choice(love_lines)}")
    await delete_after_delay(love_msg)

@client.on(events.NewMessage(pattern=r"^\.(quote|qt)\b"))
async def quote_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    mention = await get_target_mention(event, parts)
    quote_msg = await event.reply(f"{mention} {random.choice(quote_lines)}" if mention else f"💫 {random.choice(quote_lines)}")
    await delete_after_delay(quote_msg)

@client.on(events.NewMessage(pattern=r"^\.(mass_love|mlove|ml)\b"))
async def mass_love_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(love_lines)}" if mention else random.choice(love_lines)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event)); ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```💖 Mass love started! {count} messages```"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(shayari|shr)\b"))
async def shayari_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    mention = await get_target_mention(event, parts)
    shayari_msg = await event.reply(f"{mention} {random.choice(shayari_lines)}" if mention else f"📜 {random.choice(shayari_lines)}")
    await delete_after_delay(shayari_msg)

@client.on(events.NewMessage(pattern=r"^\.(raid_shayari|raidshayari|rs)\b"))
async def raid_shayari_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    count = 1; target_user = None
    if len(parts) >= 2:
        if parts[-1].isdigit():
            count = min(int(parts[-1]), MAX_PER_RUN)
            if len(parts) > 2: target_user = await get_target_user(event, parts[:-1])
        else: target_user = await get_target_user(event, parts)
    mention = await get_target_mention(event, parts)
    msgs = [(f"{mention} {random.choice(shayari_lines)}" if mention else random.choice(shayari_lines)) for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event)); ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"```📜 Shayari raid started! {count} messages```"); await delete_after_delay(status_msg)

# 👥 SPECIAL FEATURES - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(clone|cl)\b"))
async def clone_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user:
        status_msg = await event.reply("❌ Reply to user or use @username"); await delete_after_delay(status_msg); return
    if target_user.id == OWNER_ID:
        status_msg = await event.reply("❌ Can't clone yourself!"); await delete_after_delay(status_msg); return
    cloning_msg = await event.reply("🔄 Cloning profile...")
    success = await clone_profile(target_user)
    if success:
        cloned_bio = user_clones[OWNER_ID]['target_bio']
        await cloning_msg.edit(f"```✅ **Profile Cloned!**\n\n👤 Now: **{target_user.first_name}**\n📝 Bio: {cloned_bio if cloned_bio else 'No bio'}\n🖼️ PFP: ✅ Cloned\n\nUse `.unclone` to restore.```")
        await delete_after_delay(cloning_msg, 3)
    else: await cloning_msg.edit("❌ Clone failed!"); await delete_after_delay(cloning_msg)

@client.on(events.NewMessage(pattern=r"^\.(unclone|ucl)$"))
async def unclone_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if OWNER_ID not in user_clones:
        status_msg = await event.reply("❌ No active clone"); await delete_after_delay(status_msg); return
    restoring_msg = await event.reply("🔄 Restoring profile...")
    success = await restore_original_profile()
    if success: await restoring_msg.edit("✅ **Profile Restored!**"); await delete_after_delay(restoring_msg, 3)
    else: await restoring_msg.edit("❌ Restore failed!"); await delete_after_delay(restoring_msg)

# 🏷 TAGGING COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(mass_tag|mtag|mt)\b"))
async def mass_tag_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=3)
    if len(parts) < 4 or not parts[2].isdigit(): return
    target_user = await get_target_user(event, [parts[0], parts[1]])
    if not target_user: return
    count = min(int(parts[2]), MAX_PER_RUN); msg = parts[3]
    mention = f"[{target_user.first_name}](tg://user?id={target_user.id})"
    msgs = [f"{mention} {msg}" for _ in range(count)]
    prev = ongoing_tasks.get(event.chat_id)
    if prev and not prev.done(): prev.cancel()
    task = asyncio.create_task(send_loop(event.chat_id, msgs, event)); ongoing_tasks[event.chat_id] = task
    status_msg = await event.reply(f"🏷 Mass tag started! {count} messages"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(tag_all|tagall|ta)\b"))
async def tagall_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    msg = parts[1]
    try:
        participants = []
        async for user in client.iter_participants(event.chat_id):
            if not user.bot and user.id != OWNER_ID: participants.append(user)
        async def tag_loop():
            for user in participants:
                if event.chat_id not in ongoing_tasks: break
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                await client.send_message(event.chat_id, f"{mention} {msg}")
                await asyncio.sleep(TAG_DELAY)  # 🔥 6 SECONDS DELAY FOR TAGGING
        prev = ongoing_tasks.get(event.chat_id)
        if prev and not prev.done(): prev.cancel()
        task = asyncio.create_task(tag_loop()); ongoing_tasks[event.chat_id] = task
        status_msg = await event.reply(f"🏷 Tagging {len(participants)} users"); await delete_after_delay(status_msg)
    except: pass

@client.on(events.NewMessage(pattern=r"^\.(tag_admins|tagadmins|tadm)\b"))
async def tagadmins_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2: return
    msg = parts[1]
    try:
        admins = []
        async for user in client.iter_participants(event.chat_id, filter=types.ChannelParticipantsAdmins):
            if not user.bot and user.id != OWNER_ID: admins.append(user)
        async def tag_loop():
            for user in admins:
                if event.chat_id not in ongoing_tasks: break
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                await client.send_message(event.chat_id, f"{mention} {msg}")
                await asyncio.sleep(TAG_DELAY)  # 🔥 6 SECONDS DELAY FOR TAGGING
        prev = ongoing_tasks.get(event.chat_id)
        if prev and not prev.done(): prev.cancel()
        task = asyncio.create_task(tag_loop()); ongoing_tasks[event.chat_id] = task
        status_msg = await event.reply(f"🏷 Tagging {len(admins)} admins"); await delete_after_delay(status_msg)
    except: pass

# 📊 INFO COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(user_info|userinfo|ui)\b"))
async def userinfo_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split()) or await event.get_sender()
    user_info = f"""
```👤 User Info

Name: {target_user.first_name} {target_user.last_name or ''}
Username: @{target_user.username or 'N/A'}
User ID: `{target_user.id}`
Bot: {'✅ Yes' if target_user.bot else '❌ No'}
DC ID: {target_user.photo.dc_id if target_user.photo else 'N/A'}

Chat ID: {event.chat_id}```
    """
    await event.reply(user_info)


import psutil

@client.on(events.NewMessage(pattern=r"^\.(ping|pg)$"))
async def ping_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    
    start = time.time()
    msg = await event.reply("🏓 Pong!")
    end = time.time()
    response_time = (end - start) * 1000
    
    # Check API latency
    api_start = time.time()
    await client.get_me()
    api_end = time.time()
    api_latency = (api_end - api_start) * 1000
    
    # Calculate uptime
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = ""
    if days > 0:
        uptime_str += str(days) + "d "
    if hours > 0:
        uptime_str += str(hours) + "h "
    if minutes > 0:
        uptime_str += str(minutes) + "m "
    uptime_str += str(seconds) + "s"
    
    # Get system info
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    
    # Build response text exactly as you want
    response_text = "```🏓 Pong!\n"
    
    response_text += "📡 Response Time: " + str(round(response_time, 2)) + "ms\n"
    response_text += "💓 API Latency: " + str(round(api_latency, 2)) + "ms\n"
    response_text += "🖥️ CPU Usage: " + str(cpu_usage) + "%\n"
    response_text += "🧠 Memory: " + str(memory_usage) + "%\n"
    response_text += "📊 Uptime: " + uptime_str + "```"
    
    await msg.edit(response_text)
    await delete_after_delay(msg)
    
@client.on(events.NewMessage(pattern=r"^\.(alive|al)$"))
async def alive_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    alive_msg = await event.reply("🤖 **BOT IS ALIVE AND RUNNING!**\n\n⚡️ Status: Online\n🔥 Features: Working\n💖 Owner: Active");
    await delete_after_delay(alive_msg)

# 🛑 CONTROL COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(stop|st)$"))
async def stop_all_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    stopped_count = 0
    for chat_id, task in list(ongoing_tasks.items()):
        if not task.done(): task.cancel(); stopped_count += 1
    ongoing_tasks.clear()
    if event.chat_id in reply_raid_targets: reply_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in flirt_raid_targets: flirt_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in love_raid_targets: love_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in quote_raid_targets: quote_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in mass_love_raid_targets: mass_love_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in shayari_raid_targets: shayari_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in raid_shayari_targets: raid_shayari_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in roast_boy_raid_targets: roast_boy_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in roast_girl_raid_targets: roast_girl_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in roast_abuse_raid_targets: roast_abuse_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in flirt_girl_raid_targets: flirt_girl_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in hindi_roast_boy_raid_targets: hindi_roast_boy_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in hindi_roast_girl_raid_targets: hindi_roast_girl_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in hindi_roast_abuse_raid_targets: hindi_roast_abuse_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in hindi_flirt_girl_raid_targets: hindi_flirt_girl_raid_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in raid100_targets: raid100_targets.pop(event.chat_id); stopped_count += 1
    if event.chat_id in raid_targets: raid_targets.pop(event.chat_id); stopped_count += 1
    status_msg = await event.reply(f"🛑 Stopped {stopped_count} tasks"); await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_roast|stoproast|str)$"))
async def stop_roast(event):
    if not is_owner(event): return
    await delete_command_message(event)
    task = ongoing_tasks.get(event.chat_id)
    if task and not task.done(): task.cancel(); ongoing_tasks.pop(event.chat_id, None); status_msg = await event.reply("🛑 Roast stopped")
    else: status_msg = await event.reply("❌ No active roast")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(stop_tag|stoptag|stt)$"))
async def stop_tag(event):
    if not is_owner(event): return
    await delete_command_message(event)
    task = ongoing_tasks.get(event.chat_id)
    if task and not task.done(): task.cancel(); ongoing_tasks.pop(event.chat_id, None); status_msg = await event.reply("🛑 Tagging stopped")
    else: status_msg = await event.reply("❌ No active tagging")
    await delete_after_delay(status_msg)

@client.on(events.NewMessage(pattern=r"^\.(purge|pg)\b"))
async def purge_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return
    count = int(parts[1])
    try:
        deleted = 0
        async for message in client.iter_messages(event.chat_id, limit=count, from_user='me'):
            await message.delete(); deleted += 1; await asyncio.sleep(0.5)
        status_msg = await event.reply(f"🗑️ Purged {deleted} messages"); await delete_after_delay(status_msg)
    except: pass

@client.on(events.NewMessage(pattern=r"^\.(purge_all|purgeall|pga)$"))
async def purge_all_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    if event.is_private:
        status_msg = await event.reply("❌ Groups only"); await delete_after_delay(status_msg); return
    try:
        count = 0
        async for message in client.iter_messages(event.chat_id, from_user='me'):
            await message.delete(); count += 1; await asyncio.sleep(0.5)
        status_msg = await event.reply(f"🗑️ Deleted {count} messages"); await delete_after_delay(status_msg)
    except: pass


# 📱 STATUS COMMAND - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(status|stat)\b"))
async def status_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    if len(parts) < 2: return
    global user_status; status_type = parts[1].lower()
    if status_type == 'online':
        user_status = "online"; await client(functions.account.UpdateStatusRequest(offline=False))
        status_msg = await event.reply("🟢 **Status: ONLINE**")
    elif status_type == 'offline':
        user_status = "offline"; await client(functions.account.UpdateStatusRequest(offline=True))
        status_msg = await event.reply("🔴 **Status: OFFLINE**")
    else: status_msg = await event.reply("❌ Use: .status online OR .status offline")
    await delete_after_delay(status_msg)

# ❓ HELP COMMAND
@client.on(events.NewMessage(pattern=r"^\.help$"))
async def help_main_menu(event):
    if not is_owner(event): return
    await delete_command_message(event)
    main_menu = """
```╭━━━━⟬🤖 ULTIMATE NEXUS USERBOT HELP MENU 🤖⟭━━━━╮
┃                                                
┃    📚 Select a page to view commands:          
┃                                                
┃    ⟡➣ PAGE 1 - SETTINGS & ANIMATION           
┃        .help1 - Delay, Broadcast, Animation    
┃                                                
┃    ⟡➣ PAGE 2 - ROAST AND SPAM COMMANDS        
┃        .help2 - English/Hindi Roast & Flirt    
┃                                                
┃    ⟡➣ PAGE 3 - AUTO RAID COMMANDS              
┃        .help3 - Raid and Auto-Raid commands    
┃                                                
┃    ⟡➣ PAGE 4 - STOP COMMANDS                   
┃        .help4 - All Stop commands               
┃                                                
┃    ⟡➣ PAGE 5 - ROMANCE & TAGGING               
┃        .help5 - Love, Shayari, Tagging         
┃                                                
┃    ⟡➣ PAGE 6 - SPECIAL FEATURES                 
┃        .help6 - Clone, Weather, AI Image       
┃                                                
┃    ⟡➣ PAGE 7 - MODERATION                       
┃        .help7 - Gban, Gmute, Purge             
┃                                                
┃    ⟡➣ PAGE 8 - OSINT & INFO                     
┃        .help8 - Phone, Aadhar, IP lookup       
┃                                                
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(main_menu)

# PAGE 1 - SETTINGS & ANIMATION
@client.on(events.NewMessage(pattern=r"^\.help1$"))
async def help_page1(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page1 = """
```╭━━━━⟬📖 SETTINGS & ANIMATION⟭━━━━╮
┃                                  
┃    ⚙️ Settings Commands           
┃    ⟡➣ .delay / .dly <seconds>    
┃        Change delay (Current: 6s) 
┃                                  
┃    🎬 Animation Commands          
┃    ⟡➣ .hack [@user] - Hacking (~120 sec)
┃    ⟡➣ .middlefinger / .mf [@user] - Middle finger
┃    ⟡➣ .dance - Dance animation    
┃    ⟡➣ .love - Love animation      
┃    ⟡➣ .bomb - Bomb blast          
┃    ⟡➣ .clock - Clock animation    
┃    ⟡➣ .train - Moving train       
┃    ⟡➣ .party - Party animation    
┃    ⟡➣ .ghost - Ghost appearance   
┃    ⟡➣ .india - India patriotic    
┃    ⟡➣ .rain - Rain animation      
┃    ⟡➣ .storm - Storm animation    
┃    ⟡➣ .snow - Snowfall animation  
┃    ⟡➣ .fire - Fire effect         
┃    ⟡➣ .lightning - Lightning strike
┃    ⟡➣ .cobra - Cobra snake        
┃    ⟡➣ .heart - Heart animation    
┃    ⟡➣ .helicopter - Helicopter    
┃    ⟡➣ .gmm - Good morning         
┃    ⟡➣ .gn - Good night            
┃    ⟡➣ .drugs - Drugs warning      
┃    ⟡➣ .gf - Girlfriend animation  
┃    ⟡➣ .tank - Tank war            
┃    ⟡➣ .hmm - Thinking animation   
┃    ⟡➣ .fuck - Angry abuse         
┃    ⟡➣ .cat - Cute cat animation   
┃    ⟡➣ .pikachu - Pikachu animation
┃    ⟡➣ .nikal - Go away animation  
┃                                  
┃    📢 Broadcast Commands           
┃    ⟡➣ .broadcast_dm / .bdm <msg> - All DMs
┃    ⟡➣ .broadcast_group / .bgrp <msg> - All groups
┃    ⟡➣ .broadcast_channel / .bchn <msg> - All channels
┃    ⟡➣ .broadcast_all / .ball <msg> - All chats
┃    ⟡➣ .broadcast_current / .bcur <msg> - Current chat
┃                                  
┃    Navigate: .help (Menu) | .help2 (Next)  
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page1)

# PAGE 2 - ROAST COMMANDS
@client.on(events.NewMessage(pattern=r"^\.help2$"))
async def help_page2(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page2 = """
```╭━━━━⟬📖 ROAST COMMANDS⟭━━━━╮
┃                            
┃    🔥 Roast Commands (English)
┃    ⟡➣ .roast_boy / .rb [@user] [count]
┃    ⟡➣ .roast_girl / .rg [@user] [count]
┃    ⟡➣ .roast_abuse / .ra [@user] [count]
┃    ⟡➣ .flirt_girl / .fg [@user] [count]
┃                            
┃    🔥 Roast Commands (Hindi)
┃    ⟡➣ .hindi_roast_boy / .hrb [@user] [count]
┃    ⟡➣ .hindi_roast_girl / .hrg [@user] [count]
┃    ⟡➣ .hindi_roast_abuse / .hra [@user] [count]
┃    ⟡➣ .hindi_flirt_girl / .hfg [@user] [count]
┃                            
┃    💣 Raid Commands        
┃    ⟡➣ .raid100 / .r100 <msg> - 100x message
┃    ⟡➣ .raid / .rd <count> <msg> - Custom
┃    ⟡➣ .spam <delay> <msg> - Spam user
┃                            
┃    Navigate: .help1 (Prev) | .help (Menu) | .help3 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page2)

# PAGE 3 - RAID COMMANDS
@client.on(events.NewMessage(pattern=r"^\.help3$"))
async def help_page3(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page3 = """
```╭━━━━⟬📖 RAID COMMANDS⟭━━━━╮
┃                            
┃    🔁 Auto-Reply Raids      
┃    ⟡➣ .reply_raid / .rr [@user]
┃    ⟡➣ .flirt_raid / .fr [@user]
┃    ⟡➣ .love_raid / .lr [@user]
┃    ⟡➣ .quote_raid / .qr [@user]
┃    ⟡➣ .mass_love_raid / .mlr [@user]
┃    ⟡➣ .shayari_raid / .sr [@user]
┃    ⟡➣ .raid_shayari_raid / .rsr [@user]
┃    ⟡➣ .roast_boy_raid / .rbr [@user]
┃    ⟡➣ .roast_girl_raid / .rgr [@user]
┃    ⟡➣ .roast_abuse_raid / .rar [@user]
┃    ⟡➣ .flirt_girl_raid / .fgr [@user]
┃    ⟡➣ .hindi_roast_boy_raid / .hrbr [@user]
┃    ⟡➣ .hindi_roast_girl_raid / .hrgr [@user]
┃    ⟡➣ .hindi_roast_abuse_raid / .hrar [@user]
┃    ⟡➣ .hindi_flirt_girl_raid / .hfgr [@user]
┃    ⟡➣ .raid100_raid / .r100r [@user]
┃    ⟡➣ .raid_raid / .rdr [@user]
┃                            
┃    Navigate: .help2 (Prev) | .help (Menu) | .help4 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page3)

# PAGE 4 - STOP COMMANDS
@client.on(events.NewMessage(pattern=r"^\.help4$"))
async def help_page4(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page4 = """
```╭━━━━⟬📖 STOP COMMANDS⟭━━━━╮
┃                            
┃    🛑 Stop Commands         
┃    ⟡➣ .stop_reply_raid / .srr
┃    ⟡➣ .stop_flirt_raid / .sfr
┃    ⟡➣ .stop_love_raid / .slr
┃    ⟡➣ .stop_quote_raid / .sqr
┃    ⟡➣ .stop_mass_love_raid / .smlr
┃    ⟡➣ .stop_shayari_raid / .ssr
┃    ⟡➣ .stop_raid_shayari_raid / .srsr
┃    ⟡➣ .stop_roast_boy_raid / .srbr
┃    ⟡➣ .stop_roast_girl_raid / .srgr
┃    ⟡➣ .stop_roast_abuse_raid / .srar
┃    ⟡➣ .stop_flirt_girl_raid / .sfgr
┃    ⟡➣ .stop_hindi_roast_boy_raid / .shrbr
┃    ⟡➣ .stop_hindi_roast_girl_raid / .shrgr
┃    ⟡➣ .stop_hindi_roast_abuse_raid / .shrar
┃    ⟡➣ .stop_hindi_flirt_girl_raid / .shfgr
┃    ⟡➣ .stop_raid100_raid / .sr100r
┃    ⟡➣ .stop_raid_raid / .srdr
┃    ⟡➣ .stop / .st - Stop all tasks
┃    ⟡➣ .stop_roast / .stoproast / .str
┃    ⟡➣ .stop_tag / .stoptag / .stt
┃                            
┃    Navigate: .help3 (Prev) | .help (Menu) | .help5 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page4)

# PAGE 5 - ROMANCE & TAGGING
@client.on(events.NewMessage(pattern=r"^\.help5$"))
async def help_page5(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page5 = """
```╭━━━━⟬📖 ROMANCE & TAGGING⟭━━━━╮
┃                                
┃    💖 Romance Commands         
┃    ⟡➣ .love / .lv [@user]     
┃    ⟡➣ .quote / .qt [@user]    
┃    ⟡➣ .mass_love / .mlove / .ml [@user] [count]
┃    ⟡➣ .shayari / .shr [@user] 
┃    ⟡➣ .raid_shayari / .raidshayari / .rs [@user] [count]
┃                                
┃    🏷 Tagging Commands         
┃    ⟡➣ .tag_all / .tagall / .ta <msg>
┃    ⟡➣ .tag_admins / .tagadmins / .tadm <msg>
┃    ⟡➣ .all <msg> - Faster tagging
┃    ⟡➣ .cancel - Cancel .all tagging
┃                                
┃    Navigate: .help4 (Prev) | .help (Menu) | .help6 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page5)

# PAGE 6 - SPECIAL FEATURES
@client.on(events.NewMessage(pattern=r"^\.help6$"))
async def help_page6(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page6 = """
```╭━━━━⟬📖 SPECIAL FEATURES⟭━━━━╮
┃                              
┃    👥 Special Features       
┃    ⟡➣ .clone / .cl [@user] - Clone
┃    ⟡➣ .unclone / .ucl - Revert
┃    ⟡➣ .translate / .tr - Translate
┃    ⟡➣ .cp <reply to a photo> - update profile picture
┃    ⟡➣ .rcp - restore profile picture
┃    ⟡➣ .bio <text> - Update Bio 
┃    ⟡➣ .history [@user] - Name history
┃    ⟡➣ .weather [city] - Weather
┃    ⟡➣ .zombie - Remove deleted accounts
┃    ⟡➣ .whois - User info     
┃    ⟡➣ .search <query> - Web search
┃    ⟡➣ .dp - Download profile pic
┃    ⟡➣ .create [prompt] - AI image
┃    ⟡➣ .online - AI online mode
┃    ⟡➣ .offline - AI offline mode
┃    ⟡➣ .qr <text> - QR generator
┃    ⟡➣ .dl <link> - Download videos
┃    ⟡➣ .tts <m/f> <hindi/eng> <text> - Text to speech
┃    ⟡➣ .report <count> <reason> - report message to telegram
┃    ⟡➣ .name <name> - Stylish name
┃    ⟡➣ .ascii <text> - ASCII art
┃    ⟡➣ .ss <url> - Screenshot  
┃    ⟡➣ .startvc - Start voice chat
┃    ⟡➣ .join - Join voice chat 
┃    ⟡➣ .left - Leave voice chat
┃                              
┃    Navigate: .help5 (Prev) | .help (Menu) | .help7 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page6)

# PAGE 7 - MODERATION
@client.on(events.NewMessage(pattern=r"^\.help7$"))
async def help_page7(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page7 = """
```╭━━━━⟬📖 MODERATION⟭━━━━╮
┃                        
┃    🤵 Moderator Commands
┃    ⟡➣ .gmute - Global mute
┃    ⟡➣ .gunmute - Global unmute
┃    ⟡➣ .gmutedlist - Muted list
┃    ⟡➣ .gban - Global ban  
┃    ⟡➣ .gungban - Global unban
┃    ⟡➣ .gbanlist - Ban list
┃    ⟡➣ .adminlist - Admins list
┃    ⟡➣ .ban - Ban user
┃    ⟡➣ .mute - mute user
┃    ⟡➣ .kick - kick user
┃    ⟡➣ .unban - Unban user
┃    ⟡➣ .unmute - unmute user
┃    ⟡➣ .promote - Promote admin
┃    ⟡➣ .demote - Demote admin
┃    ⟡➣ .pin - Pin message  
┃    ⟡➣ .unpin - Unpin message
┃                        
┃    Navigate: .help6 (Prev) | .help (Menu) | .help8 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page7)

# PAGE 8 - OSINT & CONTROL
@client.on(events.NewMessage(pattern=r"^\.help8$"))
async def help_page8(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page8 = """
```╭━━━━⟬📖 OSINT & CONTROL⟭━━━━╮
┃                              
┃    💻 OSINT Commands         
┃    ⟡➣ .num [number] - Phone lookup
┃    ⟡➣ .aadhar [number] - Aadhar lookup
┃    ⟡➣ .vehicle [number] - Vehicle lookup
┃    ⟡➣ .ip [IP] - IP lookup  
┃    ⟡➣ .pin [code] - PIN lookup
┃                              
┃    📊 Info Commands          
┃    ⟡➣ .user_info / .userinfo / .ui [@user]
┃    ⟡➣ .ping / .pg - Status   
┃    ⟡➣ .alive / .al - Check   
┃                              
┃    🛑 Control Commands        
┃    ⟡➣ .purge - Delete last N
┃    ⟡➣ .purge_all / .purgeall / .pga - Delete all
┃                              
┃    Navigate: .help7 (Prev) | .help9 (Next)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page8)

# PAGE 9 - VOICE CHAT MUSIC
@client.on(events.NewMessage(pattern=r"^\.help9$"))
async def help_page9(event):
    if not is_owner(event): return
    await delete_command_message(event)
    page9 = """
```╭━━━━⟬📖 VOICE CHAT MUSIC⟭━━━━╮
┃                              
┃    🎵 Music Commands         
┃    ⟡➣ .play [song/YT link] - Play
┃    ⟡➣ .skip - Skip current   
┃    ⟡➣ .queue - Show queue    
┃    ⟡➣ .end - End & leave     
┃    ⟡➣ .pause - Pause music   
┃    ⟡➣ .resume - Resume music 
┃                              
┃    Navigate: .help8 (Prev) | .help (Menu)
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯```
"""
    await event.reply(page9)
# QUICK HELP - For quick reference
@client.on(events.NewMessage(pattern=r"^\.quickhelp$"))
async def quick_help(event):
    if not is_owner(event): return
    
    quick = """
```⚡ **QUICK COMMANDS REFERENCE**

Most Used:
.spam <@user> <count> <msg> - Spam user
.raid <count> <msg> - Raid message
.broadcast_all <msg> - Broadcast everywhere
.delay <seconds> - Set delay
.stop - Stop all tasks

Roast:
.rb [@user] [count] - Roast boy
.rg [@user] [count] - Roast girl
.hra [@user] [count] - Hindi abuse roast

Auto-Raids:
.rr [@user] - Auto-reply raid
.fr [@user] - Auto-flirt raid
.rbr [@user] - Auto-roast boy raid

Info:
.ui [@user] - User info
.ping - Check status
.alive - Bot status

For full commands: .help (Main Menu)```
    """
    await event.edit(quick)
# ---------------------------
# FAKE WEB SERVER TO KEEP USERBOT RUNNING
async def handle(request):
    return web.Response(text="Userbot running", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")


# 🚀 START COMMAND
@client.on(events.NewMessage(pattern=r"^\.(start|stt)$"))
async def start_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    start_msg = await event.reply(
    "```🤖 𝐔𝐋𝐓𝐈𝐌𝐀𝐓𝐄 𝐍𝐄𝐗𝐔𝐒 𝐔𝐒𝐄𝐑𝐁𝐎𝐓 𝐀𝐂𝐓𝐈𝐕𝐀𝐓𝐄𝐃!\n"
    "━━━━━━━━━━━━━━━━\n"
    "⏰ 𝐂𝐔𝐑𝐑𝐄𝐍𝐓 𝐃𝐄𝐋𝐀𝐘: 6 seconds\n"
    "📌 𝐂𝐇𝐀𝐍𝐆𝐄 𝐃𝐄𝐋𝐀𝐘: .delay <seconds>\n"
    "🔧 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐋𝐈𝐒𝐓: .help\n"
    "━━━━━━━━━━━━━━━━\n"
    "🌟 Stay tuned for powerful automation!\n\n"
    "(𝐒𝐭𝐚𝐭𝐮𝐬: Online | Mode: Smooth)```"
)
    await asyncio.sleep(7)
    await delete_after_delay(start_msg)


# Start the client
async def main():
    global bot_start_time
    bot_start_time = datetime.now()
    print("Starting userbot...")
    await client.start()
    global OWNER_ID  # IMPORTANT: Global declare karein
    me = await client.get_me()
    OWNER_ID = me.id  # Yahan assign karein
    #fake web server
    await start_web_server()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} ({me.id})")
    print("Muted list:", muted)
    # run until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Stopped by user.")
