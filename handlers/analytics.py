"""
📈 ANALYTICS & REPORTS HANDLER
ForexBot Pro - Performance Analysis
"""

import logging
import os
from datetime import datetime, date, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from utils.charts import ChartGenerator
from utils.formatters import format_stats, format_detailed_report

logger = logging.getLogger(__name__)


class Analytics:
    """Performance analytics and reports"""

    def __init__(self):
        self.db = Database()
        self.charts = ChartGenerator()

    async def quick_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Quick statistics overview"""
        user_id = update.effective_user.id
        self.db.ensure_user(user_id)
        stats = self.db.get_stats(user_id)

        if stats["total_trades"] == 0:
            await update.message.reply_text(
                "📭 Abhi koi trade record nahi hai!\n\n"
                "`/addtrade` se trade log karna start karein.",
                parse_mode="Markdown"
            )
            return

        msg = format_stats(stats)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def detailed_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Detailed weekly/monthly report with charts"""
        user_id = update.effective_user.id
        args = context.args

        period = "monthly"
        if args and args[0].lower() == "weekly":
            period = "weekly"

        today = date.today()
        if period == "weekly":
            start = today - timedelta(days=7)
            title = "📊 Weekly Report"
        else:
            start = today.replace(day=1)
            title = "📊 Monthly Report"

        start_str = start.strftime("%Y-%m-%d")
        end_str = today.strftime("%Y-%m-%d")

        stats = self.db.get_stats(user_id, start_str, end_str)
        trades = self.db.get_trades(user_id, limit=100, start_date=start_str, end_date=end_str)

        if not trades:
            await update.message.reply_text(
                f"📭 {title}: Is period mein koi trade nahi mila!\n"
                f"Period: {start_str} se {end_str}"
            )
            return

        await update.message.reply_text("⏳ Report generate ho rahi hai, please wait...")

        # Generate chart
        chart_path = self.charts.generate_monthly_bar(user_id, trades, title)

        report_text = format_detailed_report(stats, trades, title, start_str, end_str)

        if chart_path and os.path.exists(chart_path):
            with open(chart_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=report_text[:1024],
                    parse_mode="Markdown"
                )
            os.remove(chart_path)
        else:
            await update.message.reply_text(report_text, parse_mode="Markdown")

    async def equity_curve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show equity curve chart"""
        user_id = update.effective_user.id
        equity_data = self.db.get_equity_curve(user_id)

        if not equity_data:
            await update.message.reply_text("📭 Equity curve ke liye trades zaruri hain!")
            return

        await update.message.reply_text("📈 Equity curve generate ho rahi hai...")

        settings = self.db.get_user_settings(user_id)
        initial_balance = settings.get("account_balance", 10000)

        chart_path = self.charts.generate_equity_curve(user_id, equity_data, initial_balance)

        if chart_path and os.path.exists(chart_path):
            with open(chart_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📈 *Equity Curve*\nInitial Balance: ${initial_balance:,.2f}",
                    parse_mode="Markdown"
                )
            os.remove(chart_path)
        else:
            await update.message.reply_text("❌ Chart generate nahi ho paya!")

    async def strategy_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Strategy-wise breakdown"""
        user_id = update.effective_user.id
        trades = self.db.get_trades(user_id, limit=500)

        if not trades:
            await update.message.reply_text("📭 Koi trade nahi mila!")
            return

        # Group by strategy
        strategies = {}
        for t in trades:
            strat = t.get("strategy") or "Unknown"
            if strat not in strategies:
                strategies[strat] = {"trades": 0, "wins": 0, "pnl": 0}
            strategies[strat]["trades"] += 1
            if t["profit_loss"] > 0:
                strategies[strat]["wins"] += 1
            strategies[strat]["pnl"] += t["profit_loss"]

        if not strategies:
            await update.message.reply_text("📭 Strategy data nahi mila!")
            return

        msg = "📊 *Strategy Performance*\n" + "━" * 28 + "\n\n"
        for strat, data in sorted(strategies.items(), key=lambda x: x[1]["pnl"], reverse=True):
            win_rate = (data["wins"] / data["trades"] * 100) if data["trades"] > 0 else 0
            pnl = data["pnl"]
            emoji = "✅" if pnl >= 0 else "❌"
            msg += (
                f"{emoji} *{strat}*\n"
                f"  Trades: {data['trades']} | WR: {win_rate:.1f}%\n"
                f"  P&L: {'+'if pnl>=0 else ''}${pnl:.2f}\n\n"
            )

        await update.message.reply_text(msg, parse_mode="Markdown")

    async def today_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Today's trading summary"""
        user_id = update.effective_user.id
        today = date.today().strftime("%Y-%m-%d")
        stats = self.db.get_stats(user_id, today, today)
        trades = self.db.get_trades(user_id, limit=20, start_date=today, end_date=today)

        if stats["total_trades"] == 0:
            await update.message.reply_text(
                f"📅 *Aaj ka Summary ({today})*\n\n"
                "Aaj koi trade nahi hua!\n\n"
                "💡 `/addtrade` se trade log karein.",
                parse_mode="Markdown"
            )
            return

        pnl = stats["total_pnl"]
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        msg = (
            f"📅 *Aaj ka Summary*\n"
            f"_{today}_\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Total Trades: *{stats['total_trades']}*\n"
            f"✅ Wins: *{stats['wins']}* | ❌ Losses: *{stats['losses']}*\n"
            f"🎯 Win Rate: *{stats['win_rate']:.1f}%*\n"
            f"{pnl_emoji} Total P&L: *{pnl_str}*\n\n"
        )

        if trades:
            msg += "📋 *Trades:*\n"
            for t in trades[:5]:
                t_pnl = t["profit_loss"]
                t_emoji = "💰" if t_pnl >= 0 else "📉"
                msg += f"{t_emoji} {t['pair']} {t['direction']} → {'+'if t_pnl>=0 else ''}${t_pnl:.2f}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")

    async def week_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """This week's performance"""
        user_id = update.effective_user.id
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        week_end = today.strftime("%Y-%m-%d")

        stats = self.db.get_stats(user_id, week_start, week_end)

        pnl = stats["total_pnl"]
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        msg = (
            f"📅 *Is Week Ki Performance*\n"
            f"_{week_start} → {week_end}_\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Total Trades: *{stats['total_trades']}*\n"
            f"✅ Wins: *{stats['wins']}* | ❌ Losses: *{stats['losses']}*\n"
            f"🎯 Win Rate: *{stats['win_rate']:.1f}%*\n"
            f"{pnl_emoji} P&L: *{pnl_str}*\n"
            f"💎 Best Pair: *{stats['best_pair']}*\n"
            f"📊 Profit Factor: *{stats['profit_factor']:.2f}*\n\n"
            f"_/report ke liye detailed chart dekhein_ 📈"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def month_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Monthly overview"""
        user_id = update.effective_user.id
        today = date.today()
        month_start = today.replace(day=1).strftime("%Y-%m-%d")
        month_end = today.strftime("%Y-%m-%d")
        month_name = today.strftime("%B %Y")

        stats = self.db.get_stats(user_id, month_start, month_end)

        pnl = stats["total_pnl"]
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        streak = self.db.get_streak(user_id)
        streak_emoji = "🔥" if streak["streak_type"] == "win" else "❄️"

        msg = (
            f"📅 *{month_name} Overview*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Total Trades: *{stats['total_trades']}*\n"
            f"✅ Wins: *{stats['wins']}* | ❌ Losses: *{stats['losses']}*\n"
            f"🎯 Win Rate: *{stats['win_rate']:.1f}%*\n"
            f"{pnl_emoji} Total P&L: *{pnl_str}*\n"
            f"💰 Avg Win: *${stats['avg_win']:.2f}*\n"
            f"📉 Avg Loss: *-${stats['avg_loss']:.2f}*\n"
            f"📊 Profit Factor: *{stats['profit_factor']:.2f}*\n"
            f"💎 Best Pair: *{stats['best_pair']}*\n"
            f"{streak_emoji} Streak: *{streak['current_streak']} {streak['streak_type']}s*\n\n"
            f"_/equity se equity curve dekhein_ 📈\n"
            f"_/report monthly ke liye detail mein_ 📊"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
