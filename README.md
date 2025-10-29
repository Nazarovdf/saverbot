# 🎬 Media Downloader Bot

Telegram bot for downloading media from Instagram, TikTok, Pinterest, and YouTube.

## ✨ Features

- 📸 **Instagram** - videos and images + MP3 extraction
- 🎵 **TikTok** - videos + MP3 extraction
- 📌 **Pinterest** - images
- ▶️ **YouTube** - multiple qualities (144p-2160p) + MP3 extraction
- 👑 **Admin Panel** - user statistics, broadcast messages
- 🌐 **Auto-detection** - just send a link!

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

### Render.com (Free & Easy)
1. Fork this repo
2. Create account on [render.com](https://render.com)
3. New → Web Service → Connect GitHub
4. Set Environment Variables: `BOT_TOKEN`, `ADMIN_ID`
5. Deploy!

### Railway.app
1. [railway.app](https://railway.app) → New Project
2. Deploy from GitHub repo
3. Add environment variables
4. Deploy

### VPS (Ubuntu)
```bash
git clone your-repo
cd instasaver
pip install -r requirements.txt
sudo apt install ffmpeg
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
