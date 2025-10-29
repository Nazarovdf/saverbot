# 🚀 GitHub Push Qo'llanmasi

## 1️⃣ Git Repository yaratish

```bash
# Git ni ishga tushirish
git init

# Fayllarni qo'shish
git add .

# Commit qilish
git commit -m "Initial commit: Media Downloader Bot"
```

## 2️⃣ GitHub repository yaratish

1. [GitHub.com](https://github.com) ga kiring
2. "New repository" tugmasini bosing
3. Repository nomi: `telegram-media-bot` (yoki boshqa nom)
4. **Private** yoki **Public** tanlang
5. "Create repository" ni bosing

## 3️⃣ GitHub ga push qilish

```bash
# Remote repository qo'shish
git remote add origin https://github.com/yourusername/telegram-media-bot.git

# Main branchga o'tish
git branch -M main

# Push qilish
git push -u origin main
```

**Agar token kerak bo'lsa:**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`
4. Copy token
5. Push da parol so'ralsa, tokenni kiriting

---

# 🌐 Deploy Qilish (Render.com)

## Render.com da deploy:

1. **GitHub push qilganingizdan keyin:**
   - [render.com](https://render.com) ga kiring
   - "New +" → "Web Service"
   - GitHub reposini connect qiling

2. **Sozlash:**
   - Name: `telegram-media-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`

3. **Environment Variables qo'shish:**
   - `BOT_TOKEN` = sizning bot tokeningiz
   - `ADMIN_ID` = sizning user ID

4. **Deploy!**
   - "Create Web Service" ni bosing
   - 2-3 daqiqa kutasiz
   - Bot avtomatik ishga tushadi!

✅ **Tayyor!** Botingiz 24/7 ishlaydi!

---

## ⚡ Tezkor deploy (Alternative)

### Railway.app:
```bash
# Railway CLI o'rnatish
npm i -g @railway/cli

# Login
railway login

# Proyekt yaratish
railway init

# Environment variables
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_ID=your_id

# Deploy
railway up
```

### Heroku:
```bash
# Heroku CLI o'rnatilgan bo'lishi kerak
heroku login

# App yaratish
heroku create telegram-media-bot

# Environment variables
heroku config:set BOT_TOKEN=your_token
heroku config:set ADMIN_ID=your_id

# Deploy
git push heroku main
```

---

## 💡 Maslahatlar

1. **Bot tokenni hech qachon GitHub'ga push qilmang!**
   - `.env` fayli `.gitignore` da bor
   - Faqat `.env.example` ni push qiling

2. **Deployment muvaffaqiyatli bo'ldi, lekin bot ishlamayapti?**
   - Environment variables to'g'ri kiritilganini tekshiring
   - Logs ni tekshiring (Render/Railway dashboard da)

3. **FFmpeg kerakmi?**
   - Render.com: Avtomatik o'rnatiladi
   - Heroku: Buildpack qo'shing: `heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git`

4. **Free plan yetarli?**
   - Ha! Render/Railway free plan oddiy botlar uchun yetarli
   - 500 user gacha muammosiz ishlaydi

---

## 🎯 Keyingi qadamlar

1. ✅ GitHub'ga push qilish
2. ✅ Render.com da deploy qilish
3. ✅ Bot ishlayotganini tekshirish
4. 📊 Statistikani kuzatish (Admin panel)
5. 🎉 Foydalanuvchilarga ulashing!

**Omad!** 🚀
