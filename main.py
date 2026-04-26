import os
import json
import threading
import asyncio
import aiohttp
import random
import time 
from aiohttp import web
from datetime import datetime
from telethon import events, functions, types
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.types import InputPhoto
from telethon.tl.types import MessageEntityMentionName

#fixed
asyncio.set_event_loop(asyncio.new_event_loop())

# ----------------- CONFIG -----------------
API_ID = 31376570
API_HASH = "6b869ab57239d9b73a0ac1964f03e9b7"
OWNER_ID =6740955542        
SESSION_STRING="1BVtsOMEBuzL0Ftj9daNVaOeLZZfXt6KYiahNVmEmlR0yEVLLUfWVW7pGm6WV5ES01hZTO-ZviK1gOB4AELs9HgOysxZ7hRviUDbB0Z3OgF7-ATbov-bXOqMPmwS7D2xGu1Ztb4TDH2gihLxd8OM90WHCVUrO_YbEVrChmGp5XvTr5mNPf8Jk4xVkhrXXETWMDG0o_Io3F8D-1FGEZuNWpjtswXVBtR94nt_RODJtA_KqgK1Vtp0kG85hFsoX6Am6zL_8pHoO4LPOPXXUa5iLaD7C7jdKjs2Z-63dwZBQ-iRsnLFO1amNnMiskTZ1oYj-Wuij9V0ZMDrmBPCSkwSilRo8GJpTBFU="
MUTED_FILE = "muted.json"
PORT = 10000  # port for web server (if needed)
# ------------------------------------------

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
from telethon.sessions import StringSession

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

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
        target_id, user_entity = await resolve_target(event)
        if not target_id or not user_entity:
            await event.reply("Use reply or provide @username / user_id to gmute.")
            return
        if target_id == OWNER_ID:
            await event.reply("You can't gmute yourself.")
            return
        if target_id in muted:
            await event.reply(f"{user_entity.first_name} is already globally muted.")
            return
        muted.add(int(target_id))
        save_muted(muted)
        display = user_entity.first_name or (getattr(user_entity, "username", "User"))
        await event.reply(f"{display} successfully pel dia gya h 👺")
    except Exception as ex:
        await event.reply(f"Error in .gmute: {ex}")
        # Command: .gunmute
@client.on(events.NewMessage(pattern=r'^\.gunmute(?:\s|$)', func=lambda e: True))
async def gunmute_handler(event):
    try:
        # only owner can use
        if event.sender_id != OWNER_ID:
            return
        target_id, user_entity = await resolve_target(event)
        if not target_id or not user_entity:
            await event.reply("Use reply or provide @username / user_id to gunmute.")
            return
        if int(target_id) not in muted:
            await event.reply(f"{user_entity.first_name} is not muted")
            return
        muted.discard(int(target_id))
        save_muted(muted)
        display = user_entity.first_name or (getattr(user_entity, "username", "User"))
        await event.reply(f"{display} chhod dia ladle 👺👺")
    except Exception as ex:
        await event.reply(f"Error in .gunmute: {ex}")

# Optional: .gmutedlist to show current list (owner only)
@client.on(events.NewMessage(pattern=r'^\.gmutedlist(?:\s|$)', func=lambda e: True))
async def gmuted_list(event):
    if event.sender_id != OWNER_ID:
        return
    if not muted:
        await event.reply("No one is globally muted.")
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
# Command: .all <message> - tag members one by one
@client.on(events.NewMessage(pattern=r'^\.all\s+(.+)$', func=lambda e: True))
async def tag_all_handler(event):
    global tag_task
    
    if event.sender_id != OWNER_ID:
        return
    
    if tag_task:
        await event.edit("**Tagging already in progress. Use .cancel to stop.**")
        await asyncio.sleep(0.6)
        await event.delete()
        return
    
    message_text = event.pattern_match.group(1)
    
    await event.edit("**Starting to tag members**")
    await asyncio.sleep(0.6)
    await event.delete()
    
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
                    await asyncio.sleep(0.7)  # Avoid flood
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
    
    if tag_task:
        tag_task.cancel()
        tag_task = None
        await event.edit("**Tagging cancelled.**")
        await asyncio.sleep(0.6)
        await event.delete()
    else:
        await event.edit("No tagging in progress.")
        await asyncio.sleep(0.6)
        await event.delete()

        # Global variable for spam task
spam_task = None

# Command: .spam <message> - auto spam message
@client.on(events.NewMessage(pattern=r'^\.spam\s+(.+)$', func=lambda e: True))
async def spam_handler(event):
    global spam_task
    
    if event.sender_id != OWNER_ID:
        return
    
    if spam_task:
        await event.reply("Spam already running. Use .stopspam to stop.")
        return
    
    message_text = event.pattern_match.group(1)
    
    await event.reply("🚀 Spam started... Use .stopspam to stop")
    
    # Start spam task
    spam_task = asyncio.create_task(auto_spam(event.chat_id, message_text))

async def auto_spam(chat_id, message_text):
    global spam_task
    try:
        while True:
            await client.send_message(chat_id, message_text)
            await asyncio.sleep(1)  # 1 second delay
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
    
    if spam_task:
        spam_task.cancel()
        spam_task = None
        await event.reply("🛑 Spam stopped.")
    else:
        await event.reply("❌ No spam running.")

        # Command: .purge - delete messages from replied message to current
@client.on(events.NewMessage(pattern=r'^\.purge(?:\s|$)', func=lambda e: True))
async def purge_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    if not event.is_reply:
        await event.reply("❌ Reply to a message to start purge from there.")
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
from telethon import events
import requests, json

@client.on(events.NewMessage(pattern=r'\.num (\d+)'))
async def number_info(event):
    num = event.pattern_match.group(1)
    api = f"https://number-to-information.vercel.app/fetch?key=NO-LOVE&num={num}"
    try:
        data = requests.get(api).json()
        await event.reply(f"📱 Number Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'\.vehicle (\S+)'))
async def vehicle_info(event):
    vehicle_no = event.pattern_match.group(1)
    api = f"https://vehicle-2-info.vercel.app/rose-x?vehicle_no={vehicle_no}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🚗 Vehicle Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'\.aadhar (\d{12})'))
async def aadhar_info(event):
    aadhaar = event.pattern_match.group(1)
    api = f"https://rose-x-tool.vercel.app/fetch?key=@Ros3_x&aadhaar={aadhaar}"
    try:
        data = requests.get(api).json()
        await event.reply(f"🪪 Aadhaar Info:\n```{json.dumps(data, indent=2)}```")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")
        # ------------------------------
# GOOGLE SEARCH CONFIG
# ------------------------------
GOOGLE_API_KEY = "AIzaSyBPnt16fUVxu78zWOdVmYhiByj-hooPL2U"           # yaha api key
CX_ID = "52a3d9bf39f3b4594"                      # tera CX ID

# ------------------------------
# SEARCH COMMAND
# ------------------------------
@client.on(events.NewMessage(pattern=r"\.search (.+)"))
async def search_google(event):
    query = event.pattern_match.group(1)

    await event.reply("🔎 Searching… for results wait…")

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
        await event.reply("😕 Koi result nahi mila.")
        return

    results = data["items"][:3]

    msg = f"🔍 **Search results for:** `{query}`\n\n"

    for item in results:
        title = item.get("title", "No Title")
        desc = item.get("snippet", "No description available")
        link = item.get("link", "")

        msg += f"🟢 **{title}**\n📄 {desc}\n🔗 {link}\n\n"

    image_url = None
    try:
        for item in results:
            if "pagemap" in item and "cse_image" in item["pagemap"]:
                image_url = item["pagemap"]["cse_image"][0]["src"]
                break
    except:
        image_url = None

    if image_url:
        await event.reply(msg)
    else:
        await event.reply(msg)
        
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
 
OWNER_ID = 6740955542   # ← Yaha aapka owner ID set hai

@client.on(events.NewMessage(pattern='.kill'))
async def kill_command(event):
    """Kill command handler - Owner only"""
    
    # ❌ Non-owner → silent
    if event.sender_id != OWNER_ID:
        return

    # ❌ Not replying to anyone → friendly reminder
    if not event.is_reply:
        await event.reply("❗Target not locked. Reply to someone first!")
        return
    
    try:
        replied_msg = await event.get_reply_message()
        user = await client.get_entity(replied_msg.sender_id)
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Random death message
        death_message = random.choice(death_messages)
        formatted_message = death_message.format(username=username)
        
        # Dramatic effect
        message = await event.reply("🔫 Target Locking...")
        await asyncio.sleep(1.8)
        
        await message.edit("💥 Missile Launching...")
        await asyncio.sleep(1.8)
        
        await message.edit("🎯 Target Hit!")
        await asyncio.sleep(1)

        await message.edit(formatted_message)

    except:
        # Custom error message instead of traceback
        await event.reply("⚠️ Operation Failed! Target Escaped 😶‍🌫️")


@client.on(events.NewMessage(pattern='.kidnap'))
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
        
# SANGMATA BOTS FOR NAME HISTORY
SANGMATA_BOTS = ["@SangMata_BOT", "@SangMata_beta_bot"]

# ------------- SETTINGS -----------------
MAX_PER_RUN = 10000000000000000
DELAY_SECONDS = 6  # 🔥 DEFAULT DELAY 6 SECONDS FOR ALL COMMANDS
TAG_DELAY = 6      # 🔥 TAG COMMANDS DELAY

# ----------- MESSAGES DATA --------------

# 🔥 BOYS ROAST LINES
boys_roast = [
"**., TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**., TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**. TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**. TU EK CHALTA PHIRTA BUG HAI.** 🐛",
    "**TU HERO NAHI, SIRF ERROR 404 KA EXAMPLE HAI.** ❌",
"**TERE JOKES SE CALCULATOR BHI CONFUSE HO JAYE.** 🧮",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**. TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU EK BROKEN LINK HO.** 🔗",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"., TERI SHAKAL DEKHKE LAGTA HAI BHAGWAN NE BHI TRIAL VERSION MEIN BANAYA THA. 🤡"
"TERE JAISE LOGON KE LIYE HI 'BLOCK' BUTTON BANA HAI. 🚫"
"., TU ITNA FAKE HAI KI TERA SNAPCHAT FILTER BHI EMBARRASS HO JAYE. 🎭"
"TERI AWAAZ SUNKE LAGTA HAI — MIC NE BHI MUTE KARNA SEEKH LIYA. 🎤🔇"
"., TU EK CHALTA PHIRTA 'TERMS AND CONDITIONS' HAI — KOI PADHTA NAHI, SAB SKIP KAR DETE HAIN. 📄"
"TERI PHOTO DEKHKE FACEBOOK NE 'LOW QUALITY CONTENT' KA TAG DIYA. 📸"
"., TERA DIMAAG HAI YA PENDING UPDATE KA NOTIFICATION? ⏳"
"TU HERO NAHI, SIRF EK 'SKIP INTRO' BUTTON KA EXAMPLE HAI. ⏭️"
"TERI BAATEIN SUNKE LAGTA HAI — YOUTUBE KI UNWANTED AD CHAL RAHI HAI. 📺"
"., TERA EXISTENCE EK '404 NOT FOUND' PAGE JAISA HAI. ❌"
"TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE RESTORE KARNE SE MUKAR GAYA. 🗑️"
"., TERA CONFIDENCE AUR TERA TALENT — DONO ALAG ZIP CODES MEIN REHTE HAIN. 🏘️"
"TERI SHAKAL DEKHKE LAGTA HAI — NATURE NE BHI GALTI KAR DI. 🌍"
"., TU ITNA SLOW HAI KI GHONGHE NE TUJHE RACE MEIN HARAYA. 🐌"
"TERI SUCCESS AUR TERI REALITY — DONO MEIN KABHI FLIGHT CANCELLATION HO JATI HAI. ✈️"
"., TU EK 'LOADING…' JAISA HAI — KABHI COMPLETE NAHI HOTA. 🔄"
"TERI PERSONALITY CHECK KIYA — 'FILE CORRUPTED' ERROR AAYA. 🖥️"
"., TU ITNA IRRELEVANT HAI KI GOOGLE MAPS PE BHI 'NO DATA' DIKHTA HAI. 🗺️"
"TERI EXISTENCE EK TYPO HAI — GALAT JAGAH, GALAT TIME, GALAT PERSONALITY. ⌨️"
"., TU ITNA 'UNIQUE' HAI KI AVERAGE BHI TUJHE CHODKAR BHAG GAYA. 🏃"
"TERI BAATON MEIN DUM NAHI, SIRF BACKGROUND NOISE HAI. 🔊"
"., TU ITNA DESPERATE HAI KI LIKES KE LIYE KHUD KO MEME BANA DIYA. 🤡❤️"
"TERI PHOTO DEKHKE INSTAGRAM NE 'REPORT' OPTION RECOMMEND KIYA. 📱🚩"
"., TERA FUTURE PLAN AUR TERA PAST DONO SAME HAIN — DARK AUR UNCLEAR. 🌑"
"TU ITNA OVERCONFIDENT HAI KI FAILURE BHI TUJHSE EMBARRASSED HAI. 📉😳"
"TERI LIFE EK FLOP MOVIE KI TARAH HAI — INTERVAL KE BAAD KOI AATA HI NAHI. 🎬"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'BEFORE USE' WALA EXAMPLE HAI. 🧼"
"., TU ITNA SELF-OBSESSED HAI KI KHUD SE SELFI LETE WAQT BHI FILTER LAGATA HAI. 🤳"
"TERI BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN — KOI PADHTA NAHI, SAB HATATE HAIN. 🔔"
"., TU EK CHALTA PHIRTA BUFFERING SYMBOL HAI. ⏳"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'AFTER EFFECTS' KA GALAT EXAMPLE HAI. 🎨"
"., TERA EGO AUR TERA IQ — DONO ULTRA PRO MAX LEVEL PE HAIN PAR DIRECTION GALAT HAI. 🧠"
"TERI SUCCESS KA GRAPH DEKHA TOH LAGA — YEH TOH 'FALLING' KA NEW RECORD HAI. 📉"
"., TU ITNA 'MAIN CHARACTER' HAI KI BACKGROUND MUSIC BHI TUJHE IGNORE KARTA HAI. 🎵"
"TERI PERSONALITY AUR TERI REALITY — DONO MEIN 5G SPEED KA DIFFERENCE HAI. 📶"
"., TERA EXISTENCE EK 'WARNING LABEL' DESERVE KARTA HAI — 'USE AT YOUR OWN RISK'. ⚠️"
"TERI AWAAZ SUNKE SIRI BHI 'I DON'T UNDERSTAND' BOLTI HAI. 📱🤷"
"., TU ITNA FAKE HAI KI CHATGPT BHI TERA REPLY NAHI KARTA. 🤖"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'PHOTOSHOP' KA 'BEFORE' WALA PART HAI. 🖼️"
"., TU EK CHALTA PHIRTA 'TERMS AND CONDITIONS' HAI — IMPORTANT NAHI, IRRITATING ZAROOR. 📄"
"TERI BAATON MEIN WEIGHT NAHI, SIRF LENGTH HAI. 📏"
"., TERA CONFIDENCE AUR TERA SKILL — DONO ALAG GENERATION KE HAIN. 📱"
"TERI PHOTO DEKHKE CAMERA NE 'LOW LIGHT WARNING' DI. 📸⚠️"
"., TU ITNA SLOW HAI KI DIAL-UP INTERNET BHI TUJHE FAST LAGTA HAI. 🐢"
"TERI EXISTENCE EK 'SPAM FOLDER' JAISI HAI — KABHI OPEN NAHI HOTI. 📂"
"., TU HERO NAHI, SIRF EK 'ERROR 502' KA EXAMPLE HAI. 🌐"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'FACEBOOK' KA OLD PROFILE PICTURE HAI. 📘"
"., TERA DIMAAG HAI YA 'STORAGE FULL' KA NOTIFICATION? 📱"
"TERI BAATEIN SUNKE LAGTA HAI — TU 'YOUTUBE' KA 'SKIP AD' WALA PART HAI. ⏭️"
"., TU ITNA 'POSITIVE' HAI KI TERI POSITIVITY BHI NEGATIVE LAGTI HAI. 🧘"
"TERI SUCCESS AUR TERI LIFE — DONO MEIN 'CONNECTION LOST' HO JATA HAI. 📶"
"., TU EK CHALTA PHIRTA 'BUG' HAI — FIX HONA CHAHIYE. 🐛"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'FACETUNE' KA 'BEFORE' WALA VERSION HAI. 🎨"
"., TERA PRESENCE DEKHKE LOG SOCHTE HAIN — 'YEH BANDA KYUN HAI YAHAN'? 🧐"
"TERI BAATON MEIN DUM NAHI, SIRF 'AIR' HAI. 💨"
"., TU ITNA IRRELEVANT HAI KI TERA BIRTH CERTIFICATE BHI 'DRAFT' MODE MEIN HAI. 📄"
"TERI PHOTO DEKHKE LAGTA HAI — TU 'FILTER' KA 'AFTER' WALA PART BHUL GAYA. 📸"
"., TERA FUTURE AUR TERA PRESENT — DONO MEIN 'LOADING' CHAL RAHA HAI. ⏳"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'GOOGLE IMAGES' KA 'LOW RES' WALA PART HAI. 🖼️"
"., TU EK CHALTA PHIRTA 'GLITCH' HAI — SYSTEM SE BAHR NIKAL. 🖥️"
"TERI AWAAZ SUNKE LAGTA HAI — TU 'AUDIO' KA 'MUTED' VERSION HAI. 🔇"
"., TERA EXISTENCE EK 'JOKE' HAI — PAR MazaK KISKO AATA HAI? 🃏"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'NATURE' KA 'REJECTED' VERSION HAI. 🌿"
"., TU ITNA 'COOL' BANNA CHAHTA HAI JAISE 'FREEZE' BUTTON DAB GAYA HO. ❄️"
"TERI BAATEIN SUNKE LAGTA HAI — TU 'GOOGLE TRANSLATE' KA 'WRONG' VERSION HAI. 🌐"
"., TERA CONFIDENCE AUR TERA REALITY — DONO MEIN '5G' KA DIFFERENCE HAI. 📶"
"TERI PHOTO DEKHKE LAGTA HAI — TU 'PHOTOSHOOT' KA 'BLOOPER' WALA PART HAI. 🎬"
"., TU EK CHALTA PHIRTA 'POP-UP AD' HAI — SAB BAND KAR DETE HAIN. 🚫"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'MIRROR' KA 'CRACKED' VERSION HAI. 🪞"
"., TERA DIMAAG HAI YA 'PENDING INSTALLATION'? 📲"
"TERI EXISTENCE EK 'RECYCLE BIN' KA 'PERMANENT' WALA PART HAI. 🗑️"
"., TU ITNA 'UNIQUE' HAI KI 'BEING AVERAGE' BHI TUJHE 'EXCLUSIVE' LAGTA HAI. 🦄"
"TERI BAATEIN SUNKE LAGTA HAI — TU 'SIRI' KA 'GLITCH' WALA VERSION HAI. 🍎"
"., TERA PRESENCE DEKHKE LOG 'DO NOT DISTURB' MODE ON KAR DETE HAIN. 📵"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'ADOBE' KA 'TRIAL' VERSION HAI. 🎨"
"., TERA CAREER GRAPH AUR TERI HEIGHT — DONO SAME HAIN — BAS BARABAR NAHI BADHE. 📉"
"TERI PHOTO DEKHKE LAGTA HAI — TU 'INSTAGRAM' KA 'ARCHIVED' WALA PART HAI. 📸"
"., TU EK CHALTA PHIRTA 'ERROR 404' HAI — MILA HI NAHI. 🔍"
"TERI AWAAZ SUNKE LAGTA HAI — TU 'AUDIO' KA 'CORRUPTED' FILE HAI. 🎵"
"., TERA EXISTENCE EK 'TRIAL VERSION' HAI — EXPIRE KAB HO RAHA HAI? ⏳"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'PAINT' MEIN BANAYA GAYA '3D' MODEL HAI. 🎨"
"., TERA CONFIDENCE AUR TERA SKILL — DONO MEIN 'LATENCY' HAI. 🎮"
"TERI BAATEIN SUNKE LAGTA HAI — TU 'CHATGPT' KA 'BETA' VERSION HAI. 🤖"
"., TU ITNA 'MAIN CHARACTER' HAI KI LOG TUJHE 'BACKGROUND' MEIN BHI IGNORE KARTE HAIN. 👥"
"TERI PHOTO DEKHKE LAGTA HAI — TU 'SNAPCHAT' KA 'FILTER' BHUL GAYA. 👻"
"., TERA DIMAAG HAI YA 'LOW BATTERY' KA WARNING? 🔋"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'ZOOM' KA 'BLUR BACKGROUND' WALA PART HAI. 🖥️"
"., TU EK CHALTA PHIRTA 'SPAM' HAI — BLOCK HONE KA INTZAAR KAR RAHA. 🚫"
"TERI EXISTENCE EK 'NOTIFICATION' JAISI HAI — KOI OPEN NAHI KARTA. 🔔"
"., TU ITNA 'FAKE' HAI KI 'REALITY' BHI TUJHSE DUR BHAGTI HAI. 🏃"
"TERI AWAAZ SUNKE LAGTA HAI — TU 'YOUTUBE' KA 'MUTED' WALA AD HAI. 📺"
"., TERA PRESENCE DEKHKE LOG 'SKIP' BUTTON DHUNDHTE HAIN. ⏭️"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'PHOTOSHOP' KA 'LAYER' BHUL GAYA. 🖼️"
"., TERA CAREER AUR TERI LIFE — DONO 'AIRPLANE MODE' MEIN HAIN. ✈️"
"TERI BAATEIN SUNKE LAGTA HAI — TU 'GOOGLE' KA 'NO RESULTS' WALA PAGE HAI. 🔍"
"., TU EK CHALTA PHIRTA 'BUFFERING' HAI — COMPLETE KAB HOGA? ⏳"
"TERI PHOTO DEKHKE LAGTA HAI — TU 'CAMERA' KA 'LENS CAP' BHUL GAYA. 📸"
"., TERA CONFIDENCE AUR TERI REALITY — DONO 'OFFLINE' HAIN. 📴"
"TERI SHAKAL DEKHKE LAGTA HAI — TU 'BHAGWAN' KA 'MISTAKE' WALA PART HAI. 😇"
"., TU HERO NAHI, SIRF EK 'CAPTCHA' HAI — HAR KOI TUJHE 'SKIP' KARTA HAI. 🤖"
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU EK OFFLINE FILE JAISA HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MEMBER HO WHATSAPP GROUP KA.** 🔇",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LIFE KA BETA VERSION HAI.** 🧪",
"**TU EK CHALTA PHIRTA CAPTCHA HAI.** 🔢",
"**TERE BAATEIN BACKGROUND NOISE JAISI HAI.** 🎧",
"**TU CHALTA PHIRTA DEMO ACCOUNT HAI.** 📝",
"**. TU WALKING ERROR MESSAGE HO.** ❌",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE LOGIC KE AAGE CALCULATOR BHI FAIL HO JAYE.** 🧮",
"**TU EK CANCELLED DOWNLOAD KA EXAMPLE HAI.** ⬇️",
"**. TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU LIFE KA GLITCH HO.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎬",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HO – SABKO SKIP KARNA HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HO – SAB IGNORE KARTE HAI.** 📅",
"**. TU DEMO ACCOUNT KA HUMAN VERSION HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HO.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HO JO HAMESHA CRASH HOTI HAI.** 📱",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**. TU HERO NAHI, SIRF DEMO VIDEO KA CLIP HAI.** 🎞️",
"**TU EK CRASHED APP HAI – KABHI OPEN NAHI HOTA.** 📱",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**. TU LIFE KA BUG REPORT HAI.** 🐛",
"**TU EK FORWARDED MESSAGE JAISA HAI – IGNORE KARTA SABKO.** 📩",
"**TERE HAIRSTYLE SE BARBER BHI SHOCK HO JAYE.** 💇‍♂️",
"**TU CHALTA PHIRTA CAPTCHA HAI – SABKO CONFUSE KARTA.** 🔢",
"**. TU LOW BATTERY ALERT HAI.** 🔋",
"**TU EK CANCELLED CALL HO – KOI NAHI SUNTA.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN BHI PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA POSTER HAI.** 🖼️",
"**. TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO ACCOUNT HAI – INCOMPLETE AUR USELESS.** 📝",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU WALKING TYPO HAI.** ✏️",
"**. TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF TEASER VIDEO KA CLIP HAI.** 🎬",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**. TU OTT TRIAL SHOW HAI – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU EK WALKING ERROR MESSAGE HAI.** ❌",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HAI – SAB IGNORE KARTE HAIN.** 📅",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HAI JO HAMESHA CRASH HOTI HAI.** 📱",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**. TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TU EK WALKING TYPO HAI.** ✏️",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HAI – INCOMPLETE AUR USELESS.** 🎥",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU LOW BATTERY ALERT HAI.** 🔋",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – KOI NAHI DEKHTA.** 📄",
"**TERE UPDATES HAMESHA PENDING HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAIN.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**. TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🖱️",
"**TERE BAAT KARTE HI SABKO LAGTA HAI SPAM CALL AAYI.** 📞",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
    "**., TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**., TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**. TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**. TU CHAI KI PYALI KI TARAH HAI – GARAM HAI PAR KISI KO PASAND NAHI!** ☕",
    "**TERE JAISE LOGON KE LIYE HI BLOCK BUTTON BANA HAI!** 🚫",
    "**. TU INSTAGRAM REELS KI TARAH HAI – 15 SECOND MEIN BORING!** ⏱️",
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
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE . DEDIYA",
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
    "**.NS KI AULAAD!** 🐃",
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
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE . DEDIYA",
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
"**., TU APNE AAPKO HERO SAMAJHTA HAI!** 🤡",
    "**TERE JAISE LOGON KO DEKHKAR HI MUTE BUTTON KA INVENTION HUA THA!** 🔇",
    "**., TU ITNA USELESS HAI KI RECYCLE BIN BHI TUJHE ACCEPT NAHI KAREGA!** 🗑️",
    "**TU APNE GHAR KA WiFi PASSWORD HAI – SABKO YAAD HAI PAR KISI KAAM KA NAHI!** 📶",
    "**. TU TOH WALKING CRINGE CONTENT HAI!** 😬",
    "**TERI PHOTO DEKHKAR CAMERA BHI APNA LENS BAND KAR LETA HAI!** 📸",
    "**. TU EK CHALTA PHIRTA BUG HAI.** 🐛",
    "**TU HERO NAHI, SIRF ERROR 404 KA EXAMPLE HAI.** ❌",
"**TERE JOKES SE CALCULATOR BHI CONFUSE HO JAYE.** 🧮",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**. TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU EK BROKEN LINK HO.** 🔗",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU EK OFFLINE FILE JAISA HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MEMBER HO WHATSAPP GROUP KA.** 🔇",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LIFE KA BETA VERSION HAI.** 🧪",
"**TU EK CHALTA PHIRTA CAPTCHA HAI.** 🔢",
"**TERE BAATEIN BACKGROUND NOISE JAISI HAI.** 🎧",
"**TU CHALTA PHIRTA DEMO ACCOUNT HAI.** 📝",
"**. TU WALKING ERROR MESSAGE HO.** ❌",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE LOGIC KE AAGE CALCULATOR BHI FAIL HO JAYE.** 🧮",
"**TU EK CANCELLED DOWNLOAD KA EXAMPLE HAI.** ⬇️",
"**. TU BUFFERING KA SYMBOL HAI.** ⏳",
"**TU LIFE KA GLITCH HO.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎬",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HO – SABKO SKIP KARNA HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HO – SAB IGNORE KARTE HAI.** 📅",
"**. TU DEMO ACCOUNT KA HUMAN VERSION HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HO.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC JAISA HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HO JO HAMESHA CRASH HOTI HAI.** 📱",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**. TU HERO NAHI, SIRF DEMO VIDEO KA CLIP HAI.** 🎞️",
"**TU EK CRASHED APP HAI – KABHI OPEN NAHI HOTA.** 📱",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**. TU LIFE KA BUG REPORT HAI.** 🐛",
"**TU EK FORWARDED MESSAGE JAISA HAI – IGNORE KARTA SABKO.** 📩",
"**TERE HAIRSTYLE SE BARBER BHI SHOCK HO JAYE.** 💇‍♂️",
"**TU CHALTA PHIRTA CAPTCHA HAI – SABKO CONFUSE KARTA.** 🔢",
"**. TU LOW BATTERY ALERT HAI.** 🔋",
"**TU EK CANCELLED CALL HO – KOI NAHI SUNTA.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN BHI PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA POSTER HAI.** 🖼️",
"**. TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO ACCOUNT HAI – INCOMPLETE AUR USELESS.** 📝",
"**TERE CONFIDENCE KI SPEED 2G INTERNET SE BHI SLOW HAI.** 📉",
"**TU WALKING TYPO HAI.** ✏️",
"**. TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF TEASER VIDEO KA CLIP HAI.** 🎬",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**. TU OTT TRIAL SHOW HAI – KOI NAHI DEKHTA.** 📺",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – USELESS.** 📄",
"**TERE UPDATES HAMESHA PENDING REHTE HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU EK WALKING ERROR MESSAGE HAI.** ❌",
"**TERE HAIRSTYLE SE BARBER BHI CONFUSE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU EK PLAYLIST SKIP BUTTON HAI.** ⏭️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU WIFI KA WEAK SIGNAL HAI.** 📶",
"**TU HERO NAHI, SIRF TEASER KA CLIP HAI.** 🎞️",
"**TERE UPDATES HAMESHA FAILED HO JATE HAIN.** ⚠️",
"**TU EK CALENDAR REMINDER HAI – SAB IGNORE KARTE HAIN.** 📅",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAI.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU EK APP HAI JO HAMESHA CRASH HOTI HAI.** 📱",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TERE HAIRSTYLE KA PATCH KABHI RELEASE NAHI HUA.** 🛠️",
"**TU CHALTA PHIRTA LOW BATTERY WARNING HAI.** 🔋",
"**. TU NOTIFICATIONS KA SPAM FOLDER HAI.** 📂",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU EK CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TERE HAIRSTYLE DEKHKAR BARBER BHI RETIRE HO JAYE.** 💇‍♂️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAI.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAI.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**. TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TU EK WALKING TYPO HAI.** ✏️",
"**. TU FREE TRIAL KA EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HAI – INCOMPLETE AUR USELESS.** 🎥",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**. TU LOW BATTERY ALERT HAI.** 🔋",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**TU EK MUTED MIC HAI.** 🎙️",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU EK OFFLINE FILE HAI – KOI NAHI DEKHTA.** 📄",
"**TERE UPDATES HAMESHA PENDING HAIN.** ⏳",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU EK FORWARDED WHATSAPP MESSAGE HAI.** 📲",
"**TERE JOKES DAD JOKES SE BHI WEAK HAIN.** 😂",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🛑",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU EK CHALTA PHIRTA WIFI ERROR HAI.** 📶",
"**. TU LIFE KA PERMANENT BUG HAI.** 🐛",
"**TU HERO NAHI, SIRF GLITCH KA EXAMPLE HAI.** 🖥️",
"**TERE JOKES SE EVEN AI BHI CONFUSE HO JAYE.** 🤖",
"**TU CHALTA PHIRTA SPAM CALL HAI.** 📞",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU LIFE KA GLITCH HAI.** 🖥️",
"**TU HERO NAHI, SIRF BETA VERSION KA POSTER HAI.** 🖼️",
"**. TU TRIAL VERSION KA HUMAN FORM HAI.** 🧪",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU EK LOW BATTERY WARNING HAI.** 🔋",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP AD HAI.** 🖱️",
"**TERE BAAT KARTE HI SABKO LAGTA HAI SPAM CALL AAYI.** 📞",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO ACCOUNT KA HUMAN FORM HAI.** 📝",
"**TU WALKING ERROR MESSAGE HAI.** ❌",
"**TU HERO NAHI, SIRF BETA VERSION KA EXAMPLE HAI.** 🧪",
"**. TU WIFI SIGNAL KA WEAK VERSION HAI.** 📶",
"**TU CHALTA PHIRTA GLITCH HAI.** 🖥️",
"**TERE IDEAS RECYCLE BIN SE BHI BEKAAR HAIN.** 🗑️",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU LOW BATTERY WARNING HAI.** 🔋",
"**TU OTT TRIAL SHOW HO – KOI NAHI DEKHTA.** 📺",
"**TERE JOKES MEMES SE BHI WEAK HAIN.** 😹",
"**TU CHALTA PHIRTA BUG REPORT HAI.** 🐛",
"**. TU WIFI SIGNAL JAISA HAI – KABHI STRONG KABHI WEAK.** 📶",
"**TU LIFE KA PENDING UPDATE HAI.** ⏳",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FORWARDING MESSAGE KA IGNORED VERSION HAI.** 📩",
"**TU EK CANCELLED CALL KA RINGTONE HAI.** 📞",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**. TU DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAIN.** 🛑",
"**TU EK CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**. TU LIFE KA BUG HAI – PATCH NAHI HUA.** 🐛",
"**TU HERO NAHI, SIRF BETA TRAILER KA CLIP HAI.** 🎞️",
"**TERE IDEAS SABKO CONFUSE KARTE HAIN.** 🤯",
"**TU CHALTA PHIRTA CRASH REPORT HAI.** ⚠️",
"**. TU WIFI ERROR HAI – SIGNAL NAHI MILTA.** 📶",
"**TU EK DEMO VIDEO HO – SAB IGNORE KARTE HAI.** 🎥",
"**TERE JOKES MEMES KE AAGE FAIL HO JATE HAIN.** 😹",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU FREE TRIAL EXPIRED VERSION HAI.** ⏳",
"**TU CHALTA PHIRTA POP-UP HAI.** 🖱️",
"**TERE BAATEIN NOTIFICATIONS JAISI ANNOYING HAIN.** 🔔",
"**TU HERO NAHI, SIRF TRAILER KA CLIP HAI.** 🎞️",
"**TERE EXISTENCE SE LOADING SCREEN PRODUCTIVE LAGTI HAI.** 💻",
"**TU HERO NAHI, SIRF TRAILER KA TEASER HAI.** 🎬",
"**. TU SPAM FOLDER KA PERMANENT RESIDENT HAI.** 📂",
"**TU EK DEMO VIDEO HO – INCOMPLETE AUR USELESS.** 🎥",
"**TERE CONFIDENCE KI SPEED DIAL-UP INTERNET SE BHI SLOW HAI.** 📉",
"**TU CHALTA PHIRTA TYPO HAI.** ✏️",
"**. TU WALKING AD HAI – SAB BLOCK KARTE HAI.** 🛑",
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
    "NABE RANDIKE BACHHE AUKAT NHI HETO APNI RANDI MAAKO LEKE AAYA MATH KAR HAHAHAHA�;KIDZ MADARCHOD TERI MAAKO CHOD CHODKE TERR LIYE . DEDIYA",
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
    "**🖕 .NS KI AULAAD! 🖕😂**",
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
        await event.reply("💤 **THIS USER IS CURRENTLY OFFLINE**\n\n📵 _Last seen: Recently_\n⏰ _Status: Not available_")

# --------- COMMAND HANDLERS -------------

# ⚙️ DELAY CHANGE COMMAND
@client.on(events.NewMessage(pattern=r"^\.(delay|dly)\b"))
async def delay_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    parts = event.raw_text.split()
    
    # Declare global variables FIRST
    global DELAY_SECONDS, TAG_DELAY
    
    if len(parts) < 2 or not parts[1].isdigit():
        status_msg = await event.reply(f"⏰ **Current Delay:** {DELAY_SECONDS} seconds\n\nUse `.delay <seconds>` to change delay")
        await delete_after_delay(status_msg)
        return
    
    new_delay = int(parts[1])
    DELAY_SECONDS = new_delay
    TAG_DELAY = new_delay
    
    status_msg = await event.reply(f"✅ **Delay Updated!**\n\n⏰ New Delay: {DELAY_SECONDS} seconds\n\nAll commands will now use {DELAY_SECONDS} seconds delay")
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
✅ **HACKING COMPLETE!** ✅

👤 **Target:** {mention}
🆔 **User ID:** `{target_user.id}`
📱 **Device:** iPhone 14 Pro
📍 **Location:** Delhi, India
📧 **Email:** {target_user.first_name.lower()}123@gmail.com
📞 **Phone:** +91 XXXXXX{random.randint(1000,9999)}
💳 **Bank:** SBI Account **XXXX{random.randint(1000,9999)}**
📸 **Photos:** {random.randint(50,200)} private photos found
📱 **Last Login:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **WARNING:** All data has been extracted and stored securely!
🔒 **Firewall Status:** BREACHED
📡 **Connection:** ENCRYPTED

💀 **SYSTEM COMPROMISED!** 💀
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
✅ **BROADCAST COMPLETE!**

📱 **DMs:** ✓ {sent_dm} | ✗ {failed_dm}
👥 **Groups:** ✓ {sent_grp} | ✗ {failed_grp}  
📢 **Channels:** ✓ {sent_chn} | ✗ {failed_chn}
────────────────
📊 **Total:** ✓ {total_sent} | ✗ {total_failed}
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
    status_msg = await event.reply(f"🔥 Roast started! {count} messages"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"🔥 Roast started! {count} messages"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"🔥 Abuse roast started! {count} messages"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"💖 Flirt started! {count} messages"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"🔥 लड़का रोस्ट शुरू! {count} मैसेज"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"🔥 लड़की रोस्ट शुरू! {count} मैसेज"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"🔥 गाली रोस्ट शुरू! {count} मैसेज"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"💖 फ्लर्ट शुरू! {count} मैसेज"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply("💣 Raid100 started!"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"💣 Raid started! {count} messages"); await delete_after_delay(status_msg)

# 🔁 AUTO-REPLY RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(reply_raid|rr)\b"))
async def reply_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    reply_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"🔁 Reply raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"📜 Raid shayari activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"👧 Roast girl raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 🗣️ ROAST ABUSE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(roast_abuse_raid|rar)\b"))
async def roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    roast_abuse_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"🗣️ Roast abuse raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💖 FLIRT GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(flirt_girl_raid|fgr)\b"))
async def flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    flirt_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💖 Flirt girl raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"👧 Hindi roast girl raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 🗣️ HINDI ROAST ABUSE RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_roast_abuse_raid|hrar)\b"))
async def hindi_roast_abuse_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_roast_abuse_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"🗣️ Hindi roast abuse raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💖 HINDI FLIRT GIRL RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(hindi_flirt_girl_raid|hfgr)\b"))
async def hindi_flirt_girl_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    hindi_flirt_girl_raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💖 Hindi flirt girl raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💣 RAID100 RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid100_raid|r100r)\b"))
async def raid100_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    raid100_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💣 Raid100 raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

# 💣 RAID RAID COMMANDS - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(raid_raid|rdr)\b"))
async def raid_raid_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user: return
    raid_targets[event.chat_id] = target_user.id
    status_msg = await event.reply(f"💣 Raid raid activated on {target_user.first_name}!"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"💖 Mass love started! {count} messages"); await delete_after_delay(status_msg)

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
    status_msg = await event.reply(f"📜 Shayari raid started! {count} messages"); await delete_after_delay(status_msg)

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
        await cloning_msg.edit(f"✅ **Profile Cloned!**\n\n👤 Now: **{target_user.first_name}**\n📝 Bio: {cloned_bio if cloned_bio else 'No bio'}\n🖼️ PFP: ✅ Cloned\n\nUse `.unclone` to restore.")
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

# 📊 CHECKNAME COMMAND - LONG + SHORT
@client.on(events.NewMessage(pattern=r"^\.(checkname|cn)\b"))
async def checkname_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    
    target_user = await get_target_user(event, event.raw_text.split())
    if not target_user:
        status_msg = await event.reply("❌ Reply to user or use @username/userid")
        await delete_after_delay(status_msg)
        return
    
    try:
        user_id = target_user.id
        current_name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip()
        
        processing_msg = await event.reply(f"🔍 **Fetching name history for {current_name}...**\n\n📡 Connecting to SangMata bots...")
        
        for bot_username in SANGMATA_BOTS:
            try:
                await client.send_message(bot_username, f"/info {user_id}")
                await asyncio.sleep(2)
            except: pass
        
        await processing_msg.edit(f"✅ **Requests sent to SangMata bots!**\n\n👤 **Target:** {current_name}\n🆔 **User ID:** {user_id}\n\n📨 Check your chats with:\n• @SangMata_BOT\n• @SangMata_beta_bot\n\nThey will send the complete name history directly.")
        
    except Exception as e:
        error_msg = await event.reply(f"❌ Error fetching name history: {str(e)}")
        await delete_after_delay(error_msg)

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
👤 **User Info**

**Name:** {target_user.first_name} {target_user.last_name or ''}
**Username:** @{target_user.username or 'N/A'}
**User ID:** `{target_user.id}`
**Bot:** {'✅ Yes' if target_user.bot else '❌ No'}
**DC ID:** {target_user.photo.dc_id if target_user.photo else 'N/A'}

**Chat ID:** `{event.chat_id}`
    """
    info_msg = await event.reply(user_info); await delete_after_delay(info_msg)

@client.on(events.NewMessage(pattern=r"^\.(ping|pg)$"))
async def ping_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    start = time.time(); msg = await event.reply("🏓 Pong!"); end = time.time()
    await msg.edit(f"🏓 **Pong!**\n⏱️ {(end-start)*1000:.2f}ms"); await delete_after_delay(msg)

@client.on(events.NewMessage(pattern=r"^\.(alive|al)$"))
async def alive_handler(event):
    if not is_owner(event): return
    await delete_command_message(event)
    alive_msg = await event.reply("🤖 **BOT IS ALIVE AND RUNNING!**\n\n⚡️ Status: Online\n🔥 Features: Working\n💖 Owner: Active"); await delete_after_delay(alive_msg)

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
0
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

@client.on(events.NewMessage(pattern=r"^\.(spam|sp)\b"))
async def spam_handler(event):
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
    status_msg = await event.reply(f"💣 Spam started! {count} messages"); await delete_after_delay(status_msg)

    # ---------------------------
# KEEP ALIVE FUNCTION
# ---------------------------
async def keep_alive():
    while True:
        try:
            await client.send_message("me", "🟢 Alive")  # self-ping
        except Exception as e:
            print("KeepAlive Error:", e)
        await asyncio.sleep(600)  # 10 minutes


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
@client.on(events.NewMessage(pattern=r"^\.(help|hp)$"))
async def help_handler(event):
    if not is_owner(event): return
    help_msg = """
🤖 **ULTIMATE BOT COMMANDS** 🤖

⚙️ **Settings Commands**
`.delay` / `.dly` <seconds> - Change delay between messages (Current: 6s)

🎬 **Animation Commands**
`.hack` [@user] - Dangerous hacking animation (~120 sec)
`.middlefinger` / `.mf` [@user] - Middle finger abuse animation (~120 sec)

📢 **Broadcast Commands**
`.broadcast_dm` / `.bdm` <msg> - Send to all DMs
`.broadcast_group` / `.bgrp` <msg> - Send to all groups  
`.broadcast_channel` / `.bchn` <msg> - Send to all channels
`.broadcast_all` / `.ball` <msg> - Send to DMs + Groups + Channels
`.broadcast_current` / `.bcur` <msg> - Send to current chat only

🔥 **Roast Commands (English)**
`.roast_boy` / `.rb` [@user] [count] - Boys roast
`.roast_girl` / `.rg` [@user] [count] - Girls roast  
`.roast_abuse` / `.ra` [@user] [count] - Abuse roast
`.flirt_girl` / `.fg` [@user] [count] - Flirt lines

🔥 **Roast Commands (Hindi)**
`.hindi_roast_boy` / `.hrb` [@user] [count] - लड़का रोस्ट
`.hindi_roast_girl` / `.hrg` [@user] [count] - लड़की रोस्ट
`.hindi_roast_abuse` / `.hra` [@user] [count] - गाली रोस्ट
`.hindi_flirt_girl` / `.hfg` [@user] [count] - फ्लर्ट लाइन्स

💣 **Raid Commands**
`.raid100` / `.r100` <msg> - 100x message
`.raid` / `.rd` <count> <msg> - Custom count

🔁 **Auto-Reply Raids**
`.reply_raid` / `.rr` [@user] - Auto-reply abuse
`.flirt_raid` / `.fr` [@user] - Auto-flirt
`.love_raid` / `.lr` [@user] - Auto-love lines
`.quote_raid` / `.qr` [@user] - Auto-quotes
`.mass_love_raid` / `.mlr` [@user] - Auto-mass love
`.shayari_raid` / `.sr` [@user] - Auto-shayari
`.raid_shayari_raid` / `.rsr` [@user] - Auto-raid shayari
`.roast_boy_raid` / `.rbr` [@user] - Auto-roast boy
`.roast_girl_raid` / `.rgr` [@user] - Auto-roast girl
`.roast_abuse_raid` / `.rar` [@user] - Auto-abuse roast
`.flirt_girl_raid` / `.fgr` [@user] - Auto-flirt girl
`.hindi_roast_boy_raid` / `.hrbr` [@user] - Auto-hindi roast boy
`.hindi_roast_girl_raid` / `.hrgr` [@user] - Auto-hindi roast girl
`.hindi_roast_abuse_raid` / `.hrar` [@user] - Auto-hindi abuse roast
`.hindi_flirt_girl_raid` / `.hfgr` [@user] - Auto-hindi flirt girl
`.raid100_raid` / `.r100r` [@user] - Auto-raid100
`.raid_raid` / `.rdr` [@user] - Auto-raid

🛑 **Stop Commands**
`.stop_reply_raid` / `.srr` - Stop reply raid
`.stop_flirt_raid` / `.sfr` - Stop flirt raid
`.stop_love_raid` / `.slr` - Stop love raid
`.stop_quote_raid` / `.sqr` - Stop quote raid
`.stop_mass_love_raid` / `.smlr` - Stop mass love raid
`.stop_shayari_raid` / `.ssr` - Stop shayari raid
`.stop_raid_shayari_raid` / `.srsr` - Stop raid shayari
`.stop_roast_boy_raid` / `.srbr` - Stop roast boy raid
`.stop_roast_girl_raid` / `.srgr` - Stop roast girl raid
`.stop_roast_abuse_raid` / `.srar` - Stop abuse raid
`.stop_flirt_girl_raid` / `.sfgr` - Stop flirt girl raid
`.stop_hindi_roast_boy_raid` / `.shrbr` - Stop hindi roast boy
`.stop_hindi_roast_girl_raid` / `.shrgr` - Stop hindi roast girl
`.stop_hindi_roast_abuse_raid` / `.shrar` - Stop hindi abuse raid
`.stop_hindi_flirt_girl_raid` / `.shfgr` - Stop hindi flirt girl
`.stop_raid100_raid` / `.sr100r` - Stop raid100 raid
`.stop_raid_raid` / `.srdr` - Stop raid raid

💖 **Romance Commands**
`.love` / `.lv` [@user] - Random love line
`.quote` / `.qt` [@user] - Romantic quote
`.mass_love` / `.mlove` / `.ml` [@user] [count] - Mass love lines
`.shayari` / `.shr` [@user] - Random shayari
`.raid_shayari` / `.raidshayari` / `.rs` [@user] [count] - Shayari raid

🏷 **Tagging Commands**
`.mass_tag` / `.mtag` / `.mt` <@user> <count> <msg> - Mass tag user
`.tag_all` / `.tagall` / `.ta` <msg> - Tag all members
`.tag_admins` / `.tagadmins` / `.tadm` <msg> - Tag admins only

👥 **Special Features**
`.clone` / `.cl` [@user] - Clone PFP + Name + Bio
`.unclone` / `.ucl` - Return to normal
`.checkname` / `.cn` [@user] - Check name history

📊 **Info Commands**
`.user_info` / `.userinfo` / `.ui` [@user] - User information
`.ping` / `.pg` - Bot status
`.alive` / `.al` - Status check

🛑 **Control Commands**
`.stop` / `.st` - Stop all tasks
`.stop_roast` / `.stoproast` / `.str` - Stop roast only
`.stop_tag` / `.stoptag` / `.stt` - Stop tagging only
`.purge` / `.pg` <count> - Delete last N messages
`.purge_all` / `.purgeall` / `.pga` - Delete ALL your messages
`.spam` / `.sp` <@user> <count> <msg> - Spam user

📱 **Status**
`.status` / `.stat` <online/offline> - Set status

⚡️ **All commands auto-delete after use!**
    """
    await event.reply(help_msg)

async def handle(request):
    return web.Response(text="Userbot running", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 8080))
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
    start_msg = await event.reply("🤖 **Ultimate Bot Started!**\n\n⏰ **Current Delay:** 6 seconds\nUse `.delay <seconds>` to change delay\n\nUse `.help` to see all commands."); await delete_after_delay(start_msg)


# Start the client
async def main():
    print("Starting userbot...")
    await client.start()
    #fake web server
    await start_web_server()
    # Start keep-alive task
    client.loop.create_task(keep_alive())
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
