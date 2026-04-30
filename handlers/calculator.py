"""
🧮 CALCULATOR HANDLERS
ForexBot Pro - Trading Calculators
"""

import logging
from telegram import Update
from telegram.ext import (
    CommandHandler, ConversationHandler, MessageHandler,
    ContextTypes, filters
)
from config import LOTSIZE_BALANCE, LOTSIZE_RISK, LOTSIZE_PAIR, LOTSIZE_SL, PIP_VALUES
from config import PNL_PAIR, PNL_LOT, PNL_ENTRY, PNL_EXIT, PNL_DIRECTION
from database import Database

logger = logging.getLogger(__name__)


class Calculator:
    """Trading calculators"""

    def __init__(self):
        self.db = Database()

    def get_lotsize_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("lotsize", self.start_lotsize)],
            states={
                LOTSIZE_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ls_balance)],
                LOTSIZE_RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ls_risk)],
                LOTSIZE_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ls_pair)],
                LOTSIZE_SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ls_sl)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def get_pnl_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("pnl", self.start_pnl)],
            states={
                PNL_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pnl_pair)],
                PNL_DIRECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pnl_direction)],
                PNL_LOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pnl_lot)],
                PNL_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pnl_entry)],
                PNL_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.pnl_exit)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    # ═══ LOT SIZE CALCULATOR ═══

    async def start_lotsize(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        settings = self.db.get_user_settings(update.effective_user.id)
        balance = settings.get("account_balance", 10000)
        context.user_data["ls"] = {}

        await update.message.reply_text(
            "🧮 *Lot Size Calculator*\n\n"
            f"Account balance enter karein (default: `${balance}`):\n"
            "Ya `skip` press karein saved balance use karne ke liye:",
            parse_mode="Markdown"
        )
        return LOTSIZE_BALANCE

    async def ls_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        if text.lower() == "skip":
            settings = self.db.get_user_settings(update.effective_user.id)
            context.user_data["ls"]["balance"] = settings.get("account_balance", 10000)
        else:
            try:
                context.user_data["ls"]["balance"] = float(text.replace("$", "").replace(",", ""))
            except ValueError:
                await update.message.reply_text("❌ Valid amount enter karein. Example: `10000`", parse_mode="Markdown")
                return LOTSIZE_BALANCE

        await update.message.reply_text(
            f"✅ Balance: *${context.user_data['ls']['balance']:,.2f}*\n\n"
            "Risk percentage enter karein (e.g. `1` for 1%, `2` for 2%):",
            parse_mode="Markdown"
        )
        return LOTSIZE_RISK

    async def ls_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            risk = float(update.message.text.strip().replace("%", ""))
            if risk <= 0 or risk > 100:
                raise ValueError
            context.user_data["ls"]["risk"] = risk
        except ValueError:
            await update.message.reply_text("❌ Valid % enter karein (0.1 se 100 ke beech).", parse_mode="Markdown")
            return LOTSIZE_RISK

        await update.message.reply_text(
            f"✅ Risk: *{context.user_data['ls']['risk']}%*\n\n"
            "Currency pair enter karein (e.g. `EURUSD`):",
            parse_mode="Markdown"
        )
        return LOTSIZE_PAIR

    async def ls_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pair = update.message.text.upper().strip()
        context.user_data["ls"]["pair"] = pair
        await update.message.reply_text(
            f"✅ Pair: *{pair}*\n\nStop Loss pips enter karein (e.g. `20` ya `15.5`):",
            parse_mode="Markdown"
        )
        return LOTSIZE_SL

    async def ls_sl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            sl_pips = float(update.message.text.strip())
            if sl_pips <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Valid SL pips enter karein.", parse_mode="Markdown")
            return LOTSIZE_SL

        ls = context.user_data["ls"]
        balance = ls["balance"]
        risk_pct = ls["risk"]
        pair = ls["pair"]

        risk_amount = balance * (risk_pct / 100)
        pip_val = PIP_VALUES.get(pair, 10.0)
        lot_size = risk_amount / (sl_pips * pip_val)

        # Round to standard lot sizes
        micro = round(lot_size, 2)
        mini = round(lot_size / 10, 3)

        await update.message.reply_text(
            f"🧮 *Lot Size Calculation Result*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Balance: *${balance:,.2f}*\n"
            f"⚠️ Risk: *{risk_pct}%* = *${risk_amount:.2f}*\n"
            f"💱 Pair: *{pair}*\n"
            f"🛑 SL: *{sl_pips} pips*\n"
            f"📊 Pip Value: *${pip_val:.2f}/lot*\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Recommended Lot Size: {micro} lots*\n\n"
            f"📦 Standard: *{micro} lots*\n"
            f"📦 Mini: *{mini} lots*\n\n"
            f"_Risk per trade: ${risk_amount:.2f}_",
            parse_mode="Markdown"
        )
        context.user_data.pop("ls", None)
        return ConversationHandler.END

    # ═══ P&L CALCULATOR ═══

    async def start_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data["pnl_calc"] = {}
        await update.message.reply_text(
            "💰 *P&L Calculator*\n\nCurrency pair enter karein (e.g. `EURUSD`):",
            parse_mode="Markdown"
        )
        return PNL_PAIR

    async def pnl_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data["pnl_calc"]["pair"] = update.message.text.upper().strip()
        await update.message.reply_text("Direction enter karein: `BUY` ya `SELL`", parse_mode="Markdown")
        return PNL_DIRECTION

    async def pnl_direction(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        direction = update.message.text.upper().strip()
        if direction not in ["BUY", "SELL"]:
            await update.message.reply_text("❌ Sirf BUY ya SELL enter karein.")
            return PNL_DIRECTION
        context.user_data["pnl_calc"]["direction"] = direction
        await update.message.reply_text("Lot size enter karein (e.g. `0.1`):", parse_mode="Markdown")
        return PNL_LOT

    async def pnl_lot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            context.user_data["pnl_calc"]["lot"] = float(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Valid lot size enter karein.", parse_mode="Markdown")
            return PNL_LOT
        await update.message.reply_text("Entry price enter karein:", parse_mode="Markdown")
        return PNL_ENTRY

    async def pnl_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            context.user_data["pnl_calc"]["entry"] = float(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Valid price enter karein.", parse_mode="Markdown")
            return PNL_ENTRY
        await update.message.reply_text("Exit price enter karein:", parse_mode="Markdown")
        return PNL_EXIT

    async def pnl_exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            exit_p = float(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Valid price enter karein.", parse_mode="Markdown")
            return PNL_EXIT

        d = context.user_data["pnl_calc"]
        pair, direction, lot, entry = d["pair"], d["direction"], d["lot"], d["entry"]
        pip_val = PIP_VALUES.get(pair, 10.0)

        if "JPY" in pair:
            pips = (exit_p - entry) / 0.01 if direction == "BUY" else (entry - exit_p) / 0.01
        else:
            pips = (exit_p - entry) / 0.0001 if direction == "BUY" else (entry - exit_p) / 0.0001

        pnl = pips * pip_val * lot
        pnl_emoji = "💰" if pnl >= 0 else "📉"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        await update.message.reply_text(
            f"💰 *P&L Calculation Result*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💱 Pair: *{pair}* | {direction}\n"
            f"📦 Lot: *{lot}*\n"
            f"🔵 Entry: *{entry}*\n"
            f"🔴 Exit: *{exit_p}*\n"
            f"📊 Pips: *{pips:.1f}*\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{pnl_emoji} *P&L: {pnl_str}*",
            parse_mode="Markdown"
        )
        context.user_data.pop("pnl_calc", None)
        return ConversationHandler.END

    # ═══ MARGIN CALCULATOR ═══

    async def margin_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "🏦 *Margin Calculator*\n\n"
                "Usage: `/margin <pair> <lot_size> <leverage>`\n"
                "Example: `/margin EURUSD 1.0 100`\n\n"
                "_1 lot = 100,000 units_",
                parse_mode="Markdown"
            )
            return

        try:
            pair, lot, leverage = args[0].upper(), float(args[1]), int(args[2])
            contract_size = 100000
            # Simplified margin calculation
            if "USD" in pair[:3]:
                margin = (lot * contract_size) / leverage
            else:
                margin = (lot * contract_size * 1.1) / leverage  # Approximate

            await update.message.reply_text(
                f"🏦 *Margin Calculation*\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"💱 Pair: *{pair}*\n"
                f"📦 Lot: *{lot}*\n"
                f"⚡ Leverage: *1:{leverage}*\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏦 *Required Margin: ${margin:,.2f}*",
                parse_mode="Markdown"
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Sahi format: `/margin EURUSD 1.0 100`", parse_mode="Markdown")

    # ═══ RISK/REWARD CALCULATOR ═══

    async def risk_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "⚖️ *Risk/Reward Calculator*\n\n"
                "Usage: `/risk <entry> <sl> <tp>`\n"
                "Example: `/risk 1.0850 1.0830 1.0890`\n\n"
                "_Enter ke sath SL aur TP prices_",
                parse_mode="Markdown"
            )
            return

        try:
            entry, sl, tp = float(args[0]), float(args[1]), float(args[2])
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = reward / risk if risk > 0 else 0

            rr_emoji = "✅" if rr_ratio >= 1.5 else "⚠️" if rr_ratio >= 1 else "❌"

            await update.message.reply_text(
                f"⚖️ *Risk/Reward Analysis*\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"🔵 Entry: *{entry}*\n"
                f"🛑 Stop Loss: *{sl}*\n"
                f"🎯 Take Profit: *{tp}*\n\n"
                f"📉 Risk: *{risk:.5f}* ({risk/entry*100:.2f}%)\n"
                f"📈 Reward: *{reward:.5f}* ({reward/entry*100:.2f}%)\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{rr_emoji} *R:R Ratio: 1:{rr_ratio:.2f}*\n\n"
                f"{'✅ Good trade setup!' if rr_ratio >= 2 else '⚠️ Consider improving R:R' if rr_ratio >= 1 else '❌ Poor R:R ratio!'}",
                parse_mode="Markdown"
            )
        except (ValueError, ZeroDivisionError):
            await update.message.reply_text("❌ Valid prices enter karein.", parse_mode="Markdown")

    # ═══ COMPOUND CALCULATOR ═══

    async def compound_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "📈 *Compound Interest Calculator*\n\n"
                "Usage: `/compound <balance> <monthly_%> <months>`\n"
                "Example: `/compound 10000 5 12`\n\n"
                "_Monthly return % se 1 saal ki projection_",
                parse_mode="Markdown"
            )
            return

        try:
            balance, monthly_pct, months = float(args[0]), float(args[1]), int(args[2])
            current = balance
            projections = []
            for m in range(1, min(months + 1, 13)):
                current *= (1 + monthly_pct / 100)
                projections.append((m, current))

            total_return = ((projections[-1][1] - balance) / balance * 100) if projections else 0

            msg = (
                f"📈 *Compound Projection*\n"
                f"Initial: ${balance:,.2f} | Monthly: {monthly_pct}%\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
            )
            for m, val in projections[:12]:
                msg += f"Month {m:2d}: *${val:,.2f}*\n"

            msg += (
                f"\n━━━━━━━━━━━━━━━━━━\n"
                f"💰 *Final: ${projections[-1][1]:,.2f}*\n"
                f"📈 *Total Return: +{total_return:.1f}%*"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Sahi format: `/compound 10000 5 12`", parse_mode="Markdown")

    # ═══ PIP VALUE CALCULATOR ═══

    async def pip_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if not args:
            msg = "💹 *Pip Values (per standard lot, USD)*\n\n"
            for pair, val in list(PIP_VALUES.items())[:10]:
                msg += f"`{pair}`: *${val:.2f}/pip*\n"
            msg += "\n_Usage: `/pipvalue EURUSD 0.1` for custom lot_"
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

        pair = args[0].upper()
        lot = float(args[1]) if len(args) > 1 else 1.0
        pip_val = PIP_VALUES.get(pair, 10.0) * lot

        await update.message.reply_text(
            f"💹 *Pip Value*\n\n"
            f"💱 Pair: *{pair}*\n"
            f"📦 Lot: *{lot}*\n"
            f"💰 *1 pip = ${pip_val:.2f}*",
            parse_mode="Markdown"
        )

    # ═══ BREAK-EVEN CALCULATOR ═══

    async def breakeven_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "📊 *Break-Even Calculator*\n\n"
                "Usage: `/breakeven <win_rate_%> <risk_reward>`\n"
                "Example: `/breakeven 50 2`\n\n"
                "_50% win rate aur 1:2 R:R ke saath kya hota hai_",
                parse_mode="Markdown"
            )
            return

        try:
            win_rate = float(args[0]) / 100
            rr = float(args[1])
            expected_value = (win_rate * rr) - ((1 - win_rate) * 1)
            break_even_wr = 1 / (1 + rr) * 100

            ev_emoji = "✅" if expected_value > 0 else "❌"

            await update.message.reply_text(
                f"📊 *Break-Even Analysis*\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"🎯 Win Rate: *{win_rate*100}%*\n"
                f"⚖️ R:R Ratio: *1:{rr}*\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📉 Break-Even WR: *{break_even_wr:.1f}%*\n"
                f"{ev_emoji} Expected Value per trade: *{expected_value:.2f}R*\n\n"
                f"{'✅ Positive edge! Strategy profitable.' if expected_value > 0 else '❌ Negative edge! Strategy unprofitable.'}",
                parse_mode="Markdown"
            )
        except (ValueError, ZeroDivisionError):
            await update.message.reply_text("❌ Valid values enter karein.", parse_mode="Markdown")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("❌ Calculator cancel ho gaya.")
        return ConversationHandler.END
