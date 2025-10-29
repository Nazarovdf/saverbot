import telebot
import instaloader
import yt_dlp
import os
import json
from datetime import datetime
from telebot import types
from dotenv import load_dotenv
from moviepy import VideoFileClip
import shutil

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
if BOT_TOKEN:
    BOT_TOKEN = BOT_TOKEN.strip()

ADMIN_ID_STR = os.getenv('ADMIN_ID', '0')
if ADMIN_ID_STR:
    ADMIN_ID_STR = ADMIN_ID_STR.strip()

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except:
    ADMIN_ID = 0

print(f"Bot started. Admin ID: {ADMIN_ID}")

bot = telebot.TeleBot(BOT_TOKEN)

# User data storage (for MP3 extraction)
user_data = {}

# Users database file
USERS_DB_FILE = "users_db.json"

loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=True,  # Enable for carousel
    download_video_thumbnails=False,
    save_metadata=False,
)


# Database functions
def load_users_db():
    """Load users database"""
    if os.path.exists(USERS_DB_FILE):
        try:
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users_db(db):
    """Save users database"""
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def register_user(user):
    """Register or update user"""
    db = load_users_db()
    user_id_str = str(user.id)
    
    if user_id_str not in db:
        db[user_id_str] = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'total_downloads': 0
        }
    else:
        db[user_id_str]['last_seen'] = datetime.now().isoformat()
    
    save_users_db(db)

def increment_download_count(user_id):
    """Increment user download count"""
    db = load_users_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]['total_downloads'] = db[user_id_str].get('total_downloads', 0) + 1
        save_users_db(db)

def is_admin(user_id):
    """Check if user is admin"""
    return ADMIN_ID != 0 and user_id == ADMIN_ID

def cleanup_all_folders():
    """Cleanup all temporary Instagram folders"""
    try:
        for item in os.listdir('.'):
            if os.path.isdir(item) and len(item) == 11:  # Instagram shortcode length
                try:
                    for f in os.listdir(item):
                        os.remove(os.path.join(item, f))
                    os.rmdir(item)
                except:
                    pass
    except:
        pass


# Platform detection
def detect_platform(url):
    """Detect which platform the URL belongs to"""
    url_lower = url.lower()
    if 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    return None


# start bosilganda
@bot.message_handler(commands=["start", "help"])
def start(message):
    register_user(message.from_user)
    
    welcome_text = """
🎬 <b>Media Downloader Bot</b>

<b>Qo'llab-quvvatlanadigan platformalar:</b>
📸 Instagram - video/rasm + MP3
🎵 TikTok - video + MP3
▶️ YouTube - video (turli sifatlar) + MP3

Havola yuboring! 🚀
"""
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📖 Yordam"))
    
    if is_admin(message.from_user.id):
        markup.add(types.KeyboardButton("👑 Admin Panel"))
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)


# Instagram download (original logic - WORKS!)
def download_instagram(url, user_id, message):
    """Download Instagram video/image"""
    shortcode = None
    loading_msg = None
    try:
        # Extract shortcode
        try:
            shortcode = url.split("/")[-2]
            if not shortcode:
                shortcode = url.split("/")[-3]
        except IndexError:
            bot.reply_to(message, "❌ Link noto'g'ri")
            return
        
        loading_msg = bot.send_message(message.chat.id, "⏳ Instagram yuklanmoqda...")
        
        # Download post
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)
        
        # Get caption
        caption = post.caption if post.caption else "📸 Instagram"
        if len(caption) > 1000:
            caption = caption[:997] + "..."
        
        # Find all media files
        video_files = []
        photo_files = []
        for file in os.listdir(shortcode):
            file_path = os.path.join(shortcode, file)
            if file.endswith(".mp4"):
                video_files.append(file_path)
            elif file.endswith((".jpg", ".png")):
                photo_files.append(file_path)
        
        # Send media
        if video_files:
            # Send first video with buttons
            with open(video_files[0], "rb") as video:
                markup = types.InlineKeyboardMarkup()
                btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
                btn_caption = types.InlineKeyboardButton("📝 Description", callback_data=f"show_caption_{user_id}")
                markup.row(btn_audio, btn_caption)
                try:
                    bot.send_video(message.chat.id, video, reply_markup=markup)
                except:
                    video.seek(0)
                    bot.send_video(message.chat.id, video, reply_markup=markup)
            
            # Send other videos if any
            for video_path in video_files[1:]:
                with open(video_path, "rb") as video:
                    bot.send_video(message.chat.id, video)
            
            # Store for MP3 and caption
            user_data[user_id] = {
                'file_path': video_files[0],
                'folder_path': shortcode,
                'platform': 'instagram',
                'caption': caption
            }
            
        elif photo_files:
            # Send all photos
            if len(photo_files) == 1:
                # Single photo with caption
                with open(photo_files[0], "rb") as photo:
                    markup = types.InlineKeyboardMarkup()
                    btn_caption = types.InlineKeyboardButton("📝 Description", callback_data=f"show_caption_{user_id}")
                    markup.add(btn_caption)
                    try:
                        bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup)
                    except:
                        photo.seek(0)
                        bot.send_photo(message.chat.id, photo, reply_markup=markup)
                    
                    # Store caption
                    user_data[user_id] = {
                        'folder_path': shortcode,
                        'platform': 'instagram',
                        'caption': caption
                    }
            else:
                # Multiple photos (carousel)
                for i, photo_path in enumerate(photo_files):
                    with open(photo_path, "rb") as photo:
                        if i == 0:
                            # First photo with description button
                            markup = types.InlineKeyboardMarkup()
                            btn_caption = types.InlineKeyboardButton("📝 Description", callback_data=f"show_caption_{user_id}")
                            markup.add(btn_caption)
                            bot.send_photo(message.chat.id, photo, caption=f"📸 {i+1}/{len(photo_files)}", reply_markup=markup)
                            
                            # Store caption
                            user_data[user_id] = {
                                'folder_path': shortcode,
                                'platform': 'instagram',
                                'caption': caption
                            }
                        else:
                            bot.send_photo(message.chat.id, photo, caption=f"📸 {i+1}/{len(photo_files)}")
            
            # Cleanup immediately for photos
            try:
                shutil.rmtree(shortcode, ignore_errors=True)
            except:
                pass
        else:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, "❌ Media topilmadi")
            return
        
        # Delete loading message
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        # Increment counter
        increment_download_count(user_id)
        
        # Cleanup all shortcode folders
        cleanup_all_folders()
    
    except Exception as e:
        if loading_msg:
            try:
                bot.delete_message(message.chat.id, loading_msg.message_id)
            except:
                pass
        bot.reply_to(message, "❌ Instagram yuklab olinmadi")
        
        # Cleanup on error
        if shortcode and os.path.exists(shortcode):
            try:
                for f in os.listdir(shortcode):
                    os.remove(os.path.join(shortcode, f))
                os.rmdir(shortcode)
            except:
                pass


# TikTok download
def download_tiktok(url, user_id, message):
    """Download TikTok video"""
    loading_msg = None
    download_path = None
    try:
        loading_msg = bot.send_message(message.chat.id, "⏳ TikTok yuklanmoqda...")
        download_path = f"tiktok_{user_id}.mp4"
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': download_path,
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(download_path):
            with open(download_path, 'rb') as video:
                markup = types.InlineKeyboardMarkup()
                btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
                markup.add(btn_audio)
                bot.send_video(message.chat.id, video, reply_markup=markup)
            
            # Store for MP3
            user_data[user_id] = {'file_path': download_path, 'platform': 'tiktok'}
            
            bot.delete_message(message.chat.id, loading_msg.message_id)
            increment_download_count(user_id)
        else:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, "❌ TikTok yuklab olinmadi")
    
    except Exception:
        if loading_msg:
            try:
                bot.delete_message(message.chat.id, loading_msg.message_id)
            except:
                pass
        bot.reply_to(message, "❌ TikTok yuklab olinmadi")
        if download_path and os.path.exists(download_path):
            os.remove(download_path)



# YouTube quality selection
def get_youtube_formats(url):
    """Get available formats for YouTube video"""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = {}
            for f in info['formats']:
                # Get formats with both video and audio, or at least video
                if f.get('vcodec') != 'none':
                    height = f.get('height')
                    if height and height >= 144:
                        quality = f"{height}p"
                        if quality not in formats:
                            formats[quality] = f['format_id']
            return formats, info.get('title', 'video')
    except:
        return None, None


# YouTube download
def download_youtube(url, user_id, message, format_id=None):
    """Download YouTube video"""
    loading_msg = None
    download_path = None
    try:
        loading_msg = bot.send_message(message.chat.id, "⏳ YouTube yuklanmoqda...")
        download_path = f"youtube_{user_id}.mp4"
        
        if format_id:
            ydl_opts = {
                'format': f'{format_id}+bestaudio/best[ext=m4a]/best',
                'outtmpl': download_path,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
            }
        else:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': download_path,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4'
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(download_path):
            file_size = os.path.getsize(download_path)
            markup = types.InlineKeyboardMarkup()
            btn_audio = types.InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"extract_audio_{user_id}")
            markup.add(btn_audio)
            
            with open(download_path, 'rb') as video:
                if file_size > 50 * 1024 * 1024:
                    # Send as document if >50MB
                    bot.send_document(message.chat.id, video, caption=f"📹 YouTube ({file_size/(1024*1024):.1f}MB)", reply_markup=markup)
                else:
                    bot.send_video(message.chat.id, video, reply_markup=markup)
            
            # Store for MP3
            user_data[user_id] = {'file_path': download_path, 'platform': 'youtube'}
            
            bot.delete_message(message.chat.id, loading_msg.message_id)
            increment_download_count(user_id)
        else:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, "❌ YouTube yuklab olinmadi")
    
    except Exception:
        if loading_msg:
            try:
                bot.delete_message(message.chat.id, loading_msg.message_id)
            except:
                pass
        bot.reply_to(message, "❌ YouTube yuklab olinmadi")
        if download_path and os.path.exists(download_path):
            os.remove(download_path)


# MP3 extraction with MoviePy
def extract_audio(user_id, message):
    """Extract MP3 from video using MoviePy"""
    loading_msg = None
    audio_path = None
    video_clip = None
    try:
        if user_id not in user_data:
            bot.send_message(message.chat.id, "❌ Video topilmadi. Yangi havola yuboring.")
            return
        
        video_path = user_data[user_id].get('file_path')
        if not video_path or not os.path.exists(video_path):
            bot.send_message(message.chat.id, "❌ Video topilmadi. Yangi havola yuboring.")
            return
        
        loading_msg = bot.send_message(message.chat.id, "⏳ MP3 yuklanmoqda...")
        audio_path = f"audio_{user_id}.mp3"
        
        # Extract audio using MoviePy
        video_clip = VideoFileClip(video_path)
        video_clip.audio.write_audiofile(audio_path, logger=None)
        video_clip.close()
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            with open(audio_path, 'rb') as audio:
                bot.send_audio(message.chat.id, audio)
            
            # Cleanup audio file
            os.remove(audio_path)
            
            # Cleanup video after MP3 (videodownloader.py style)
            folder = user_data[user_id].get('folder_path')
            if folder and os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)
            elif video_path and os.path.exists(video_path) and os.path.isfile(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass
            
            # Cleanup all remaining folders
            cleanup_all_folders()
            
            bot.delete_message(message.chat.id, loading_msg.message_id)
        else:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, "❌ MP3 yuklab olinmadi")
    
    except Exception as e:
        if video_clip:
            try:
                video_clip.close()
            except:
                pass
        
        if loading_msg:
            try:
                bot.delete_message(message.chat.id, loading_msg.message_id)
            except:
                pass
        
        bot.reply_to(message, f"❌ MP3 xatosi: Video faylida audio yo'q yoki fayl buzilgan")
        
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass


# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        
        # Admin panel callbacks
        if call.data == "admin_users_list":
            if is_admin(user_id):
                show_all_users(call.message)
            return
        
        if call.data == "admin_broadcast":
            if is_admin(user_id):
                bot.send_message(call.message.chat.id, "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:")
                bot.register_next_step_handler(call.message, send_broadcast)
            return
        
        if call.data.startswith("extract_audio_"):
            extract_audio(user_id, call.message)
        
        elif call.data.startswith("show_caption_"):
            if user_id in user_data:
                caption = user_data[user_id].get('caption', 'Caption topilmadi')
                bot.send_message(call.message.chat.id, f"📝 <b>Description:</b>\n\n{caption}", parse_mode='HTML')
            else:
                bot.send_message(call.message.chat.id, "❌ Caption topilmadi")
        
        elif call.data.startswith("yt_quality_"):
            parts = call.data.split("_")
            quality = parts[2]
            stored_user_id = int(parts[3])
            
            if stored_user_id != user_id:
                return
            
            if user_id not in user_data:
                return
            
            url = user_data[user_id].get('url')
            formats = user_data[user_id].get('formats')
            format_id = formats.get(quality)
            
            download_youtube(url, user_id, call.message, format_id)
        
        elif call.data.startswith("yt_mp3only_"):
            stored_user_id = int(call.data.split("_")[2])
            
            if stored_user_id != user_id:
                return
            
            if user_id not in user_data:
                return
            
            url = user_data[user_id].get('url')
            loading_msg = bot.send_message(call.message.chat.id, "⏳ MP3 yuklanmoqda...")
            audio_path = f"yt_audio_{user_id}"
            
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': audio_path,
                    'quiet': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                audio_file = f"{audio_path}.mp3"
                if os.path.exists(audio_file):
                    with open(audio_file, 'rb') as audio:
                        bot.send_audio(call.message.chat.id, audio)
                    os.remove(audio_file)
                
                bot.delete_message(call.message.chat.id, loading_msg.message_id)
            except:
                bot.delete_message(call.message.chat.id, loading_msg.message_id)
                bot.send_message(call.message.chat.id, "❌ MP3 yuklab olinmadi")
    except:
        pass


# Admin Panel
def show_admin_panel(message):
    """Show admin panel"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    db = load_users_db()
    total_users = len(db)
    total_downloads = sum(user.get('total_downloads', 0) for user in db.values())
    
    now = datetime.now()
    active_today = 0
    active_week = 0
    
    for user_info in db.values():
        try:
            last_seen = datetime.fromisoformat(user_info.get('last_seen', ''))
            days_diff = (now - last_seen).days
            if days_diff == 0:
                active_today += 1
            if days_diff <= 7:
                active_week += 1
        except:
            pass
    
    admin_text = f"""
👑 <b>Admin Panel</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {total_users}
├ Bugun faol: {active_today}
└ Hafta: {active_week}

📥 <b>Yuklamalar:</b>
├ Jami: {total_downloads}
└ O'rtacha: {total_downloads / total_users if total_users > 0 else 0:.1f} / user

📁 <b>Faol sessiyalar:</b> {len(user_data)}
"""
    
    markup = types.InlineKeyboardMarkup()
    btn_users = types.InlineKeyboardButton("👥 Barcha foydalanuvchilar", callback_data="admin_users_list")
    btn_broadcast = types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    markup.row(btn_users)
    markup.row(btn_broadcast)
    
    bot.send_message(message.chat.id, admin_text, parse_mode='HTML', reply_markup=markup)


# Admin commands
@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    """Show all users (admin only)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    db = load_users_db()
    if not db:
        bot.reply_to(message, "Hozircha foydalanuvchilar yo'q")
        return
    
    users_text = "👥 <b>Barcha foydalanuvchilar:</b>\n\n"
    for i, (user_id, user_info) in enumerate(list(db.items())[:50], 1):
        username = user_info.get('username', 'N/A')
        first_name = user_info.get('first_name', 'N/A')
        downloads = user_info.get('total_downloads', 0)
        users_text += f"{i}. @{username} ({first_name}) - {downloads} yuklamalar\n"
    
    if len(db) > 50:
        users_text += f"\n... va yana {len(db) - 50} foydalanuvchi"
    
    bot.send_message(message.chat.id, users_text, parse_mode='HTML')


@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """Broadcast message to all users (admin only)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    bot.reply_to(message, "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:")
    bot.register_next_step_handler(message, send_broadcast)


def send_broadcast(message):
    """Send broadcast message"""
    db = load_users_db()
    success = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, "📢 Broadcast boshlandi...")
    
    for user_id in db.keys():
        try:
            bot.send_message(int(user_id), message.text)
            success += 1
        except:
            failed += 1
    
    bot.edit_message_text(
        f"✅ Broadcast tugadi!\n\nMuvaffaqiyatli: {success}\nXato: {failed}",
        message.chat.id,
        status_msg.message_id
    )


@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Show detailed statistics (admin only)"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Sizda admin huquqi yo'q!")
        return
    
    show_admin_panel(message)


# Main message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    register_user(message.from_user)
    
    text = message.text
    user_id = message.from_user.id
    
    # Check for buttons
    if text == "📖 Yordam":
        bot.reply_to(message, "Havola yuboring: Instagram, TikTok yoki YouTube")
        return
    
    if text == "👑 Admin Panel" and is_admin(user_id):
        show_admin_panel(message)
        return
    
    # Detect platform
    platform = detect_platform(text)
    
    if platform == 'instagram':
        download_instagram(text, user_id, message)
    elif platform == 'tiktok':
        download_tiktok(text, user_id, message)
    elif platform == 'youtube':
        # Show quality selection
        formats, title = get_youtube_formats(text)
        if formats:
            user_data[user_id] = {
                'url': text,
                'formats': formats
            }
            
            markup = types.InlineKeyboardMarkup()
            buttons = []
            for quality in sorted(formats.keys(), key=lambda x: int(x[:-1]), reverse=True):
                btn = types.InlineKeyboardButton(quality, callback_data=f"yt_quality_{quality}_{user_id}")
                buttons.append(btn)
            
            btn_mp3 = types.InlineKeyboardButton("🎵 Faqat MP3", callback_data=f"yt_mp3only_{user_id}")
            buttons.append(btn_mp3)
            
            for i in range(0, len(buttons), 2):
                if i + 1 < len(buttons):
                    markup.row(buttons[i], buttons[i + 1])
                else:
                    markup.row(buttons[i])
            
            bot.send_message(message.chat.id, f"🎬 <b>{title}</b>\n\nSifatni tanlang:", reply_markup=markup, parse_mode='HTML')
        else:
            bot.reply_to(message, "❌ YouTube yuklab olinmadi")
    else:
        bot.reply_to(message, "❌ Noma'lum havola. Instagram, TikTok yoki YouTube havolasini yuboring.")


bot.infinity_polling()
