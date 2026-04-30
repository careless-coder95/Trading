"""
🎯 GOALS HANDLER
ForexBot Pro - Goal Setting & Tracking
"""

import logging
from datetime import date, timedelta
from telegram import Update
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    ContextTypes, filters
)
from config import GOAL_TYPE, GOAL_AMOUNT, GOAL_DATES
from database import Database

logger = logging.getLogger(__name__)


class Goals:
    """Goal tracking and management"""

    def __init__(self):
        self.db = Database()

    def get_setgoal_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("setgoal", self.start_setgoal)],
            states={
                GOAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.goal_type)],
                GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.goal_amount)],
                GOAL_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.goal_dates)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def start_setgoal(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start goal setting process"""
        self.db.ensure_user(update.effective_user.id)
        await update.message.reply_text(
            "🎯 *Goal Set Karein*\n\n"
            "Goal type select karein:\n"
            "`daily` — Aaj ka target\n"
            "`weekly` — Is week ka target\n"
            "`monthly` — Is month ka target\n\n"
            "_/cancel se cancel karein_",
            parse_mode="Markdown"
        )
        return GOAL_TYPE

    async def goal_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        goal_type = update.message.text.lower().strip()
        if goal_type not in ["daily", "weekly", "monthly"]:
            await update.message.reply_text(
                "❌ Sirf `daily`, `weekly` ya `monthly` enter karein.",
                parse_mode="Markdown"
            )
            return GOAL_TYPE

        context.user_data["goal"] = {"type": goal_type}
        
        type_emoji = {"daily": "📅", "weekly": "📆", "monthly": "📊"}
        await update.message.reply_text(
            f"{type_emoji[goal_type]} *{goal_type.capitalize()} Goal*\n\n"
            "Target profit amount enter karein (USD mein):\n"
            "Example: `500`",
            parse_mode="Markdown"
        )
        return GOAL_AMOUNT

    async def goal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            amount = float(update.message.text.strip())
            if amount <= 0:
                raise ValueError
            
            context.user_data["goal"]["amount"] = amount
            goal_type = context.user_data["goal"]["type"]
            
            # Auto-calculate dates
            today = date.today()
            if goal_type == "daily":
                start_date = today
                end_date = today
            elif goal_type == "weekly":
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # monthly
                start_date = today.replace(day=1)
                next_month = today.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            
            context.user_data["goal"]["start_date"] = start_date
            context.user_data["goal"]["end_date"] = end_date
            
            await update.message.reply_text(
                f"✅ Amount: *${amount:.2f}*\n\n"
                f"Period: `{start_date}` se `{end_date}`\n\n"
                "Confirm karne ke liye `yes` type karein ya `/cancel`",
                parse_mode="Markdown"
            )
            return GOAL_DATES
            
        except ValueError:
            await update.message.reply_text("❌ Valid amount enter karein (positive number).")
            return GOAL_AMOUNT

    async def goal_dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        confirmation = update.message.text.lower().strip()
        
        if confirmation != "yes":
            await update.message.reply_text("❌ Goal set nahi hua. `/setgoal` se dobara try karein.")
            context.user_data.pop("goal", None)
            return ConversationHandler.END
        
        goal = context.user_data["goal"]
        goal_id = self.db.set_goal(
            update.effective_user.id,
            goal["type"],
            goal["amount"],
            goal["start_date"],
            goal["end_date"]
        )
        
        type_emoji = {"daily": "📅", "weekly": "📆", "monthly": "📊"}
        await update.message.reply_text(
            f"🎯 *Goal #{goal_id} Set Ho Gaya!*\n\n"
            f"{type_emoji[goal['type']]} Type: *{goal['type'].capitalize()}*\n"
            f"💰 Target: *${goal['amount']:.2f}*\n"
            f"📆 Period: `{goal['start_date']}` → `{goal['end_date']}`\n\n"
            f"_Track karne ke liye `/goals` use karein!_ 📈",
            parse_mode="Markdown"
        )
        context.user_data.pop("goal", None)
        return ConversationHandler.END

    async def view_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """View all active goals"""
        user_id = update.effective_user.id
        goals = self.db.get_goals(user_id)
        
        if not goals:
            await update.message.reply_text(
                "🎯 Koi active goal nahi hai!\n\n"
                "`/setgoal` se goal set karein.",
                parse_mode="Markdown"
            )
            return
        
        msg = "🎯 *Active Goals*\n" + "━" * 30 + "\n\n"
        
        for goal in goals:
            # Get current progress
            stats = self.db.get_stats(
                user_id, 
                goal["start_date"], 
                goal["end_date"]
            )
            current = stats["total_pnl"]
            target = goal["target_amount"]
            progress = (current / target * 100) if target > 0 else 0
            
            # Progress bar
            bars = int(progress / 10)
            bar_display = "█" * min(bars, 10) + "░" * max(10 - bars, 0)
            
            status_emoji = "🟢" if current >= target else "🟡" if progress >= 50 else "🔴"
            type_emoji = {"daily": "📅", "weekly": "📆", "monthly": "📊"}
            
            msg += (
                f"{status_emoji} *Goal #{goal['id']}* {type_emoji.get(goal['goal_type'], '📊')}\n"
                f"Type: *{goal['goal_type'].capitalize()}*\n"
                f"Target: *${target:.2f}*\n"
                f"Current: {'+'if current>=0 else ''}*${current:.2f}*\n"
                f"Progress: {bar_display} *{progress:.1f}%*\n"
                f"Period: `{goal['start_date']}` → `{goal['end_date']}`\n\n"
            )
        
        msg += f"_Total: {len(goals)} goals_ | Keep trading! 💪"
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def view_streak(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """View current win/loss streak"""
        user_id = update.effective_user.id
        streak = self.db.get_streak(user_id)
        
        if not streak:
            await update.message.reply_text(
                "📊 Abhi koi trade nahi hai streak track karne ke liye!",
                parse_mode="Markdown"
            )
            return
        
        streak_type = streak["streak_type"]
        current = streak["current_streak"]
        longest_win = streak["longest_win_streak"]
        longest_loss = streak["longest_loss_streak"]
        
        if streak_type == "win":
            emoji = "🔥"
            color = "GREEN"
            msg_header = f"{emoji} *WIN STREAK!* {emoji}"
        else:
            emoji = "❄️"
            color = "RED"
            msg_header = f"{emoji} *Loss Streak* {emoji}"
        
        msg = (
            f"{msg_header}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Current Streak: *{current} consecutive {streak_type}s*\n\n"
            f"🏆 *All-Time Records:*\n"
            f"✅ Longest Win Streak: *{longest_win}*\n"
            f"❌ Longest Loss Streak: *{longest_loss}*\n\n"
        )
        
        if streak_type == "win" and current >= 3:
            msg += "💪 _Momentum hai! Keep going!_"
        elif streak_type == "loss" and current >= 3:
            msg += "⚠️ _Take a break, review your strategy!_"
        else:
            msg += "📈 _Stay focused and trade smart!_"
        
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.pop("goal", None)
        await update.message.reply_text("❌ Goal setting cancel ho gaya.")
        return ConversationHandler.END
