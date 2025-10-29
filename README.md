# 🎬 Media Downloader Bot

## 🔧 Yangi funksiyalar (v2.3):
- ✅ **MoviePy** - MP3 extraction (FFmpeg avtomatik)
- ✅ Instagram Description button
- ✅ Auto cleanup all temporary folders
- ✅ YouTube katta hajm support
- ❌ Pinterest o'chirildi (muammolar tufayli)
- 🚂 Railway.com deployment optimized

Telegram bot for downloading media from Instagram, TikTok, and YouTube.

## ✨ Features

- 📸 **Instagram** - videos and images + MP3 extraction
- 🎵 **TikTok** - videos + MP3 extraction
- ▶️ **YouTube** - multiple qualities (144p-2160p) + MP3 extraction
- 🎵 **MoviePy** - MP3 extraction without manual FFmpeg setup
- 👑 **Admin Panel** - user statistics, broadcast messages
- 🌐 **Auto-detection** - just send a link!
- 🧹 **Auto cleanup** - no temporary files left behind

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Setup Bot Token
1. Create bot via [@BotFather](https://t.me/BotFather)
2. Copy `.env.example` to `.env`
3. Add your bot token:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id  # Optional - for admin panel
```

### 3. Run Bot
```bash
python bot.py
```

## 👑 Admin Panel

Set `ADMIN_ID` in `.env` to enable admin features:
- 👥 User statistics
- 📢 Broadcast messages
- 📤 Export database
- 🗑 Clean temp files

## 🌐 Deployment

### Railway.app (Recommended ✅)
1. Fork this repo
2. [railway.app](https://railway.app) → New Project
3. Deploy from GitHub repo
4. Add environment variables:
   - `BOT_TOKEN` = your_bot_token
   - `ADMIN_ID` = your_telegram_user_id
5. Deploy! (FFmpeg avtomatik o'rnatiladi via `nixpacks.toml`)

### Render.com
1. Fork this repo
2. Create account on [render.com](https://render.com)
3. New → Web Service → Connect GitHub
4. Set Environment Variables: `BOT_TOKEN`, `ADMIN_ID`
5. Deploy!

### VPS (Ubuntu)
```bash
git clone your-repo
cd instasaver

# Install dependencies
sudo apt update
sudo apt install ffmpeg libsm6 libxext6 -y
pip install -r requirements.txt

# Setup .env
cp .env.example .env
nano .env  # Add BOT_TOKEN and ADMIN_ID

# Run bot
python3 bot.py

# Or run in background:
nohup python3 bot.py &
```

## 📄 Litsenziya

MIT License

## 🤝 Hissa qo'shish

Pull request'lar qabul qilinadi. Katta o'zgarishlar uchun avval issue oching.

## 📧 Bog'lanish

Savollar yoki takliflar uchun issue oching yoki Telegram orqali bog'laning.

---

⭐ Agar loyiha foydali bo'lsa, star bering!
