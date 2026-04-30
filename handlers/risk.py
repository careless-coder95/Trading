"""
⚠️ RISK MANAGEMENT HANDLER
ForexBot Pro - Risk & Drawdown Management
"""

import logging
from datetime import date, timedelta
from telegram import Update
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    ContextTypes, filters
)
from config import MAXLOSS_AMOUNT, MAXLOSS_TYPE
from database import Database

logger = logging.getLogger(__name__)


class RiskManager:
    """Risk management and drawdown tracking"""

    def __init__(self):
        self.db = Database()

    def get_maxloss_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("maxloss", self.start_maxloss)],
            states={
                MAXLOSS_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.maxloss_type)],
                MAXLOSS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.maxloss_amount)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def drawdown_tracker(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Track current drawdown"""
        user_id = update.effective_user.id
        self.db.ensure_user(user_id)
        
        # Get user settings
        settings = self.db.get_user_settings(user_id)
        initial_balance = settings.get("account_balance", 10000)
        
        # Get equity curve data
        equity_data = self.db.get_equity_curve(user_id)
        
        if not equity_data:
            await update.message.reply_text(
                "📊 Drawdown track karne ke liye trades zaruri hain!\n"
                "`/addtrade` se start karein.",
                parse_mode="Markdown"
            )
            return
        
        # Calculate current equity
        total_pnl = sum([t["profit_loss"] for t in equity_data])
        current_equity = initial_balance + total_pnl
        
        # Find peak equity
        peak_equity = initial_balance
        max_drawdown_amount = 0
        max_drawdown_percent = 0
        
        running_equity = initial_balance
        for trade in equity_data:
            running_equity += trade["profit_loss"]
            if running_equity > peak_equity:
                peak_equity = running_equity
            
            drawdown_amount = peak_equity - running_equity
            drawdown_percent = (drawdown_amount / peak_equity * 100) if peak_equity > 0 else 0
            
            if drawdown_amount > max_drawdown_amount:
                max_drawdown_amount = drawdown_amount
                max_drawdown_percent = drawdown_percent
        
        # Current drawdown
        current_drawdown_amount = peak_equity - current_equity
        current_drawdown_percent = (current_drawdown_amount / peak_equity * 100) if peak_equity > 0 else 0
        
        # Status emoji
        if current_drawdown_percent < 5:
            status = "🟢 Safe"
        elif current_drawdown_percent < 10:
            status = "🟡 Caution"
        elif current_drawdown_percent < 20:
            status = "🟠 Warning"
        else:
            status = "🔴 Danger"
        
        msg = (
            f"📉 *Drawdown Tracker*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Initial Balance: *${initial_balance:,.2f}*\n"
            f"🏔️ Peak Equity: *${peak_equity:,.2f}*\n"
            f"💵 Current Equity: *${current_equity:,.2f}*\n\n"
            f"📊 *Current Drawdown:*\n"
            f"Amount: *-${current_drawdown_amount:,.2f}*\n"
            f"Percent: *{current_drawdown_percent:.2f}%*\n"
            f"Status: {status}\n\n"
            f"🔻 *Max Drawdown (All-Time):*\n"
            f"Amount: *-${max_drawdown_amount:,.2f}*\n"
            f"Percent: *{max_drawdown_percent:.2f}%*\n\n"
        )
        
        if current_drawdown_percent >= 10:
            msg += "⚠️ _Consider reducing position sizes!_\n"
        if current_drawdown_percent >= 20:
            msg += "🛑 _High risk! Stop trading and review strategy!_"
        else:
            msg += "💡 _Keep risk per trade under 1-2%_"
        
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def start_maxloss(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Set maximum loss limit"""
        await update.message.reply_text(
            "🛑 *Maximum Loss Limit Set Karein*\n\n"
            "Limit type select karein:\n"
            "`daily` — Ek din ka max loss\n"
            "`weekly` — Ek week ka max loss\n"
            "`monthly` — Ek month ka max loss\n\n"
            "_/cancel se cancel karein_",
            parse_mode="Markdown"
        )
        return MAXLOSS_TYPE

    async def maxloss_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        limit_type = update.message.text.lower().strip()
        
        if limit_type not in ["daily", "weekly", "monthly"]:
            await update.message.reply_text(
                "❌ Sirf `daily`, `weekly` ya `monthly` enter karein.",
                parse_mode="Markdown"
            )
            return MAXLOSS_TYPE
        
        context.user_data["maxloss"] = {"type": limit_type}
        
        await update.message.reply_text(
            f"✅ Type: *{limit_type.capitalize()}*\n\n"
            "Maximum loss amount enter karein (USD mein):\n"
            "Example: `200`\n\n"
            "_Agar is limit ko cross karo, bot warning dega!_",
            parse_mode="Markdown"
        )
        return MAXLOSS_AMOUNT

    async def maxloss_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            amount = float(update.message.text.strip())
            if amount <= 0:
                raise ValueError
            
            maxloss = context.user_data["maxloss"]
            limit_type = maxloss["type"]
            
            # Save to database
            self.db.set_max_loss_limit(
                update.effective_user.id,
                limit_type,
                amount
            )
            
            type_emoji = {"daily": "📅", "weekly": "📆", "monthly": "📊"}
            
            await update.message.reply_text(
                f"🛑 *Max Loss Limit Set!*\n\n"
                f"{type_emoji[limit_type]} Type: *{limit_type.capitalize()}*\n"
                f"💰 Limit: *${amount:.2f}*\n\n"
                f"_Agar aap is limit ko cross karte hain, aapko warning milegi!_\n"
                f"_Risk management is key! 🔑_",
                parse_mode="Markdown"
            )
            context.user_data.pop("maxloss", None)
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ Valid amount enter karein (positive number).")
            return MAXLOSS_AMOUNT

    async def risk_assessment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comprehensive risk assessment"""
        user_id = update.effective_user.id
        
        # Get recent performance
        today = date.today()
        week_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        month_start = today.replace(day=1).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        daily_stats = self.db.get_stats(user_id, today_str, today_str)
        weekly_stats = self.db.get_stats(user_id, week_start, today_str)
        monthly_stats = self.db.get_stats(user_id, month_start, today_str)
        
        # Get max loss limits
        settings = self.db.get_user_settings(user_id)
        daily_limit = settings.get("max_loss_daily", 0)
        weekly_limit = settings.get("max_loss_weekly", 0)
        monthly_limit = settings.get("max_loss_monthly", 0)
        
        # Calculate risk scores
        risk_score = 0
        warnings = []
        
        # Check daily loss
        if daily_limit > 0 and abs(daily_stats["total_pnl"]) > daily_limit:
            risk_score += 30
            warnings.append("🔴 Daily loss limit exceeded!")
        
        # Check weekly loss
        if weekly_limit > 0 and abs(weekly_stats["total_pnl"]) > weekly_limit:
            risk_score += 25
            warnings.append("🟠 Weekly loss limit exceeded!")
        
        # Check win rate
        if weekly_stats["win_rate"] < 40:
            risk_score += 20
            warnings.append("⚠️ Win rate below 40%")
        
        # Check profit factor
        if weekly_stats["profit_factor"] < 1.0:
            risk_score += 15
            warnings.append("📉 Profit factor below 1.0")
        
        # Check streak
        streak = self.db.get_streak(user_id)
        if streak and streak["streak_type"] == "loss" and streak["current_streak"] >= 3:
            risk_score += 10
            warnings.append(f"❄️ {streak['current_streak']} consecutive losses")
        
        # Risk level
        if risk_score >= 50:
            risk_level = "🔴 *HIGH RISK*"
            recommendation = "🛑 _STOP TRADING! Review your strategy and take a break._"
        elif risk_score >= 30:
            risk_level = "🟠 *MEDIUM RISK*"
            recommendation = "⚠️ _Reduce position sizes and trade carefully._"
        elif risk_score >= 10:
            risk_level = "🟡 *LOW RISK*"
            recommendation = "💡 _Monitor your trades closely._"
        else:
            risk_level = "🟢 *SAFE*"
            recommendation = "✅ _Good risk management! Keep it up._"
        
        msg = (
            f"⚠️ *Risk Assessment Report*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Risk Level: {risk_level}\n"
            f"Risk Score: *{risk_score}/100*\n\n"
        )
        
        if warnings:
            msg += "🚨 *Warnings:*\n"
            for w in warnings:
                msg += f"• {w}\n"
            msg += "\n"
        
        msg += (
            f"📊 *Weekly Performance:*\n"
            f"Trades: {weekly_stats['total_trades']}\n"
            f"Win Rate: {weekly_stats['win_rate']:.1f}%\n"
            f"P&L: {'+'if weekly_stats['total_pnl']>=0 else ''}${weekly_stats['total_pnl']:.2f}\n"
            f"Profit Factor: {weekly_stats['profit_factor']:.2f}\n\n"
            f"{recommendation}"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancel ho gaya.")
        return ConversationHandler.END
