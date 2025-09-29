import os
import re
import sys
import subprocess
import vobject
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyrogram import Client, filters, idle
from pyrogram.types import (
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from pyrogram.errors import FloodWait, UserNotParticipant
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
import platform
import time

# ====================
# Bot Configuration
# ====================

bot = Client(
    name="OKTOCV",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

START_TIME = time.time()

# ====================
# Channel Verification
# ====================

REQUIRED_CHANNEL = "@mafianewera"
ADMIN_USERNAME = "@DiexroDev"

async def check_channel_member(user_id):
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

def verification_required(func):
    async def wrapper(client, message):
        user_id = message.from_user.id
        
        if user_id in OWNER_ID:
            return await func(client, message)
            
        if ngecek_(user_id):
            return await func(client, message)
            
        if not await check_channel_member(user_id):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/mafianewera")],
                [InlineKeyboardButton("✅ Saya Sudah Join", callback_data="verify_join")]
            ])
            
            await message.reply(
                f"**🔒 Akses Dibatasi**\n\n"
                f"Untuk menggunakan bot ini, Anda harus bergabung dengan channel kami terlebih dahulu:\n"
                f"**{REQUIRED_CHANNEL}**\n\n"
                f"Setelah bergabung, klik tombol **✅ Saya Sudah Join**",
                reply_markup=keyboard
            )
            return
            
        return await func(client, message)
    return wrapper

# ====================
# Trial System
# ====================

def get_trial_expiry():
    return datetime.now() + timedelta(days=1)

def is_first_time_user(user_id):
    return user_id not in dbs._buyer

def activate_trial(user_id, user_data):
    dbs._buyer[user_id] = {
        "expired": get_trial_expiry(),
        "name": user_data.get("name", "-"),
        "username": user_data.get("username", "-"),
        "saldo": 0,
        "log": [],
        "is_trial": True,
        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data()

# ====================
# Trial Notification System
# ====================

async def send_trial_expired_notification(user_id):
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Upgrade Premium", url="https://t.me/DiexroDev")],
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/mafianewera")]
        ])
        
        await bot.send_message(
            user_id,
            "⏰ **TRIAL ANDA TELAH HABIS!**\n\n"
            "Masa trial 1 hari Anda telah berakhir. Untuk terus menggunakan semua fitur bot, "
            "silahkan upgrade ke akun premium.\n\n"
            "**Fitur Premium:**\n"
            "• ✅ Akses semua fitur tanpa batas\n"
            "• 🚀 Prioritas processing\n"
            "• 📞 Support 24/7\n"
            "• 🔄 Masa aktif lebih lama\n\n"
            "Hubungi admin untuk informasi lebih lanjut:",
            reply_markup=keyboard
        )
        return True
    except Exception as e:
        print(f"Gagal mengirim notifikasi trial expired ke {user_id}: {e}")
        return False

async def send_trial_reminder(user_id, hours_left):
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Upgrade Sekarang", url="https://t.me/DiexroDev")],
            [InlineKeyboardButton("⏰ Cek Status", callback_data="check_status")]
        ])
        
        if hours_left <= 1:
            time_msg = "⏳ **TRIAL ANDA HAMPIR HABIS!**\nKurang dari 1 jam lagi!"
        elif hours_left <= 6:
            time_msg = f"⏳ **TRIAL ANDA AKAN HABIS!**\nTersisa {hours_left} jam lagi!"
        else:
            time_msg = f"⏰ **Pengingat Trial**\nTersisa {hours_left} jam lagi!"
        
        await bot.send_message(
            user_id,
            f"{time_msg}\n\n"
            "Segera upgrade ke premium untuk terus menikmati semua fitur bot:\n\n"
            "**💎 Keuntungan Premium:**\n"
            "• Akses penuh tanpa batas waktu\n"
            "• Processing lebih cepat\n"
            "• Support prioritas\n"
            "• Fitur terbaru pertama\n\n"
            "Jangan sampai kehabisan!",
            reply_markup=keyboard
        )
        return True
    except Exception as e:
        print(f"Gagal mengirim reminder trial ke {user_id}: {e}")
        return False

async def check_and_notify_trial_users():
    while True:
        try:
            sekarang = datetime.now()
            notified_users = set()
            
            try:
                with open("notified_users.json", "r") as f:
                    notified_data = json.load(f)
                    notified_users = set(notified_data.get("trial_expired", []))
            except FileNotFoundError:
                notified_data = {"trial_expired": [], "trial_reminder": {}}
            
            for user_id, data in list(dbs._buyer.items()):
                if not data.get("is_trial"):
                    continue
                    
                expired = data.get("expired")
                if not expired:
                    continue
                    
                if isinstance(expired, str):
                    try:
                        expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue
                
                sisa_waktu = expired - sekarang
                sisa_jam = int(sisa_waktu.total_seconds() // 3600)
                
                reminder_sent = notified_data.get("trial_reminder", {}).get(str(user_id), 0)
                
                if sisa_jam <= 1 and reminder_sent < 3:
                    await send_trial_reminder(user_id, sisa_jam)
                    notified_data.setdefault("trial_reminder", {})[str(user_id)] = 3
                    
                elif sisa_jam <= 6 and reminder_sent < 2:
                    await send_trial_reminder(user_id, sisa_jam)
                    notified_data.setdefault("trial_reminder", {})[str(user_id)] = 2
                    
                elif sisa_jam <= 24 and reminder_sent < 1:
                    await send_trial_reminder(user_id, sisa_jam)
                    notified_data.setdefault("trial_reminder", {})[str(user_id)] = 1
                
                if sisa_waktu.total_seconds() <= 0 and user_id not in notified_users:
                    success = await send_trial_expired_notification(user_id)
                    if success:
                        notified_users.add(user_id)
                        notified_data["trial_expired"] = list(notified_users)
            
            with open("notified_users.json", "w") as f:
                json.dump(notified_data, f, indent=2)
                
            await asyncio.sleep(1800)
            
        except Exception as e:
            print(f"Error dalam check_and_notify_trial_users: {e}")
            await asyncio.sleep(300)

@bot.on_callback_query(filters.regex("^check_status$"))
async def check_status_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    if user_id not in dbs._buyer:
        await callback_query.answer("❌ Anda belum memiliki akses.", show_alert=True)
        return
        
    data = dbs._buyer[user_id]
    expired = data.get("expired")
    
    if isinstance(expired, str):
        try:
            expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
        except:
            expired = None
            
    if expired:
        sisa_waktu = expired - datetime.now()
        if sisa_waktu.total_seconds() > 0:
            jam = int(sisa_waktu.total_seconds() // 3600)
            menit = int((sisa_waktu.total_seconds() % 3600) // 60)
            status_msg = f"⏰ Sisa waktu: {jam} jam {menit} menit"
        else:
            status_msg = "❌ Trial telah habis"
    else:
        status_msg = "❌ Tidak ada akses aktif"
        
    await callback_query.answer(status_msg, show_alert=True)

# ====================
# Utility Functions
# ====================

def get_runtime():
    seconds = int(time.time() - START_TIME)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def remove_numbers(name):
    return re.sub(r'\d+', '', name).strip()

def remove_emojis(text):
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def read_vcf(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        vcard_data = file.read()
    return vobject.readComponents(vcard_data)

def write_vcf(contacts, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for contact in contacts:
            file.write(contact.serialize())

def count_contacts_in_vcf(file_path):
    contacts = list(read_vcf(file_path))
    return len(contacts)

def count_contacts_in_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        numbers = re.findall(r'\d+', content)
        return len(numbers)

def rename_contacts(contacts, start_index=1):
    renamed_contacts = []
    for index, contact in enumerate(contacts, start=start_index):
        if hasattr(contact, 'fn'):
            clean_name = remove_numbers(contact.fn.value)
            clean_name = remove_emojis(clean_name)
            contact.fn.value = f'{clean_name} {str(index).zfill(4)}'
        renamed_contacts.append(contact)
    return renamed_contacts

def split_vcf(input_file, newna, contacts_per_file=100):
    contacts = list(read_vcf(input_file))
    total_contacts = len(contacts)
    file_count = (total_contacts + contacts_per_file - 1) // contacts_per_file
    dump_ = []
    global_index = 1

    for i in range(file_count):
        start = i * contacts_per_file
        end = min(start + contacts_per_file, total_contacts)
        contacts_chunk = rename_contacts(contacts[start:end], start_index=global_index)
        output_file = f'{newna}-{i+1}.vcf'
        write_vcf(contacts_chunk, output_file)
        dump_.append(output_file)
        global_index += len(contacts_chunk)

    return dump_

def split_vcf_session(input_file, newna, contacts_per_file=100, start_index=1):
    contacts = list(read_vcf(input_file))
    total_contacts = len(contacts)
    file_count = (total_contacts + contacts_per_file - 1) // contacts_per_file
    dump_ = []
    global_index = start_index

    for i in range(file_count):
        start = i * contacts_per_file
        end = min(start + contacts_per_file, total_contacts)
        chunk = rename_contacts(contacts[start:end], start_index=global_index)
        filename = f"{newna}-{i+1}.vcf"
        write_vcf(chunk, filename)
        dump_.append(filename)
        global_index += len(chunk)

    return {
        "files": dump_,
        "next_index": global_index
    }

def split_cut_vcf(input_file, namectc, dibagi_menjadi_bagian=1):
    contacts = list(read_vcf(input_file))
    total_contacts = len(contacts)
    contacts_per_file = (total_contacts + dibagi_menjadi_bagian - 1) // dibagi_menjadi_bagian

    dump_ = []
    file_index = 1
    current_contacts = []
    global_index = 1

    for i, contact in enumerate(contacts, start=1):
        current_contacts.append(contact)
        if len(current_contacts) == contacts_per_file and file_index < dibagi_menjadi_bagian:
            output_file = f'{namectc.replace(".vcf", "")}-{file_index}.vcf'
            renamed_chunk = rename_contacts(current_contacts, global_index)
            write_vcf(renamed_chunk, output_file)
            dump_.append(output_file)
            global_index += len(current_contacts)
            current_contacts = []
            file_index += 1

    if current_contacts:
        output_file = f'{namectc.replace(".vcf", "")}-{file_index}.vcf'
        renamed_chunk = rename_contacts(current_contacts, global_index)
        write_vcf(renamed_chunk, output_file)
        dump_.append(output_file)

    return dump_

def merge_vcf_files(file_paths, output_file_path):
    merged_contacts = []
    for file_path in file_paths:
        contacts = read_vcf(file_path)
        merged_contacts.extend(contacts)
    write_vcf(merged_contacts, f"{output_file_path}.vcf")

def create_vcf_entry(phone_number, contact_name):
    vcf_entry = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{"+" if not str(phone_number).startswith("0") else ""}{phone_number}
END:VCARD
"""
    return vcf_entry

def create_vcf_file(phone_numbers, ctcname, file_name, start_index=1):
    with open(file_name, "w") as file:
        for i, phone_number in enumerate(phone_numbers, start=start_index):
            vcf_entry = create_vcf_entry(phone_number, f"{ctcname}-{str(i).zfill(4)}")
            file.write(vcf_entry + "\n")
    return file_name

def extract_numbers_from_file(file_path):
    numbers = []
    with open(file_path, 'r') as file:
        content = file.read()
        numbers = re.findall(r'\d+', content)
    return numbers

def process_filesgbg(file_paths, output_file):
    all_numbers = []
    for file_path in file_paths:
        if os.path.isfile(file_path):
            numbers = extract_numbers_from_file(file_path)
            all_numbers.extend(numbers)
        else:
            print(f"File {file_path} tidak ditemukan.")
    with open(output_file, 'w') as file:
        for number in all_numbers:
            file.write(number + '\n')

def extract_phone_numbers(vcf_file_path, output_txt_file_path):
    with open(vcf_file_path, 'r') as vcf_file:
        vcf_content = vcf_file.read()
    vcard_list = vobject.readComponents(vcf_content)
    with open(output_txt_file_path, 'w') as txt_file:
        for vcard in vcard_list:
            if hasattr(vcard, 'tel'):
                for tel in vcard.tel_list:
                    txt_file.write(tel.value + '\n')

def hapus_spasi_antar_nomor(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    modified_lines = [''.join(line.split()) + '\n' for line in lines]
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)
    modified_lines = [line.replace('-', '') for line in modified_lines]
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)
    modified_lines = [line.replace('(', '') for line in modified_lines]
    modified_lines = [line.replace(')', '') for line in modified_lines]
    modified_lines = [line.replace('/', '') for line in modified_lines]
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)

def parse_timedelta(time_str):
    pattern = r'(\d+)([hmb])'
    time_dict = {'h': 'days', 'm': 'weeks', 'b': 'months'}
    matches = re.findall(pattern, time_str)
    if not matches:
        return None
    kwargs = {'days': 0, 'weeks': 0, 'months': 0}
    for value, unit in matches:
        kwargs[time_dict[unit]] += int(value)
    return kwargs

def add_time_delta(current_time, time_str):
    delta_dict = parse_timedelta(time_str)
    if not delta_dict:
        return None
    new_time = current_time + timedelta(days=delta_dict['days'], weeks=delta_dict['weeks'])
    new_time = new_time + relativedelta(months=delta_dict['months'])
    return new_time

def split_vcf_custom_start_session(input_file, newna, contacts_per_file=100, start_number=1, start_file=1):
    contacts = list(read_vcf(input_file))
    total_contacts = len(contacts)
    file_count = (total_contacts + contacts_per_file - 1) // contacts_per_file
    dump_ = []
    global_index = start_number
    file_index = start_file

    for _ in range(file_count):
        start = (file_index - start_file) * contacts_per_file
        end = min(start + contacts_per_file, total_contacts)
        chunk = rename_contacts(contacts[start:end], start_index=global_index)
        filename = f"{newna}-{file_index}.vcf"
        write_vcf(chunk, filename)
        dump_.append(filename)
        global_index += len(chunk)
        file_index += 1

    return dump_, global_index, file_index

# ====================
# Database Management
# ====================

class dbs:
    _buyer = {}

class session:
    split_counter = 1
    file_counter = 1

session_lanjutan = {
    "split_counter": 1,
    "file_counter": 1
}

def load_data():
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            cleaned_data = {}
            for uid, value in data.items():
                if not isinstance(value, dict):
                    expired = value
                    cleaned_data[int(uid)] = {
                        "expired": datetime.strptime(expired, "%Y-%m-%d %H:%M:%S") if expired else None,
                        "name": "-",
                        "username": "-",
                        "saldo": 0,
                        "log": [],
                        "is_trial": False
                    }
                else:
                    expired = value.get("expired")
                    if expired:
                        try:
                            expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S.%f")
                            except:
                                expired = datetime.now()
                        value["expired"] = expired
                    cleaned_data[int(uid)] = value
            return cleaned_data
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

def save_data():
    def serializer(obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return obj

    try:
        with open('data.json', 'w') as file:
            json.dump(dbs._buyer, file, indent=2, default=serializer)
    except Exception as e:
        print(f"Error saving data: {e}")

# ====================
# Keyboard Layouts
# ====================

home_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("💎 Status"), KeyboardButton("📊 Hitung Kontak")],
    [KeyboardButton("🔄 Convert File"), KeyboardButton("✂️ Potong File")],
    [KeyboardButton("📁 Gabung File"), KeyboardButton("🛠️ Tools Lainnya")],
    [KeyboardButton("📞 Admin"), KeyboardButton("ℹ️ Bantuan")]
], resize_keyboard=True)

convert_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🏷️ TXT to VCF"), KeyboardButton("🚀 XLS to VCF")],
    [KeyboardButton("♻️ VCF to TXT"), KeyboardButton("📨 MSG to TXT")],
    [KeyboardButton("🔙 Kembali")]
], resize_keyboard=True)

split_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📊 POTONG VCF"), KeyboardButton("📊 POTONG LANJUTAN")],
    [KeyboardButton("🪓 BAGI VCF"), KeyboardButton("🪓 BAGI LANJUTAN")],
    [KeyboardButton("🔙 Kembali")]
], resize_keyboard=True)

tools_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🚧 RAPIKAN TXT"), KeyboardButton("🔍 Cek Nama Kontak")],
    [KeyboardButton("📨 ADMIN"), KeyboardButton("🗄️ Gabung TXT")],
    [KeyboardButton("🗄️ Gabung VCF"), KeyboardButton("🔙 Kembali")]
], resize_keyboard=True)

back_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔙 Kembali")]
], resize_keyboard=True)

cancel_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("❌ Batal")]
], resize_keyboard=True)

# ====================
# Filter Functions
# ====================

def on_msg(pilter=None):
    def wrapper(func):
        @bot.on_message(pilter)
        async def wrapped_func(client, message):
            try:
                await func(client, message)
            except Exception as err:
                await message.reply(f"❌ **Error:**\n`{err}`")
        return wrapped_func
    return wrapper

def on_txt(message):
    return message.document and message.document.file_name.endswith(".txt")

def on_vcf(message):
    return message.document and message.document.file_name.endswith(".vcf")

def on_xls(message):
    return message.document and (message.document.file_name.endswith(".xls") or 
                               message.document.file_name.endswith(".xlsx"))

def ngecek_(user_id):
    if user_id not in dbs._buyer:
        return False
    data = dbs._buyer[user_id]
    if not data.get("expired"):
        return False
    return data["expired"] > datetime.now()

def batals(text):
    return text == "❌ Batal"

# ====================
# Core Handlers
# ====================

@on_msg(filters.command("start") & filters.private)
async def start_(client, message):
    user_id = message.from_user.id
    name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    username = f"@{message.from_user.username}" if message.from_user.username else "-"

    all_users = load_all_users()
    if str(user_id) not in all_users:
        all_users[str(user_id)] = {
            "name": name,
            "username": username,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_all_users(all_users)

    if is_first_time_user(user_id):
        activate_trial(user_id, {
            "name": name,
            "username": username
        })
        trial_msg = "🎉 **TRIAL 1 HARI AKTIF!**\nAnda dapat menggunakan semua fitur gratis selama 1 hari."
    else:
        trial_msg = ""

    if not ngecek_(user_id) and not await check_channel_member(user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/mafianewera")],
            [InlineKeyboardButton("✅ Saya Sudah Join", callback_data="verify_join")]
        ])
        
        await message.reply(
            f"👋 **Hai {name}!**\n\n"
            f"{trial_msg}\n\n"
            f"🔒 **Akses Dibatasi**\n"
            f"Untuk menggunakan bot ini, Anda harus bergabung dengan channel kami terlebih dahulu:\n"
            f"**{REQUIRED_CHANNEL}**\n\n"
            f"Setelah bergabung, klik tombol **✅ Saya Sudah Join**",
            reply_markup=keyboard
        )
        return

    await message.reply(
        f"👋 **Hai {name}!**\n\n"
        f"{trial_msg}\n\n"
        f"**Selamat datang di Bot Konversi Kontak!**\n\n"
        f"Saya dapat membantu Anda mengonversi berbagai format file kontak dengan mudah dan cepat.\n\n"
        f"**Fitur Utama:**\n"
        f"• Convert TXT/VCF/XLS\n"
        f"• Potong & Gabung File\n"
        f"• Tools Utilities\n\n"
        f"Gunakan menu di bawah untuk mulai:",
        reply_markup=home_keyboard
    )

@bot.on_callback_query(filters.regex("^verify_join$"))
async def verify_join_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    if await check_channel_member(user_id):
        if is_first_time_user(user_id):
            user_data = {
                "name": f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}".strip(),
                "username": f"@{callback_query.from_user.username}" if callback_query.from_user.username else "-"
            }
            activate_trial(user_id, user_data)
            trial_msg = "\n\n🎉 **TRIAL 1 HARI AKTIF!**\nAnda dapat menggunakan semua fitur gratis selama 1 hari."
        else:
            trial_msg = ""
            
        await callback_query.message.edit(
            f"✅ **Verifikasi Berhasil!**{trial_msg}\n\n"
            "Terima kasih telah bergabung dengan channel kami. "
            "Sekarang Anda dapat menggunakan bot ini.\n\n"
            "Silakan gunakan menu di bawah untuk mulai:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Mulai Menggunakan", callback_data="start_using")]
            ])
        )
    else:
        await callback_query.answer(
            "❌ Anda belum bergabung dengan channel. Silakan join terlebih dahulu!",
            show_alert=True
        )

@bot.on_callback_query(filters.regex("^start_using$"))
async def start_using_callback(client, callback_query):
    await callback_query.message.delete()
    await callback_query.message.reply(
        "Silakan pilih menu yang diinginkan:",
        reply_markup=home_keyboard
    )

# ====================
# Menu Handlers
# ====================

@on_msg(filters.regex("^🔙 Kembali$") & filters.private)
async def back_handler(client, message):
    await message.reply(
        "**Menu Utama**\nPilih opsi yang diinginkan:",
        reply_markup=home_keyboard
    )

@on_msg(filters.regex("^🔄 Convert File$") & filters.private)
@verification_required
async def convert_menu(client, message):
    await message.reply(
        "**🔄 Menu Convert File**\nPilih jenis konversi:",
        reply_markup=convert_keyboard
    )

@on_msg(filters.regex("^✂️ Potong File$") & filters.private)
@verification_required
async def split_menu(client, message):
    await message.reply(
        "**✂️ Menu Potong File**\nPilih jenis pemotongan:",
        reply_markup=split_keyboard
    )

@on_msg(filters.regex("^📁 Gabung File$") & filters.private)
@verification_required
async def merge_menu(client, message):
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🗄️ Gabung TXT"), KeyboardButton("🗄️ Gabung VCF")],
        [KeyboardButton("🔙 Kembali")]
    ], resize_keyboard=True)
    await message.reply(
        "**📁 Menu Gabung File**\nPilih jenis file yang ingin digabung:",
        reply_markup=keyboard
    )

@on_msg(filters.regex("^🛠️ Tools Lainnya$") & filters.private)
@verification_required
async def tools_menu(client, message):
    await message.reply(
        "**🛠️ Menu Tools Lainnya**\nPilih tool yang diinginkan:",
        reply_markup=tools_keyboard
    )

@on_msg(filters.regex("^📞 Admin$") & filters.private)
async def admin_contact(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Hubungi Admin", url="https://t.me/DiexroDev")],
        [InlineKeyboardButton("💬 Channel Updates", url="https://t.me/mafianewera")]
    ])
    
    await message.reply(
        "**📞 Hubungi Admin**\n\n"
        "Untuk pertanyaan, bantuan, atau ingin upgrade ke premium:\n\n"
        f"👤 **Admin:** {ADMIN_USERNAME}\n"
        f"📢 **Channel:** {REQUIRED_CHANNEL}\n\n"
        "Klik tombol di bawah untuk langsung terhubung:",
        reply_markup=keyboard
    )

@on_msg(filters.regex("^ℹ️ Bantuan$") & filters.private)
async def help_menu(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Hubungi Admin", url="https://t.me/DiexroDev")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/mafianewera")],
        [InlineKeyboardButton("🆘 Bantuan Cepat", callback_data="quick_help")]
    ])
    
    await message.reply(
        "**ℹ️ Menu Bantuan**\n\n"
        "**Cara Menggunakan Bot:**\n"
        "1. Pilih menu yang diinginkan\n"
        "2. Ikuti instruksi yang diberikan\n"
        "3. Tunggu proses selesai\n\n"
        "**Status Akses:**\n"
        "• 🆓 Trial: 1 hari gratis\n"
        "• 💎 Premium: Akses penuh\n\n"
        "**Butuh Bantuan?**\n"
        "• Baca petunjuk di setiap menu\n"
        "• Hubungi admin untuk pertanyaan\n"
        "• Join channel untuk update",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("^quick_help$"))
async def quick_help_callback(client, callback_query):
    await callback_query.answer(
        "🆘 **Bantuan Cepat:**\n\n"
        "• Trial: 1 hari gratis\n"
        "• Premium: Hubungi admin\n"
        "• Problem? Contact @DiexroDev\n"
        "• Update: @mafianewera",
        show_alert=True
    )

# ====================
# Status Handler
# ====================

@on_msg(filters.regex("^💎 Status$") & filters.private)
async def status_user(client, message):
    user_id = message.from_user.id

    if user_id not in dbs._buyer:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Upgrade Premium", url="https://t.me/DiexroDev")],
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/mafianewera")]
        ])
        return await message.reply(
            "❌ **Anda belum memiliki akses.**\n\n"
            "Bergabung dengan channel kami untuk mendapatkan trial 1 hari gratis, "
            "atau hubungi admin untuk upgrade premium.",
            reply_markup=keyboard
        )

    data = dbs._buyer[user_id]
    nama = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    username = f"@{message.from_user.username}" if message.from_user.username else data.get("username", "-")
    saldo = data.get("saldo", 0)

    expired = data.get("expired")
    if isinstance(expired, str):
        try:
            expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S.%f")
        except:
            try:
                expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
            except:
                expired = None
                
    expired_str = expired.strftime("%Y-%m-%d %H:%M:%S") if expired else "-"
    
    is_trial = data.get("is_trial", False)
    access_type = "🆓 TRIAL" if is_trial else "💎 PREMIUM"
    
    if expired:
        time_left = expired - datetime.now()
        if time_left.total_seconds() > 0:
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            time_left_str = f"{days}h {hours}j {minutes}m"
        else:
            time_left_str = "❌ EXPIRED"
    else:
        time_left_str = "❌ TIDAK AKTIF"

    txt = (
        f"**{access_type} STATUS**\n\n"
        f"**👤 User Info:**\n"
        f"• ID: `{user_id}`\n"
        f"• Nama: `{nama}`\n"
        f"• Username: `{username}`\n\n"
        f"**⏰ Status Akses:**\n"
        f"• Tipe: {access_type}\n"
        f"• Expired: `{expired_str}`\n"
        f"• Sisa Waktu: `{time_left_str}`\n"
        f"• Saldo: `{saldo}`"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Upgrade Premium", url="https://t.me/DiexroDev")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/mafianewera")]
    ]) if is_trial or not ngecek_(user_id) else None

    await message.reply(txt, reply_markup=keyboard)

# ====================
# Function Handlers
# ====================

@on_msg(filters.regex("^🚧 RAPIKAN TXT$") & filters.private)
@verification_required
async def ngecremotate(client, message):
    user_id = message.from_user.id
    if not ngecek_(user_id):
        return await message.reply(
            "❌ **Akses Ditolak**\n\n"
            "Trial Anda telah habis atau Anda belum memiliki akses.\n\n"
            "Hubungi admin untuk upgrade premium:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Hubungi Admin", url="https://t.me/DiexroDev")]
            ])
        )
        
    ask1 = await client.ask(
        text="**📤 Kirim file TXT yang ingin dirapihkan:**",
        user_id=user_id, 
        chat_id=user_id, 
        reply_markup=cancel_keyboard
    )
    
    if batals(ask1.text) or not on_txt(ask1):
        return await message.reply("❌ Proses dibatalkan.", reply_markup=home_keyboard)
        
    file = await ask1.download()
    hapus_spasi_antar_nomor(file)
    
    try:
        await message.reply_document(file, caption="✅ **File berhasil dirapihkan**")
        await message.reply("Silakan pilih menu lainnya:", reply_markup=home_keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_document(file)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        os.remove(file)

@on_msg(filters.regex("^📨 MSG to TXT$") & filters.private)
@verification_required
async def ngecreate(client, message):
    user_id = message.from_user.id
    if not ngecek_(user_id):
        return await message.reply(
            "❌ **Akses Ditolak**\n\nTrial Anda telah habis. Hubungi admin untuk upgrade premium.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Hubungi Admin", url="https://t.me/DiexroDev")]
            ])
        )
        
    ask1 = await client.ask(
        text="**📝 Masukkan nomor yang ingin diubah jadi file:**",
        user_id=user_id, 
        chat_id=user_id, 
        reply_markup=cancel_keyboard
    )
    
    if batals(ask1.text):
        return await message.reply("❌ Proses dibatalkan.", reply_markup=home_keyboard)
        
    ask2 = await client.ask(
        text="**📁 Masukkan nama file baru:**",
        user_id=user_id, 
        chat_id=user_id, 
        reply_markup=cancel_keyboard
    )
    
    if batals(ask2.text):
        return await message.reply("❌ Proses dibatalkan.", reply_markup=home_keyboard)
        
    newname = ask2.text
    with open(f"{newname}.txt", 'w') as file:
        file.write(ask1.text)
        
    try:
        await message.reply_document(f"{newname}.txt", caption="✅ **File berhasil dibuat**")
        await message.reply("Silakan pilih menu lainnya:", reply_markup=home_keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_document(f"{newname}.txt")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        os.remove(f"{newname}.txt")

@on_msg(filters.regex("^📨 ADMIN$") & filters.private)
@verification_required
async def ngecreateadmin(client, message):
    user_id = message.from_user.id
    if not ngecek_(user_id):
        return await message.reply(
            "❌ **Akses Ditolak**\n\nTrial Anda telah habis. Hubungi admin untuk upgrade premium.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Hubungi Admin", url="https://t.me/DiexroDev")]
            ])
        )

    ask1 = await client.ask(
        text="**📱 Masukkan nomor admin (pisahkan dengan spasi):**",
        user_id=user_id,
        chat_id=user_id,
        reply_markup=cancel_keyboard
    )

    if batals(ask1.text):
        return await message.reply("❌ Proses dibatalkan.", reply_markup=home_keyboard)

    dmp_adm = ask1.text.split()
    file_name = 'ADMIN.vcf'
    
    with open(file_name, "w") as file:
        for index, phone_number in enumerate(dmp_adm, start=1):
            vcf_entry = create_vcf_entry(phone_number, f"ADMIN-{str(index).zfill(4)}")
            file.write(vcf_entry + "\n")

    try:
        await message.reply_document(file_name, caption="✅ **File ADMIN berhasil dibuat**")
        await message.reply("Silakan pilih menu lainnya:", reply_markup=home_keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_document(file_name)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        os.remove(file_name)

# ====================
# Admin Commands
# ====================

@on_msg(filters.command("add") & filters.private)
async def add_(client, message):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply("❌ Fitur ini hanya untuk owner.")

    try:
        _, target_id, timeny = message.text.split(maxsplit=2)
        target_id = int(target_id)
    except:
        return await message.reply(
            "**Format salah!**\n\n"
            "Contoh: `/add 12345678 1b`\n\n"
            "**Note:**\n"
            "• b = bulan\n" 
            "• m = minggu\n"
            "• h = hari"
        )

    user_data = dbs._buyer.get(target_id, {})
    current_expired = user_data.get("expired", datetime.now())
    
    if isinstance(current_expired, str):
        try:
            current_expired = datetime.strptime(current_expired, "%Y-%m-%d %H:%M:%S")
        except:
            current_expired = datetime.now()

    new_expired = add_time_delta(current_expired, timeny.lower())
    if not new_expired:
        return await message.reply("❌ Format waktu tidak valid. Gunakan akhiran h/m/b.")

    dbs._buyer[target_id] = {
        "expired": new_expired,
        "name": user_data.get("name", "-"),
        "username": user_data.get("username", "-"),
        "saldo": user_data.get("saldo", 0),
        "log": user_data.get("log", []),
        "is_trial": False
    }

    save_data()
    await message.reply(f"✅ **Berhasil menambahkan user** `{target_id}` **selama {timeny}**")

@on_msg(filters.command("remove") & filters.private)
async def remove_(client, message):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply("❌ Fitur ini hanya untuk owner.")

    if len(message.text.split()) != 2 or not message.text.split()[1].isnumeric():
        return await message.reply("**Format salah!**\n\nContoh: `/remove 91838299`")

    _, target_id = message.text.split()
    removed = dbs._buyer.pop(int(target_id), None)
    save_data()

    if removed:
        await message.reply(f"✅ **Pengguna {target_id} telah dihapus dari akses!**")
    else:
        await message.reply(f"❌ **Pengguna {target_id} tidak ditemukan dalam database.**")

@on_msg(filters.command("runtime") & filters.user(OWNER_ID))
async def runtime_handler(client, message):
    os_info = platform.system() + " " + platform.release()
    uptime = get_runtime()
    total_users = len(dbs._buyer)
    active_users = len([uid for uid, data in dbs._buyer.items() if ngecek_(uid)])
    
    await message.reply(
        f"**🤖 Bot Status**\n\n"
        f"🖥️ **OS:** `{os_info}`\n"
        f"⏱️ **Uptime:** `{uptime}`\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"✅ **Active Users:** `{active_users}`\n"
        f"🔧 **Version:** `2.0.0`"
    )

# ====================
# System Functions
# ====================

def load_all_users():
    try:
        with open("users_all.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_all_users(data):
    with open("users_all.json", "w") as f:
        json.dump(data, f, indent=2)

async def check_exp_loop():
    while True:
        try:
            waktu_sekarang = datetime.now()
            expired_users = []

            for user_id, data in list(dbs._buyer.items()):
                expired = data.get("expired")
                if not expired:
                    continue

                if isinstance(expired, str):
                    try:
                        expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue

                if expired < waktu_sekarang:
                    if data.get("is_trial"):
                        await send_trial_expired_notification(user_id)
                        print(f"✅ Notifikasi trial expired dikirim ke {user_id}")
                    
                    expired_users.append(user_id)

            for user_id in expired_users:
                user_data = dbs._buyer.get(user_id, {})
                if user_data.get("is_trial"):
                    print(f"🆓 Trial expired untuk user {user_id}")
                else:
                    print(f"💎 Premium expired untuk user {user_id}")
                del dbs._buyer[user_id]

            if expired_users:
                save_data()
                print(f"🧹 Cleaned {len(expired_users)} expired users")

            await asyncio.sleep(300)
        except Exception as e:
            print(f"❌ Error in check_exp_loop: {e}")
            await asyncio.sleep(60)

async def main():
    try:
        print("🔄 Loading data...")
        data_ = load_data()
        dbs._buyer = data_
        
        print("🚀 Starting bot...")
        await bot.start()
        print("✅ Bot started successfully!")
        
        asyncio.create_task(check_exp_loop())
        asyncio.create_task(check_and_notify_trial_users())
        print("✅ Background tasks started")
        
        print("🤖 Bot is now running...")
        await idle()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
    finally:
        print("🛑 Stopping bot...")
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())