"""
🤖 FOREX TRADING TELEGRAM BOT
Main Entry Point
Author: ForexBot Pro
Version: 1.0.0
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import Config
from database import Database
from handlers.trade_logger import TradeLogger
from handlers.analytics import Analytics
from handlers.calculator import Calculator
from handlers.alerts import Alerts
from handlers.goals import Goals
from handlers.journal import Journal
from handlers.risk import RiskManager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - Welcome message"""
    user = update.effective_user
    welcome_msg = f"""
🌟 *Namaste {user.first_name}! ForexBot Pro mein aapka swagat hai!* 🌟

━━━━━━━━━━━━━━━━━━━━━━
🤖 *Main aapki help karunga:*

📊 Trade log karne mein
📈 Performance analyze karne mein  
🧮 Calculators use karne mein
🎯 Goals set karne mein
⚠️ Risk manage karne mein
━━━━━━━━━━━━━━━━━━━━━━

👇 *Quick Start:*
• `/help` — Sare commands dekhein
• `/addtrade` — Pehla trade log karein
• `/stats` — Statistics dekhein

💡 *Tip:* Quick trade log ke liye type karein:
`EURUSD BUY 1.0850 SL:1.0830 TP:1.0890`

_ForexBot Pro v1.0 | Developed for Smart Traders_
"""
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comprehensive help with all commands"""
    help_text = """
📚 *FOREXBOT PRO — COMPLETE HELP GUIDE*

━━━━━━━━━━━━━━━━━━━━━━
📊 *PAGE 1: TRADE LOGGING*
━━━━━━━━━━━━━━━━━━━━━━
`/addtrade` — Naya trade log karein
`/trades` — Recent trades dekhein
`/edittrade` — Trade edit karein
`/deletetrade` — Trade delete karein

💡 *Quick Format:*
`EURUSD BUY 1.0850 SL:1.0830 TP:1.0890`

━━━━━━━━━━━━━━━━━━━━━━
📈 *PAGE 2: ANALYTICS*
━━━━━━━━━━━━━━━━━━━━━━
`/stats` — Quick statistics
`/report` — Weekly/Monthly report
`/equity` — Equity curve graph
`/performance` — Strategy breakdown
`/today` — Aaj ka summary
`/week` — Is week ki performance
`/month` — Monthly overview

━━━━━━━━━━━━━━━━━━━━━━
🧮 *PAGE 3: CALCULATORS*
━━━━━━━━━━━━━━━━━━━━━━
`/lotsize` — Lot size calculator
`/pnl` — P&L calculator
`/margin` — Margin calculator
`/risk` — Risk/Reward calculator
`/compound` — Compound projections
`/pipvalue` — Pip value calculator
`/breakeven` — Break-even calculator

━━━━━━━━━━━━━━━━━━━━━━
🎯 *PAGE 4: GOALS*
━━━━━━━━━━━━━━━━━━━━━━
`/setgoal` — Goal set karein
`/goals` — Current goals dekhein
`/streak` — Win/Loss streak

━━━━━━━━━━━━━━━━━━━━━━
⚠️ *PAGE 5: RISK MANAGEMENT*
━━━━━━━━━━━━━━━━━━━━━━
`/drawdown` — Drawdown tracker
`/maxloss` — Max loss limit set karein
`/riskcheck` — Risk assessment

━━━━━━━━━━━━━━━━━━━━━━
🔔 *PAGE 6: ALERTS*
━━━━━━━━━━━━━━━━━━━━━━
`/setalert` — Price alert set karein
`/myalerts` — Active alerts dekhein
`/delalert` — Alert delete karein
`/sessions` — Market session timings
`/reminder` — Custom reminder set

━━━━━━━━━━━━━━━━━━━━━━
📝 *PAGE 7: JOURNAL*
━━━━━━━━━━━━━━━━━━━━━━
`/journal` — Trading journal entry
`/notes` — Past entries dekhein
`/idea` — Trade idea save karein

━━━━━━━━━━━━━━━━━━━━━━
💾 *PAGE 8: DATA & EXPORT*
━━━━━━━━━━━━━━━━━━━━━━
`/export` — CSV mein export karein
`/backup` — Data backup lein
`/import` — Data import karein

━━━━━━━━━━━━━━━━━━━━━━
⚙️ *PAGE 9: SETTINGS*
━━━━━━━━━━━━━━━━━━━━━━
`/settings` — Bot settings
`/account` — Account details set
`/currency` — Base currency set
`/timezone` — Timezone set

_Type any command to get started!_ 🚀
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_quick_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quick trade format: EURUSD BUY 1.0850 SL:1.0830 TP:1.0890"""
    from utils.validators import parse_quick_trade
    from utils.formatters import format_trade_confirmation

    text = update.message.text.upper()
    trade_data = parse_quick_trade(text)

    if trade_data:
        db = Database()
        trade_id = db.add_trade(update.effective_user.id, trade_data)
        confirmation = format_trade_confirmation(trade_data, trade_id)
        await update.message.reply_text(confirmation, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "❓ Samajh nahi aaya. Trade log karne ke liye `/addtrade` use karein ya format:\n"
            "`EURUSD BUY 1.0850 SL:1.0830 TP:1.0890`",
            parse_mode="Markdown"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler"""
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Kuch problem hui. Please dobara try karein ya `/help` type karein."
        )


def main() -> None:
    """Main function to run the bot"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("❌ BOT_TOKEN environment variable set nahi hai!")

    # Initialize database
    db = Database()
    db.initialize()
    logger.info("✅ Database initialized")

    # Create application
    app = Application.builder().token(token).build()

    # Initialize handlers
    trade_logger = TradeLogger()
    analytics = Analytics()
    calculator = Calculator()
    alerts = Alerts()
    goals = Goals()
    journal = Journal()
    risk = RiskManager()

    # ═══ BASIC COMMANDS ═══
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # ═══ TRADE LOGGING ═══
    app.add_handler(trade_logger.get_add_trade_handler())
    app.add_handler(CommandHandler("trades", trade_logger.view_trades))
    app.add_handler(trade_logger.get_edit_trade_handler())
    app.add_handler(CommandHandler("deletetrade", trade_logger.delete_trade))

    # ═══ ANALYTICS ═══
    app.add_handler(CommandHandler("stats", analytics.quick_stats))
    app.add_handler(CommandHandler("report", analytics.detailed_report))
    app.add_handler(CommandHandler("equity", analytics.equity_curve))
    app.add_handler(CommandHandler("performance", analytics.strategy_performance))
    app.add_handler(CommandHandler("today", analytics.today_summary))
    app.add_handler(CommandHandler("week", analytics.week_summary))
    app.add_handler(CommandHandler("month", analytics.month_summary))

    # ═══ CALCULATORS ═══
    app.add_handler(calculator.get_lotsize_handler())
    app.add_handler(calculator.get_pnl_handler())
    app.add_handler(CommandHandler("margin", calculator.margin_calc))
    app.add_handler(CommandHandler("risk", calculator.risk_reward))
    app.add_handler(CommandHandler("compound", calculator.compound_calc))
    app.add_handler(CommandHandler("pipvalue", calculator.pip_value))
    app.add_handler(CommandHandler("breakeven", calculator.breakeven_calc))

    # ═══ GOALS ═══
    app.add_handler(goals.get_setgoal_handler())
    app.add_handler(CommandHandler("goals", goals.view_goals))
    app.add_handler(CommandHandler("streak", goals.view_streak))

    # ═══ RISK MANAGEMENT ═══
    app.add_handler(CommandHandler("drawdown", risk.drawdown_tracker))
    app.add_handler(risk.get_maxloss_handler())
    app.add_handler(CommandHandler("riskcheck", risk.risk_assessment))

    # ═══ ALERTS ═══
    app.add_handler(alerts.get_setalert_handler())
    app.add_handler(CommandHandler("myalerts", alerts.view_alerts))
    app.add_handler(CommandHandler("delalert", alerts.delete_alert))
    app.add_handler(CommandHandler("sessions", alerts.market_sessions))
    app.add_handler(alerts.get_reminder_handler())

    # ═══ JOURNAL ═══
    app.add_handler(journal.get_journal_handler())
    app.add_handler(CommandHandler("notes", journal.view_notes))
    app.add_handler(journal.get_idea_handler())

    # ═══ DATA EXPORT ═══
    app.add_handler(CommandHandler("export", trade_logger.export_trades))
    app.add_handler(CommandHandler("backup", trade_logger.backup_data))

    # ═══ SETTINGS ═══
    app.add_handler(CommandHandler("settings", settings_handler))
    app.add_handler(CommandHandler("account", account_handler))

    # ═══ CALLBACK QUERIES (Inline Buttons) ═══
    app.add_handler(CallbackQueryHandler(handle_callback))

    # ═══ QUICK TRADE FORMAT ═══
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_quick_trade
    ))

    # ═══ ERROR HANDLER ═══
    app.add_error_handler(error_handler)

    logger.info("🚀 ForexBot Pro starting...")
    print("🤖 ForexBot Pro is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("💰 Account Balance", callback_data="set_balance"),
         InlineKeyboardButton("🌍 Timezone", callback_data="set_timezone")],
        [InlineKeyboardButton("💱 Base Currency", callback_data="set_currency"),
         InlineKeyboardButton("📊 Default Risk %", callback_data="set_risk")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="set_notifications"),
         InlineKeyboardButton("📅 Report Day", callback_data="set_report_day")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ *Bot Settings*\n\nKya change karna chahte hain?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Account setup"""
    await update.message.reply_text(
        "💼 *Account Setup*\n\n"
        "Apna account balance enter karein (USD mein):\n"
        "Example: `10000`",
        parse_mode="Markdown"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set_balance":
        await query.message.reply_text("💰 Apna current balance enter karein (USD): ")
    elif data == "set_timezone":
        await query.message.reply_text("🌍 Timezone enter karein (e.g. `Asia/Kolkata`): ")
    elif data == "set_currency":
        await query.message.reply_text("💱 Base currency enter karein (e.g. `USD`, `INR`): ")
    elif data.startswith("del_trade_"):
        trade_id = int(data.split("_")[2])
        db = Database()
        db.delete_trade(trade_id, update.effective_user.id)
        await query.message.edit_text(f"✅ Trade #{trade_id} delete ho gaya!")
    elif data.startswith("confirm_"):
        await query.message.edit_text("✅ Action completed!")
    elif data == "cancel":
        await query.message.edit_text("❌ Action cancelled.")


if __name__ == "__main__":
    main()
