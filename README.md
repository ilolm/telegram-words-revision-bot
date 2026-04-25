# 📚 Telegram Words Revision Bot

Minimal Telegram bot for spaced repetition using fixed intervals.


1. Learn new N amount of words that you keep somewhere, group them together.
2. Add a new deck into the bot.
3. Revise that group of words when the bot tells you to.

## ✨ Features
- ➕ Add word groups (“decks”)
- 📚 Daily review list based on intervals: **1, 3, 7, 12, 30 days**
- 📦 View all decks
- 🗑 Delete decks via selection
- 🔔 Daily reminder (10:00 server time)
- 👥 Multi-user support

## 🧠 How it works
Each deck has a creation date.
A deck is scheduled for review when:

days_passed ∈ [1, 3, 7, 12, 30]

## 📦 Requirements
- 🐍 Python 3.10+ (Not required if deployed via Docker)
- 🤖 Telegram bot token (via BotFather)

---

## 🚀 Run with Docker

### ▶️ Run 
```bash
sudo docker container run -itd \
    --name telegram-words-revision-bot \
    --restart unless-stopped \
    -v ./words.db:/app/words.db
    -e TG_BOT_TOKEN="PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE" \
    ilolm/telegram-words-revision-bot:latest
```

### 🔨 Manual Build
```bash
sudo docker image build . -t telegram-words-revision-bot
```

---

## ⚙️ Configuration

| Variable     | Required | Description            |
| ------------ | -------- | ---------------------- |
| TG_BOT_TOKEN | yes      | Telegram bot API token |

---
## 📜 License

MIT
