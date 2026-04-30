# 🤖 ForexBot Pro — Telegram Trading Journal Bot

A complete Forex trading journal and analytics bot for Telegram.
Sab kuch Hindi + English mein available hai!

---

## 📁 Project Structure

```
forex-trading-bot/
├── bot.py                  # Main entry point
├── config.py               # All settings & constants
├── database.py             # SQLite operations
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── handlers/
│   ├── trade_logger.py     # Trade add/edit/delete/export
│   ├── analytics.py        # Stats, reports, equity curve
│   ├── calculator.py       # Lot size, P&L, margin calculators
│   ├── alerts.py           # Price alerts & reminders
│   ├── goals.py            # Goal setting & streak tracking
│   ├── journal.py          # Trading journal & ideas
│   └── risk.py             # Drawdown & risk management
└── utils/
    ├── charts.py           # Matplotlib chart generation
    ├── formatters.py       # Telegram message formatting
    └── validators.py       # Input validation helpers
```

---

## ⚙️ Setup Guide (English)

### 1. Prerequisites
- Python 3.10 or higher
- A Telegram account

### 2. Create Your Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** you receive

### 3. Get Your User ID
1. Search for **@userinfobot** on Telegram
2. Send `/start` — it will show your numeric User ID

### 4. Clone & Install

```bash
# Clone or download the project
cd forex-trading-bot

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
BOT_TOKEN=your_actual_bot_token
ADMIN_USER_ID=your_telegram_user_id
```

### 6. Run the Bot

```bash
python bot.py
```

You should see: `🤖 ForexBot Pro is running!`

Open Telegram, find your bot, and send `/start`.

---

## ⚙️ Setup Guide (Hindi)

### 1. Requirements
- Python 3.10 ya usse upar
- Telegram account

### 2. Bot Banayein
1. Telegram mein **@BotFather** search karein
2. `/newbot` send karein aur steps follow karein
3. **Bot Token** copy karein

### 3. User ID Pata Karein
1. **@userinfobot** search karein Telegram mein
2. `/start` bhejein — apna numeric User ID milega

### 4. Install Karein

```bash
cd forex-trading-bot
python -m venv venv
source venv/bin/activate   # Linux/Mac par
venv\Scripts\activate      # Windows par

pip install -r requirements.txt
```

### 5. .env Configure Karein

```bash
cp .env.example .env
# .env file mein apna BOT_TOKEN aur ADMIN_USER_ID daalen
```

### 6. Bot Chalayein

```bash
python bot.py
```

`🤖 ForexBot Pro is running!` dikhega — bot ready hai!

---

## 📋 All Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Full command list |
| **Trade Logging** | |
| `/addtrade` | New trade log karein |
| `/trades` | Recent trades dekhein |
| `/edittrade <id>` | Trade edit karein |
| `/deletetrade <id>` | Trade delete karein |
| **Analytics** | |
| `/stats` | Quick statistics |
| `/report` | Weekly/monthly report with chart |
| `/equity` | Equity curve graph |
| `/performance` | Strategy-wise breakdown |
| `/today` | Aaj ka summary |
| `/week` | Is week ki performance |
| `/month` | Monthly overview |
| **Calculators** | |
| `/lotsize` | Lot size calculator |
| `/pnl` | P&L calculator |
| `/margin <pair> <lot> <leverage>` | Margin calculator |
| `/risk <entry> <sl> <tp>` | Risk/Reward ratio |
| `/compound <bal> <pct> <months>` | Compound projections |
| `/pipvalue [pair] [lot]` | Pip value |
| `/breakeven <wr> <rr>` | Break-even analysis |
| **Goals** | |
| `/setgoal` | Goal set karein |
| `/goals` | Active goals dekhein |
| `/streak` | Win/loss streak |
| **Risk Management** | |
| `/drawdown` | Current drawdown |
| `/maxloss` | Max loss limit set karein |
| `/riskcheck` | Full risk assessment |
| **Alerts** | |
| `/setalert` | Price alert set karein |
| `/myalerts` | Active alerts |
| `/delalert <id>` | Alert delete karein |
| `/sessions` | Market session timings (IST) |
| `/reminder` | Custom reminder |
| **Journal** | |
| `/journal` | Daily journal entry |
| `/notes` | Past entries |
| `/idea` | Trade idea save karein |
| **Data** | |
| `/export` | CSV export |
| `/backup` | Database backup |
| **Settings** | |
| `/settings` | Bot settings menu |
| `/account` | Account setup |

### ⚡ Quick Trade Format
```
EURUSD BUY 1.0850 SL:1.0830 TP:1.0890
GBPJPY SELL 185.50 SL:186.00 TP:184.50 LOT:0.05
```

---

## 🔧 Troubleshooting

**Bot respond nahi kar raha?**
- Check karein `.env` mein `BOT_TOKEN` sahi hai
- Bot ko Telegram mein `/start` bhejein

**Database error?**
- `data/` folder exist karta hai check karein
- `python bot.py` dobara run karein (auto-creates tables)

**Charts nahi ban rahe?**
- `pip install matplotlib` run karein
- `data/charts/` folder exist karna chahiye

**Import errors?**
- Virtual environment activate hai? (`source venv/bin/activate`)
- `pip install -r requirements.txt` dobara run karein

---

## 📄 License
MIT — Free to use and modify.

*ForexBot Pro v1.0 — Built for Smart Traders 🚀*
