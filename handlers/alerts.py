"""
🔔 ALERTS & REMINDERS HANDLER
ForexBot Pro - Price Alerts & Market Sessions
"""

import logging
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    ContextTypes, filters
)
from config import ALERT_PAIR, ALERT_PRICE, ALERT_CONDITION, REMINDER_TEXT, REMINDER_TIME, MARKET_SESSIONS
from database import Database

logger = logging.getLogger(__name__)


class Alerts:
    """Price alerts and reminders"""

    def __init__(self):
        self.db = Database()

    def get_setalert_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("setalert", self.start_setalert)],
            states={
                ALERT_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.alert_pair)],
                ALERT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.alert_price)],
                ALERT_CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.alert_condition)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def get_reminder_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("reminder", self.start_reminder)],
            states={
                REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.reminder_text)],
                REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.reminder_time)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def start_setalert(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start price alert setup"""
        self.db.ensure_user(update.effective_user.id)
        await update.message.reply_text(
            "🔔 *Price Alert Set Karein*\n\n"
            "Currency pair enter karein:\nExample: `EURUSD`\n\n"
            "_/cancel se cancel karein_",
            parse_mode="Markdown"
        )
        return ALERT_PAIR

    async def alert_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pair = update.message.text.upper().strip()
        context.user_data["alert"] = {"pair": pair}
        await update.message.reply_text(
            f"✅ Pair: *{pair}*\n\nPrice level enter karein:\nExample: `1.0900`",
            parse_mode="Markdown"
        )
        return ALERT_PRICE

    async def alert_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            price = float(update.message.text.strip())
            context.user_data["alert"]["price"] = price
            await update.message.reply_text(
                f"✅ Price: *{price}*\n\nCondition select karein:\n"
                "`above` — Price is upar jayega tab alert\n"
                "`below` — Price neeche jayega tab alert",
                parse_mode="Markdown"
            )
            return ALERT_CONDITION
        except ValueError:
            await update.message.reply_text("❌ Valid price enter karein.", parse_mode="Markdown")
            return ALERT_PRICE

    async def alert_condition(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        condition = update.message.text.lower().strip()
        if condition not in ["above", "below"]:
            await update.message.reply_text("❌ Sirf `above` ya `below` enter karein.", parse_mode="Markdown")
            return ALERT_CONDITION

        alert = context.user_data["alert"]
        alert_id = self.db.add_alert(
            update.effective_user.id,
            alert["pair"],
            alert["price"],
            condition
        )

        cond_text = "📈 Upar jayega" if condition == "above" else "📉 Neeche jayega"

        await update.message.reply_text(
            f"✅ *Alert #{alert_id} Set Ho Gaya!*\n\n"
            f"💱 Pair: *{alert['pair']}*\n"
            f"💰 Price: *{alert['price']}*\n"
            f"🔔 Condition: *{cond_text}*\n\n"
            f"_Jab {alert['pair']} {condition} {alert['price']} hoga, aapko notification milegi!_",
            parse_mode="Markdown"
        )
        context.user_data.pop("alert", None)
        return ConversationHandler.END

    async def view_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """View all active alerts"""
        alerts = self.db.get_alerts(update.effective_user.id)

        if not alerts:
            await update.message.reply_text(
                "🔕 Koi active alert nahi hai!\n\n"
                "`/setalert` se price alert set karein.",
                parse_mode="Markdown"
            )
            return

        msg = "🔔 *Active Price Alerts*\n" + "━" * 24 + "\n\n"
        for alert in alerts:
            cond = "📈" if alert["condition"] == "above" else "📉"
            msg += (
                f"#{alert['id']} {cond} *{alert['pair']}* {alert['condition']} *{alert['price']}*\n"
                f"  _Set: {alert['created_at'][:10]}_\n\n"
            )

        msg += f"_Total: {len(alerts)} alerts_ | `/delalert <id>` se delete karein"
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def delete_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete an alert"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "🗑️ Alert delete karne ke liye:\n`/delalert <alert_id>`",
                parse_mode="Markdown"
            )
            return

        try:
            alert_id = int(args[0])
            success = self.db.delete_alert(alert_id, update.effective_user.id)
            if success:
                await update.message.reply_text(f"✅ Alert #{alert_id} delete ho gaya!")
            else:
                await update.message.reply_text(f"❌ Alert #{alert_id} nahi mila!")
        except ValueError:
            await update.message.reply_text("❌ Valid alert ID enter karein.")

    async def market_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show market session timings"""
        try:
            ist = pytz.timezone("Asia/Kolkata")
            utc = pytz.UTC
            now_utc = datetime.now(utc)
            now_ist = now_utc.astimezone(ist)

            msg = (
                f"🌍 *Market Sessions*\n"
                f"🕐 IST Time: *{now_ist.strftime('%H:%M')}*\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
            )

            sessions = {
                "Sydney 🇦🇺": {"open_ist": "05:30", "close_ist": "14:30"},
                "Tokyo 🇯🇵": {"open_ist": "05:30", "close_ist": "14:30"},
                "London 🇬🇧": {"open_ist": "13:30", "close_ist": "22:30"},
                "New York 🇺🇸": {"open_ist": "18:30", "close_ist": "03:30"},
            }

            overlaps = [
                ("Tokyo-Sydney", "05:30", "07:30"),
                ("London-Tokyo", "13:30", "14:30"),
                ("London-NY", "18:30", "22:30"),
            ]

            for session, times in sessions.items():
                msg += f"*{session}*\n"
                msg += f"  Open IST: `{times['open_ist']}` | Close: `{times['close_ist']}`\n\n"

            msg += "━━━━━━━━━━━━━━━━━━\n*🔥 Best Trading Overlaps (IST)*\n\n"
            for name, start, end in overlaps:
                msg += f"⚡ *{name}*: `{start}` — `{end}`\n"

            msg += "\n_London-NY overlap sabse zyada volatile hota hai!_ 💡"
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Sessions error: {e}")
            await update.message.reply_text("❌ Session info load nahi hui!")

    async def start_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start reminder setup"""
        await update.message.reply_text(
            "⏰ *Reminder Set Karein*\n\nReminder text enter karein:\nExample: `NFP report check karna hai`",
            parse_mode="Markdown"
        )
        return REMINDER_TEXT

    async def reminder_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data["reminder"] = {"text": update.message.text.strip()}
        await update.message.reply_text(
            "✅ Reminder text save!\n\nTime enter karein (HH:MM format, IST):\nExample: `15:30`",
            parse_mode="Markdown"
        )
        return REMINDER_TIME

    async def reminder_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            time_str = update.message.text.strip()
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError

            text = context.user_data["reminder"]["text"]
            await update.message.reply_text(
                f"✅ *Reminder Set!*\n\n"
                f"📝 Text: *{text}*\n"
                f"⏰ Time: *{time_str} IST*\n\n"
                f"_Aapko {time_str} pe reminder milega!_",
                parse_mode="Markdown"
            )
            context.user_data.pop("reminder", None)
            return ConversationHandler.END
        except (ValueError, AttributeError):
            await update.message.reply_text("❌ Valid time enter karein (HH:MM). Example: `15:30`", parse_mode="Markdown")
            return REMINDER_TIME

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancel ho gaya.")
        return ConversationHandler.END
