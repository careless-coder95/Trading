"""
📊 TRADE LOGGING HANDLERS
ForexBot Pro - Trade Management
"""

import csv
import io
import logging
import os
import shutil
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from config import (
    TRADE_PAIR, TRADE_DIRECTION, TRADE_ENTRY, TRADE_EXIT,
    TRADE_LOT, TRADE_PNL, TRADE_STRATEGY, TRADE_NOTES,
    EDIT_FIELD, EDIT_VALUE
)
from database import Database
from utils.validators import validate_pair, validate_price, validate_lot
from utils.formatters import format_trade_list, format_trade_detail

logger = logging.getLogger(__name__)


class TradeLogger:
    """Handles trade logging operations"""

    def __init__(self):
        self.db = Database()

    def get_add_trade_handler(self) -> ConversationHandler:
        """Conversation handler for adding trades"""
        return ConversationHandler(
            entry_points=[CommandHandler("addtrade", self.start_add_trade)],
            states={
                TRADE_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_pair)],
                TRADE_DIRECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_direction)],
                TRADE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_entry)],
                TRADE_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_exit)],
                TRADE_LOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_lot)],
                TRADE_PNL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_pnl)],
                TRADE_STRATEGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_strategy)],
                TRADE_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_notes)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def get_edit_trade_handler(self) -> ConversationHandler:
        """Conversation handler for editing trades"""
        return ConversationHandler(
            entry_points=[CommandHandler("edittrade", self.start_edit_trade)],
            states={
                EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_edit_field)],
                EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_edit_value)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def start_add_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start trade logging conversation"""
        self.db.ensure_user(update.effective_user.id)
        await update.message.reply_text(
            "📊 *Naya Trade Log Karein*\n\n"
            "Currency pair enter karein:\n"
            "Example: `EURUSD`, `GBPJPY`, `USDJPY`\n\n"
            "_/cancel likhein rokne ke liye_",
            parse_mode="Markdown"
        )
        return TRADE_PAIR

    async def get_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pair = update.message.text.upper().strip()
        if not validate_pair(pair):
            await update.message.reply_text(
                f"❌ `{pair}` valid pair nahi hai.\n"
                "Sahi format: `EURUSD`, `GBPUSD`, `USDJPY`",
                parse_mode="Markdown"
            )
            return TRADE_PAIR

        context.user_data["trade"] = {"pair": pair}
        keyboard = [[
            InlineKeyboardButton("📈 BUY", callback_data="dir_BUY"),
            InlineKeyboardButton("📉 SELL", callback_data="dir_SELL")
        ]]
        await update.message.reply_text(
            f"✅ Pair: *{pair}*\n\nDirection kya hai?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return TRADE_DIRECTION

    async def get_direction(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        direction = update.message.text.upper().strip()
        if direction not in ["BUY", "SELL"]:
            await update.message.reply_text("❌ Sirf BUY ya SELL likhen.")
            return TRADE_DIRECTION

        context.user_data["trade"]["direction"] = direction
        await update.message.reply_text(
            f"✅ Direction: *{direction}*\n\nEntry price enter karein:\nExample: `1.0850`",
            parse_mode="Markdown"
        )
        return TRADE_ENTRY

    async def get_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            price = float(update.message.text.strip())
            context.user_data["trade"]["entry_price"] = price
            await update.message.reply_text(
                f"✅ Entry: *{price}*\n\nExit price enter karein (ya `skip` karein agar trade abhi open hai):",
                parse_mode="Markdown"
            )
            return TRADE_EXIT
        except ValueError:
            await update.message.reply_text("❌ Valid price enter karein. Example: `1.0850`", parse_mode="Markdown")
            return TRADE_ENTRY

    async def get_exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip().lower()
        if text == "skip":
            context.user_data["trade"]["exit_price"] = None
            context.user_data["trade"]["status"] = "OPEN"
        else:
            try:
                price = float(text)
                context.user_data["trade"]["exit_price"] = price
                context.user_data["trade"]["status"] = "CLOSED"
            except ValueError:
                await update.message.reply_text("❌ Valid price ya `skip` enter karein.", parse_mode="Markdown")
                return TRADE_EXIT

        await update.message.reply_text(
            "Lot size enter karein:\nExample: `0.01`, `0.1`, `1.0`",
            parse_mode="Markdown"
        )
        return TRADE_LOT

    async def get_lot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            lot = float(update.message.text.strip())
            if lot <= 0:
                raise ValueError
            context.user_data["trade"]["lot_size"] = lot
            await update.message.reply_text(
                f"✅ Lot Size: *{lot}*\n\nP&L enter karein (USD mein, negative for loss):\n"
                "Example: `+50.25` ya `-30.00` ya `skip`",
                parse_mode="Markdown"
            )
            return TRADE_PNL
        except ValueError:
            await update.message.reply_text("❌ Valid lot size enter karein. Example: `0.01`", parse_mode="Markdown")
            return TRADE_LOT

    async def get_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        if text.lower() == "skip":
            # Auto-calculate P&L from entry/exit
            trade = context.user_data["trade"]
            if trade.get("exit_price") and trade.get("entry_price"):
                pnl = self._calculate_pnl(trade)
                context.user_data["trade"]["profit_loss"] = pnl
            else:
                context.user_data["trade"]["profit_loss"] = 0
        else:
            try:
                pnl = float(text.replace("+", ""))
                context.user_data["trade"]["profit_loss"] = pnl
            except ValueError:
                await update.message.reply_text("❌ Valid amount ya `skip` enter karein.", parse_mode="Markdown")
                return TRADE_PNL

        await update.message.reply_text(
            "Strategy enter karein (ya `skip`):\nExample: `Breakout`, `Trend Following`, `Scalping`",
            parse_mode="Markdown"
        )
        return TRADE_STRATEGY

    async def get_strategy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        context.user_data["trade"]["strategy"] = "" if text.lower() == "skip" else text
        await update.message.reply_text(
            "Notes enter karein (ya `skip`):\nExample: `NFP ke baad trade liya`, `Strong trend`",
            parse_mode="Markdown"
        )
        return TRADE_NOTES

    async def get_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        context.user_data["trade"]["notes"] = "" if text.lower() == "skip" else text
        context.user_data["trade"]["entry_time"] = datetime.now()

        trade_data = context.user_data["trade"]
        trade_id = self.db.add_trade(update.effective_user.id, trade_data)

        pnl = trade_data.get("profit_loss", 0)
        pnl_emoji = "💰" if pnl >= 0 else "📉"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        await update.message.reply_text(
            f"✅ *Trade #{trade_id} Successfully Logged!*\n\n"
            f"💱 Pair: *{trade_data['pair']}*\n"
            f"📊 Direction: *{trade_data['direction']}*\n"
            f"🔵 Entry: *{trade_data['entry_price']}*\n"
            f"🔴 Exit: *{trade_data.get('exit_price', 'Open')}*\n"
            f"📦 Lot Size: *{trade_data['lot_size']}*\n"
            f"{pnl_emoji} P&L: *{pnl_str}*\n"
            f"📋 Strategy: *{trade_data.get('strategy', 'N/A')}*\n\n"
            f"_Trade #{trade_id} save ho gaya!_ 🎉",
            parse_mode="Markdown"
        )
        context.user_data.pop("trade", None)
        return ConversationHandler.END

    async def view_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """View recent trades"""
        trades = self.db.get_trades(update.effective_user.id, limit=10)
        if not trades:
            await update.message.reply_text(
                "📭 Koi trade nahi mila!\n\n`/addtrade` se pehla trade log karein.",
                parse_mode="Markdown"
            )
            return

        msg = format_trade_list(trades)
        keyboard = [[
            InlineKeyboardButton("📊 Stats", callback_data="show_stats"),
            InlineKeyboardButton("📈 More", callback_data="more_trades"),
        ]]
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def start_edit_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start edit trade flow"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "✏️ Trade edit karne ke liye Trade ID enter karein:\n"
                "Example: `/edittrade 5`",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        try:
            trade_id = int(args[0])
            trade = self.db.get_trade_by_id(trade_id, update.effective_user.id)
            if not trade:
                await update.message.reply_text(f"❌ Trade #{trade_id} nahi mila!")
                return ConversationHandler.END

            context.user_data["edit_trade_id"] = trade_id
            await update.message.reply_text(
                f"✏️ *Trade #{trade_id} Edit*\n\n"
                f"Kya edit karna hai? Enter field name:\n"
                f"`exit_price`, `profit_loss`, `strategy`, `notes`, `lot_size`",
                parse_mode="Markdown"
            )
            return EDIT_FIELD
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Valid Trade ID enter karein.")
            return ConversationHandler.END

    async def get_edit_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        field = update.message.text.strip().lower()
        valid_fields = ["exit_price", "profit_loss", "strategy", "notes", "lot_size"]
        if field not in valid_fields:
            await update.message.reply_text(
                f"❌ Valid field enter karein:\n{', '.join(valid_fields)}"
            )
            return EDIT_FIELD

        context.user_data["edit_field"] = field
        await update.message.reply_text(f"Naya value enter karein `{field}` ke liye:", parse_mode="Markdown")
        return EDIT_VALUE

    async def get_edit_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        value = update.message.text.strip()
        field = context.user_data.get("edit_field")
        trade_id = context.user_data.get("edit_trade_id")

        try:
            if field in ["exit_price", "profit_loss", "lot_size"]:
                value = float(value)
        except ValueError:
            await update.message.reply_text("❌ Valid value enter karein.")
            return EDIT_VALUE

        success = self.db.update_trade(trade_id, update.effective_user.id, {field: value})
        if success:
            await update.message.reply_text(f"✅ Trade #{trade_id} update ho gaya!\n`{field}` = `{value}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Update nahi ho paya.")
        return ConversationHandler.END

    async def delete_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete a trade"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "🗑️ Trade delete karne ke liye:\n`/deletetrade <trade_id>`\n\nExample: `/deletetrade 5`",
                parse_mode="Markdown"
            )
            return

        try:
            trade_id = int(args[0])
            keyboard = [[
                InlineKeyboardButton("✅ Haan, Delete", callback_data=f"del_trade_{trade_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]]
            await update.message.reply_text(
                f"⚠️ Trade #{trade_id} permanently delete karna chahte hain?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text("❌ Valid Trade ID enter karein.")

    async def export_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Export trades to CSV"""
        user_id = update.effective_user.id
        trades = self.db.get_trades(user_id, limit=1000)

        if not trades:
            await update.message.reply_text("📭 Export ke liye koi trade nahi mila!")
            return

        await update.message.reply_text("⏳ CSV file generate ho rahi hai...")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id", "pair", "direction", "entry_price", "exit_price",
            "lot_size", "profit_loss", "pips", "strategy", "notes",
            "entry_time", "exit_time", "status"
        ])
        writer.writeheader()
        for trade in trades:
            writer.writerow({k: trade.get(k, "") for k in writer.fieldnames})

        output.seek(0)
        filename = f"trades_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv"

        await update.message.reply_document(
            document=output.getvalue().encode(),
            filename=filename,
            caption=f"📊 {len(trades)} trades exported successfully!\n_ForexBot Pro Export_"
        )

    async def backup_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Create database backup"""
        from config import Config
        config = Config()
        db_path = config.DATABASE_PATH

        if os.path.exists(db_path):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            with open(db_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=backup_name,
                    caption="💾 Database backup successfully created!\n_ForexBot Pro Backup_"
                )
        else:
            await update.message.reply_text("❌ Database file nahi mili!")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancel ho gaya.")
        return ConversationHandler.END

    def _calculate_pnl(self, trade: Dict) -> float:
        """Basic P&L calculation"""
        from config import PIP_VALUES
        entry = trade.get("entry_price", 0)
        exit_p = trade.get("exit_price", 0)
        lot = trade.get("lot_size", 0.01)
        direction = trade.get("direction", "BUY")
        pair = trade.get("pair", "EURUSD")

        pip_val = PIP_VALUES.get(pair, 10.0)

        if "JPY" in pair:
            pip_diff = (exit_p - entry) / 0.01 if direction == "BUY" else (entry - exit_p) / 0.01
        else:
            pip_diff = (exit_p - entry) / 0.0001 if direction == "BUY" else (entry - exit_p) / 0.0001

        return round(pip_diff * pip_val * lot, 2)
