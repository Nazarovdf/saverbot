import telebot
import os
import shutil
import uuid
import re
import json
from datetime import datetime
from telebot import types
from dotenv import load_dotenv
import yt_dlp
import requests
from urllib.parse import urlparse
import instaloader

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
except ValueError:
    ADMIN_ID = 0  # Default if not set or invalid

bot = telebot.TeleBot(BOT_TOKEN)

# Directory for temporary files
TEMP_DIR = "temp_downloads"

def ensure_temp_dir():
    """Ensure temp directory exists"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)

ensure_temp_dir()

# User data storage
user_data = {}

# Users database file
USERS_DB_FILE = "users_db.json"

# Load or create users database
def load_users_db():
    """Load users database from file"""
    if os.path.exists(USERS_DB_FILE):
        try:
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users_db(db):
    """Save users database to file"""
    try:
        with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving users DB: {e}")

def register_user(user):
    """Register or update user in database"""
    db = load_users_db()
    user_id = str(user.id)
    
    if user_id not in db:
        db[user_id] = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'total_downloads': 0
        }
    else:
        db[user_id]['last_seen'] = datetime.now().isoformat()
        db[user_id]['username'] = user.username
        db[user_id]['first_name'] = user.first_name
        db[user_id]['last_name'] = user.last_name
    
    save_users_db(db)
    return db[user_id]

def increment_download_count(user_id):
    """Increment user's download count"""
    db = load_users_db()
    user_id_str = str(user_id)
    
    if user_id_str in db:
        db[user_id_str]['total_downloads'] = db[user_id_str].get('total_downloads', 0) + 1
        save_users_db(db)

def is_admin(user_id):
    """Check if user is admin"""
    return ADMIN_ID != 0 and user_id == ADMIN_ID

users_db = load_users_db()

# Instagram loader
ig_loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False,
)


def detect_platform(url):
    """Detect which platform the URL belongs to"""
    url_lower = url.lower()
    if 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram', '📸 Instagram'
    elif 'tiktok.com' in url_lower:
        return 'tiktok', '🎵 TikTok'
    elif 'pinterest.com' in url_lower or 'pin.it' in url_lower:
        return 'pinterest', '📌 Pinterest'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube', '▶️ YouTube'
    else:
        return None, None


def cleanup_user_files(user_id):
    """Clean up user's temporary files"""
    if user_id in user_data:
        file_path = user_data[user_id].get('file_path')
        folder_path = user_data[user_id].get('folder_path')
        
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        if folder_path and os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path, ignore_errors=True)
            except:
                pass


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Register user
    register_user(message.from_user)
    
    welcome_text = """
🎬 <b>Media Downloader Bot</b>

<b>Qo'llab-quvvatlanadigan platformalar:</b>

📸 <b>Instagram</b>
   • Video va rasmlar
   • Audio ajratish

🎵 <b>TikTok</b>
   • Videolar
   • Audio ajratish

📌 <b>Pinterest</b>
   • Rasmlar

▶️ <b>YouTube</b>
   • Turli sifatlar (144p-2160p)
   • Faqat MP3
   • Audio ajratish

━━━━━━━━━━━━━━━━━

<b>📝 Qanday foydalanish:</b>
1️⃣ Havolani nusxalang
2️⃣ Menga yuboring
3️⃣ Bot avtomatik aniqlaydi!

<i>Misol havolalar uchun /examples buyrug'ini yuboring</i>
"""
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_help = types.KeyboardButton("❓ Yordam")
    btn_examples = types.KeyboardButton("📝 Misollar")
    btn_platforms = types.KeyboardButton("🌐 Platformalar")
    btn_stats = types.KeyboardButton("📊 Statistika")
    markup.add(btn_help, btn_examples)
    markup.add(btn_platforms, btn_stats)
    
    # Add admin button if user is admin
    if is_admin(message.from_user.id):
        btn_admin = types.KeyboardButton("👑 Admin Panel")
        markup.add(btn_admin)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)


def download_instagram(url, user_id, message):
    """Download Instagram video/image"""
    folder_path = None
    try:
        # Ensure temp directory exists
        ensure_temp_dir()
        
        # Extract shortcode
        shortcode = url.split("/")[-2] if url.split("/")[-2] else url.split("/")[-3]
        
        # Use simple filename without nested folders
        temp_name = f"ig_{user_id}_{uuid.uuid4().hex[:8]}"
        folder_path = os.path.join(TEMP_DIR, temp_name)
        
        # Create folder explicitly
        os.makedirs(folder_path, exist_ok=True)
        
        # Download post
        post = instaloader.Post.from_shortcode(ig_loader.context, shortcode)
        ig_loader.download_post(post, target=folder_path)
        
        # Get caption
        caption = post.caption if post.caption else "📸 Instagram"
        if len(caption) > 200:
            caption = caption[:197] + "..."
        
        
        # Find media file
        media_file = None
        is_video = False
        
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if file.endswith(".mp4"):
                    media_file = file_path
                    is_video = True
                    break
                elif file.endswith(".jpg") or file.endswith(".png"):
                    media_file = file_path
                    break
        
        if media_file and os.path.exists(media_file):
            # Store for MP3 extraction if video
            if is_video:
                user_data[user_id] = {
                    'file_path': media_file,
                    'folder_path': folder_path,
                    'platform': 'instagram',
                    'is_video': is_video
                }
            
            # Send media
            try:
                with open(media_file, 'rb') as file:
                    if is_video:
                        markup = types.InlineKeyboardMarkup()
                        btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
                        markup.add(btn_audio)
                        bot.send_video(message.chat.id, file, caption=caption, reply_markup=markup)
                    else:
                        bot.send_photo(message.chat.id, file, caption=caption)
            except Exception as send_error:
                # If sending fails, try without caption
                with open(media_file, 'rb') as file:
                    if is_video:
                        markup = types.InlineKeyboardMarkup()
                        btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
                        markup.add(btn_audio)
                        bot.send_video(message.chat.id, file, reply_markup=markup)
                    else:
                        bot.send_photo(message.chat.id, file)
            
            # Increment download count
            increment_download_count(user_id)
            
            # Cleanup if not video (video needs to be kept for MP3)
            if not is_video and folder_path:
                try:
                    shutil.rmtree(folder_path, ignore_errors=True)
                except:
                    pass
            
            return True
        else:
            bot.reply_to(message, "❌ Instagram'dan media topilmadi. Havola to'g'rimi?")
            # Cleanup failed download
            if folder_path and os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path, ignore_errors=True)
                except:
                    pass
            return False
            
    except Exception as e:
        bot.reply_to(message, f"❌ Instagram xatosi: {str(e)}")
        # Cleanup on error
        if folder_path and os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path, ignore_errors=True)
            except:
                pass
        return False


def download_tiktok(url, user_id, message):
    """Download TikTok video"""
    try:
        ensure_temp_dir()
        download_path = os.path.join(TEMP_DIR, f"tiktok_{user_id}_{uuid.uuid4().hex[:8]}.mp4")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': download_path,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(download_path):
            user_data[user_id] = {
                'file_path': download_path,
                'platform': 'tiktok',
                'is_video': True
            }
            
            with open(download_path, 'rb') as video:
                markup = types.InlineKeyboardMarkup()
                btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
                markup.add(btn_audio)
                bot.send_video(message.chat.id, video, reply_markup=markup)
            
            # Increment download count
            increment_download_count(user_id)
            
            return True
        else:
            bot.reply_to(message, "❌ TikTok video yuklab olinmadi")
            return False
            
    except Exception as e:
        bot.reply_to(message, f"❌ TikTok xatosi: {str(e)}")
        return False


def download_pinterest(url, user_id, message):
    """Download Pinterest image"""
    try:
        ensure_temp_dir()
        download_path = os.path.join(TEMP_DIR, f"pinterest_{user_id}_{uuid.uuid4().hex[:8]}.jpg")
        
        # Use yt-dlp to download
        ydl_opts = {
            'format': 'best',
            'outtmpl': download_path,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check if file exists and has content
        if not os.path.exists(download_path) or os.path.getsize(download_path) < 1024:
            bot.reply_to(message, "❌ Pinterest'dan rasm yuklab olinmadi. Havola private bo'lishi mumkin.")
            return False
        
        user_data[user_id] = {
            'file_path': download_path,
            'platform': 'pinterest',
            'is_video': False
        }
        
        # Send as document to avoid Telegram image processing errors
        with open(download_path, 'rb') as photo:
            try:
                bot.send_photo(message.chat.id, photo)
            except Exception as e:
                # If photo fails, send as document
                photo.seek(0)
                bot.send_document(message.chat.id, photo, caption="📌 Pinterest Image")
        
        # Increment download count
        increment_download_count(user_id)
        
        cleanup_user_files(user_id)
        return True
        
    except Exception as e:
        bot.reply_to(message, f"❌ Pinterest xatosi: {str(e)}")
        return False


def get_youtube_formats(url):
    """Get available YouTube formats"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = {}
            for f in info['formats']:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    if height and height >= 144:
                        quality = f"{height}p"
                        if quality not in formats:
                            formats[quality] = f['format_id']
            
            return formats, info.get('title', 'video')
    except Exception as e:
        return None, None


def download_youtube(url, user_id, message, format_id=None):
    """Download YouTube video"""
    download_path = None
    try:
        ensure_temp_dir()
        download_path = os.path.join(TEMP_DIR, f"youtube_{user_id}_{uuid.uuid4().hex[:8]}.mp4")
        
        if format_id:
            ydl_opts = {
                'format': format_id,
                'outtmpl': download_path,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'socket_timeout': 60
            }
        else:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': download_path,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 60
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(download_path):
            user_data[user_id] = {
                'file_path': download_path,
                'platform': 'youtube',
                'is_video': True
            }
            
            # Check file size (Telegram limit is 50MB for videos)
            file_size = os.path.getsize(download_path)
            
            markup = types.InlineKeyboardMarkup()
            btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
            markup.add(btn_audio)
            
            if file_size > 50 * 1024 * 1024:
                # Send as document if too large (>50MB)
                with open(download_path, 'rb') as video:
                    bot.send_document(message.chat.id, video, caption=f"📹 Video ({file_size / (1024*1024):.1f}MB)", reply_markup=markup)
            else:
                # Send as video if <50MB
                with open(download_path, 'rb') as video:
                    bot.send_video(message.chat.id, video, reply_markup=markup)
            
            # Increment download count
            increment_download_count(user_id)
            
            return True
        else:
            bot.reply_to(message, "❌ Video yuklab olinmadi")
            if download_path and os.path.exists(download_path):
                try:
                    os.remove(download_path)
                except:
                    pass
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            bot.reply_to(message, "❌ YouTube xatosi: Tarmoq muammosi. Iltimos, qayta urinib ko'ring.")
        else:
            bot.reply_to(message, f"❌ YouTube xatosi: {str(e)}")
        
        # Cleanup on error
        if download_path and os.path.exists(download_path):
            try:
                os.remove(download_path)
            except:
                pass
        return False


def extract_audio(user_id, message):
    """Extract audio from video"""
    audio_path = None
    try:
        if user_id not in user_data:
            bot.send_message(message.chat.id, "❌ Video topilmadi. Iltimos, yangi havola yuboring.")
            return
        
        user_info = user_data.get(user_id)
        if not user_info:
            bot.send_message(message.chat.id, "❌ Video topilmadi. Iltimos, yangi havola yuboring.")
            return
        
        video_path = user_info.get('file_path')
        if not video_path or not os.path.exists(video_path):
            bot.send_message(message.chat.id, "❌ Video topilmadi. Iltimos, yangi havola yuboring.")
            return
        
        loading_msg = bot.send_message(message.chat.id, "⏳ MP3 yuklanmoqda...")
        
        ensure_temp_dir()
        audio_path = os.path.join(TEMP_DIR, f"audio_{user_id}_{uuid.uuid4().hex[:8]}")
        
        # Extract audio using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path,
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_path])
            
            # Find the audio file
            audio_file = f"{audio_path}.mp3"
            
            if os.path.exists(audio_file):
                with open(audio_file, 'rb') as audio:
                    bot.send_audio(message.chat.id, audio)
                os.remove(audio_file)
            else:
                bot.send_message(message.chat.id, "❌ Audio ajratishda xatolik")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Audio xatosi: FFmpeg o'rnatilmagan bo'lishi mumkin")
        finally:
            # Cleanup audio file
            if audio_path and os.path.exists(f"{audio_path}.mp3"):
                try:
                    os.remove(f"{audio_path}.mp3")
                except:
                    pass
        
        # Cleanup video
        cleanup_user_files(user_id)
        
        # Delete loading message
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Audio xatosi: {str(e)}")
        # Cleanup on error
        if audio_path and os.path.exists(f"{audio_path}.mp3"):
            try:
                os.remove(f"{audio_path}.mp3")
            except:
                pass


@bot.message_handler(commands=['examples'])
def send_examples(message):
    # Register user
    register_user(message.from_user)
    
    examples_text = """
📝 <b>Misol havolalar:</b>

<b>📸 Instagram:</b>
• https://www.instagram.com/p/ABC123/
• https://www.instagram.com/reel/XYZ789/

<b>🎵 TikTok:</b>
• https://www.tiktok.com/@user/video/123
• https://vm.tiktok.com/ABC123/

<b>📌 Pinterest:</b>
• https://www.pinterest.com/pin/123456/
• https://pin.it/ABC123

<b>▶️ YouTube:</b>
• https://www.youtube.com/watch?v=ABC123
• https://youtu.be/ABC123

<i>Faqat havolani yuboring, bot avtomatik aniqlaydi!</i>
"""
    bot.send_message(message.chat.id, examples_text, parse_mode='HTML')

def show_admin_panel(message):
    """Show admin panel with statistics"""
    db = load_users_db()
    total_users = len(db)
    
    # Calculate statistics
    active_today = 0
    total_downloads = 0
    
    today = datetime.now().date()
    
    for user_id, user_info in db.items():
        total_downloads += user_info.get('total_downloads', 0)
        
        try:
            last_seen = datetime.fromisoformat(user_info.get('last_seen', ''))
            if last_seen.date() == today:
                active_today += 1
        except:
            pass
    
    admin_text = f"""
👑 <b>ADMIN PANEL</b>

📊 <b>Bot statistikasi:</b>

👥 Jami foydalanuvchilar: <b>{total_users}</b>
🟢 Bugun faol: <b>{active_today}</b>
📥 Jami yuklamalar: <b>{total_downloads}</b>
📁 Faol sessiyalar: <b>{len(user_data)}</b>

━━━━━━━━━━━━━━━━━

<b>Mavjud buyruqlar:</b>
/allusers - Barcha foydalanuvchilar
/broadcast - Xabar yuborish
/stats - To'liq statistika
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_users = types.InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")
    btn_stats = types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    btn_export = types.InlineKeyboardButton("📤 Export", callback_data="admin_export")
    btn_clean = types.InlineKeyboardButton("🗑 Tozalash", callback_data="admin_clean")
    markup.add(btn_users, btn_stats)
    markup.add(btn_export, btn_clean)
    
    bot.send_message(message.chat.id, admin_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    """Show all users (admin only)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    db = load_users_db()
    
    if not db:
        bot.reply_to(message, "📝 Hech qanday foydalanuvchi topilmadi")
        return
    
    users_list = "👥 <b>Barcha foydalanuvchilar:</b>\n\n"
    
    for i, (user_id, user_info) in enumerate(db.items(), 1):
        username = user_info.get('username', 'N/A')
        first_name = user_info.get('first_name', 'N/A')
        downloads = user_info.get('total_downloads', 0)
        
        users_list += f"{i}. "
        if username:
            users_list += f"@{username} "
        users_list += f"({first_name})\n"
        users_list += f"   ID: <code>{user_id}</code>\n"
        users_list += f"   📥 Yuklamalar: {downloads}\n\n"
        
        # Split message if too long
        if len(users_list) > 3500:
            bot.send_message(message.chat.id, users_list, parse_mode='HTML')
            users_list = ""
    
    if users_list:
        bot.send_message(message.chat.id, users_list, parse_mode='HTML')

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """Broadcast message to all users (admin only)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    # Check if message has text to broadcast
    msg = bot.reply_to(message, "📢 Xabar matnini yuboring (bekor qilish uchun /cancel):")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Process broadcast message"""
    if message.text == '/cancel':
        bot.reply_to(message, "❌ Bekor qilindi")
        return
    
    db = load_users_db()
    broadcast_text = message.text
    
    success_count = 0
    fail_count = 0
    
    status_msg = bot.reply_to(message, "📤 Xabar yuborilmoqda...")
    
    for user_id in db.keys():
        try:
            bot.send_message(int(user_id), broadcast_text, parse_mode='HTML')
            success_count += 1
        except:
            fail_count += 1
    
    result_text = f"""
✅ <b>Broadcast tugadi!</b>

📤 Yuborildi: {success_count}
❌ Xatolik: {fail_count}
👥 Jami: {len(db)}
"""
    
    bot.edit_message_text(result_text, message.chat.id, status_msg.message_id, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text in ["❓ Yordam", "📝 Misollar", "🌐 Platformalar", "📊 Statistika", "👑 Admin Panel"])
def handle_buttons(message):
    # Register user
    register_user(message.from_user)
    
    if message.text == "❓ Yordam":
        send_welcome(message)
    elif message.text == "📝 Misollar":
        send_examples(message)
    elif message.text == "🌐 Platformalar":
        platforms_text = """
🌐 <b>Qo'llab-quvvatlanadigan platformalar:</b>

📸 <b>Instagram</b>
├ Video yuklab olish
├ Rasm yuklab olish
└ MP3 audio ajratish

🎵 <b>TikTok</b>
├ Video yuklab olish
└ MP3 audio ajratish

📌 <b>Pinterest</b>
└ Rasm yuklab olish

▶️ <b>YouTube</b>
├ Turli sifatlar (144p-2160p)
├ Faqat MP3 yuklab olish
└ Video'dan MP3 ajratish

✅ Barcha platformalar avtomatik aniqlanadi!
"""
        bot.send_message(message.chat.id, platforms_text, parse_mode='HTML')
    elif message.text == "📊 Statistika":
        db = load_users_db()
        user_info = db.get(str(message.from_user.id), {})
        downloads = user_info.get('total_downloads', 0)
        
        stats_text = f"""
📊 <b>Sizning statistikangiz</b>

👤 User ID: <code>{message.from_user.id}</code>
📥 Yuklamalar soni: {downloads}
🤖 Bot versiya: 2.0

<i>Bot to'liq ishlamoqda!</i>
"""
        bot.send_message(message.chat.id, stats_text, parse_mode='HTML')
    elif message.text == "👑 Admin Panel":
        if is_admin(message.from_user.id):
            show_admin_panel(message)
        else:
            bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle incoming URLs"""
    url = message.text.strip()
    user_id = message.from_user.id
    
    # Check if it's a URL
    if not url.startswith(('http://', 'https://')):
        bot.reply_to(message, "❌ Iltimos, to'liq havolani yuboring (http:// yoki https:// bilan)")
        return
    
    # Detect platform
    platform, platform_name = detect_platform(url)
    
    if not platform:
        bot.reply_to(message, "❌ Qo'llab-quvvatlanmaydi. Faqat Instagram, TikTok, Pinterest yoki YouTube havolalarini yuboring.\n\n💡 /examples - misol havolalar")
        return
    
    # Show platform detection
    detect_msg = bot.send_message(message.chat.id, f"✅ {platform_name} aniqlandi!")
    
    # Cleanup old files
    cleanup_user_files(user_id)
    
    # Send loading message
    loading_msg = bot.send_message(message.chat.id, f"⏳ {platform_name} dan yuklanmoqda...")
    
    success = False
    
    try:
        # Delete detection message
        try:
            bot.delete_message(message.chat.id, detect_msg.message_id)
        except:
            pass
        
        if platform == 'instagram':
            success = download_instagram(url, user_id, message)
        elif platform == 'tiktok':
            success = download_tiktok(url, user_id, message)
        elif platform == 'pinterest':
            success = download_pinterest(url, user_id, message)
        elif platform == 'youtube':
            # Get available formats
            formats, title = get_youtube_formats(url)
            
            if formats:
                # Store URL for later use
                user_data[user_id] = {
                    'url': url,
                    'platform': 'youtube',
                    'formats': formats
                }
                
                # Create quality selection keyboard
                markup = types.InlineKeyboardMarkup(row_width=2)
                
                # Sort qualities
                quality_order = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']
                sorted_qualities = [q for q in quality_order if q in formats]
                
                buttons = []
                for quality in sorted_qualities:
                    btn = types.InlineKeyboardButton(
                        f"📹 {quality}",
                        callback_data=f"yt_quality_{quality}_{user_id}"
                    )
                    buttons.append(btn)
                
                # Add MP3 only button
                btn_mp3 = types.InlineKeyboardButton(
                    "🎵 Faqat MP3",
                    callback_data=f"yt_mp3only_{user_id}"
                )
                buttons.append(btn_mp3)
                
                # Add buttons to markup
                for i in range(0, len(buttons), 2):
                    if i + 1 < len(buttons):
                        markup.row(buttons[i], buttons[i + 1])
                    else:
                        markup.row(buttons[i])
                
                bot.send_message(
                    message.chat.id,
                    f"🎬 <b>{title}</b>\n\n📊 Sifatni tanlang yoki faqat audio yuklab oling:",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                success = True
            else:
                bot.reply_to(message, "❌ Video formatlarini olishda xatolik")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")
    
    # Delete loading message
    try:
        bot.delete_message(message.chat.id, loading_msg.message_id)
    except:
        pass


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle button callbacks"""
    try:
        user_id = call.from_user.id
        
        # Answer callback immediately to prevent timeout
        bot.answer_callback_query(call.id)
        
        if call.data.startswith("extract_audio_"):
            extract_audio(user_id, call.message)
            
        elif call.data.startswith("yt_quality_"):
            # Extract quality and user_id
            parts = call.data.split("_")
            quality = parts[2]
            stored_user_id = int(parts[3])
            
            if stored_user_id != user_id:
                bot.send_message(call.message.chat.id, "❌ Bu sizning havolangiz emas")
                return
            
            if user_id not in user_data:
                bot.send_message(call.message.chat.id, "❌ Ma'lumot topilmadi")
                return
            
            url = user_data[user_id].get('url')
            formats = user_data[user_id].get('formats')
            format_id = formats.get(quality)
            
            loading_msg = bot.send_message(call.message.chat.id, f"⏳ {quality} video yuklanmoqda...")
            
            success = download_youtube(url, user_id, call.message, format_id)
            
            try:
                bot.delete_message(call.message.chat.id, loading_msg.message_id)
            except:
                pass
                
        elif call.data.startswith("yt_mp3only_"):
            stored_user_id = int(call.data.split("_")[2])
            
            if stored_user_id != user_id:
                bot.send_message(call.message.chat.id, "❌ Bu sizning havolangiz emas")
                return
            
            if user_id not in user_data:
                bot.send_message(call.message.chat.id, "❌ Ma'lumot topilmadi")
                return
            
            url = user_data[user_id].get('url')
            
            loading_msg = bot.send_message(call.message.chat.id, "⏳ MP3 yuklanmoqda...")
            
            try:
                audio_path = os.path.join(TEMP_DIR, f"yt_audio_{user_id}_{uuid.uuid4().hex[:8]}")
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': audio_path,
                    'quiet': True,
                    'no_warnings': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Find the audio file
                audio_file = f"{audio_path}.mp3"
                
                if os.path.exists(audio_file):
                    with open(audio_file, 'rb') as audio:
                        bot.send_audio(call.message.chat.id, audio)
                    os.remove(audio_file)
                    cleanup_user_files(user_id)
                else:
                    bot.send_message(call.message.chat.id, "❌ Audio yuklab olinmadi")
                
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ MP3 xatosi: {str(e)}")
            
            try:
                bot.delete_message(call.message.chat.id, loading_msg.message_id)
            except:
                pass
        
        # Admin panel callbacks
        elif call.data == "admin_users":
            if not is_admin(user_id):
                bot.send_message(call.message.chat.id, "❌ Sizda admin huquqi yo'q!")
                return
            
            db = load_users_db()
            total_users = len(db)
            
            bot.send_message(call.message.chat.id, f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n\n/allusers - batafsil ro'yxat", parse_mode='HTML')
        
        elif call.data == "admin_stats":
            if not is_admin(user_id):
                bot.send_message(call.message.chat.id, "❌ Sizda admin huquqi yo'q!")
                return
            
            db = load_users_db()
            total_users = len(db)
            total_downloads = sum(user.get('total_downloads', 0) for user in db.values())
            
            # Calculate active users by time periods
            now = datetime.now()
            active_today = 0
            active_week = 0
            active_month = 0
            
            for user_info in db.values():
                try:
                    last_seen = datetime.fromisoformat(user_info.get('last_seen', ''))
                    days_diff = (now - last_seen).days
                    
                    if days_diff == 0:
                        active_today += 1
                    if days_diff <= 7:
                        active_week += 1
                    if days_diff <= 30:
                        active_month += 1
                except:
                    pass
            
            stats_text = f"""
📊 <b>To'liq statistika</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {total_users}
├ Bugun faol: {active_today}
├ Hafta: {active_week}
└ Oy: {active_month}

📥 <b>Yuklamalar:</b>
├ Jami: {total_downloads}
└ O'rtacha: {total_downloads / total_users if total_users > 0 else 0:.1f} / foydalanuvchi

📁 <b>Faol sessiyalar:</b> {len(user_data)}
"""
            bot.send_message(call.message.chat.id, stats_text, parse_mode='HTML')
        
        elif call.data == "admin_export":
            if not is_admin(user_id):
                bot.send_message(call.message.chat.id, "❌ Sizda admin huquqi yo'q!")
                return
            
            try:
                with open(USERS_DB_FILE, 'rb') as f:
                    bot.send_document(call.message.chat.id, f, caption="📊 Foydalanuvchilar bazasi")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Export xatosi: {str(e)}")
        
        elif call.data == "admin_clean":
            if not is_admin(user_id):
                bot.send_message(call.message.chat.id, "❌ Sizda admin huquqi yo'q!")
                return
            
            # Clean temp files
            try:
                for file in os.listdir(TEMP_DIR):
                    file_path = os.path.join(TEMP_DIR, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except:
                        pass
                
                bot.send_message(call.message.chat.id, "🗑 Vaqtinchalik fayllar tozalandi!")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Xato: {str(e)}")
                
    except Exception as e:
        try:
            bot.send_message(call.message.chat.id, f"❌ Xatolik: {str(e)}")
        except:
            pass


if __name__ == '__main__':
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
