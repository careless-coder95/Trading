"""
✨ MESSAGE FORMATTERS
ForexBot Pro - Telegram Message Formatting Utilities
"""

from typing import List, Dict, Optional
from datetime import datetime


def format_stats(stats: Dict) -> str:
    """Format quick statistics message"""
    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    pnl = stats.get("total_pnl", 0)
    avg_win = stats.get("avg_win", 0)
    avg_loss = stats.get("avg_loss", 0)
    profit_factor = stats.get("profit_factor", 0)
    best_pair = stats.get("best_pair", "N/A")

    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
    pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

    pf_str = f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞"

    # Win rate bar
    bar_filled = int(win_rate / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    return (
        f"📊 *Trading Statistics*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Total Trades: *{total}*\n"
        f"✅ Wins: *{wins}*  |  ❌ Losses: *{losses}*\n"
        f"🎯 Win Rate: *{win_rate:.1f}%*\n"
        f"`{bar}`\n\n"
        f"{pnl_emoji} Total P&L: *{pnl_str}*\n"
        f"💰 Avg Win: *+${avg_win:.2f}*\n"
        f"📉 Avg Loss: *-${avg_loss:.2f}*\n"
        f"📊 Profit Factor: *{pf_str}*\n\n"
        f"💎 Best Pair: *{best_pair}*\n\n"
        f"_/report ke liye detailed view_ | _/equity ke liye chart_"
    )


def format_trade_list(trades: List[Dict]) -> str:
    """Format a list of trades for display"""
    if not trades:
        return "📭 Koi trade nahi mila!"

    msg = f"📋 *Recent Trades* (last {len(trades)})\n" + "━" * 30 + "\n\n"

    for t in trades:
        pnl = t.get("profit_loss", 0)
        pnl_emoji = "💰" if pnl >= 0 else "📉"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        direction_emoji = "📈" if t.get("direction") == "BUY" else "📉"
        status = t.get("status", "CLOSED")
        status_badge = "🟢" if status == "OPEN" else "⚫"

        entry_time = t.get("entry_time", "")
        date_str = entry_time[:10] if entry_time else "N/A"

        msg += (
            f"{status_badge} *#{t['id']}* {direction_emoji} *{t['pair']}* {t['direction']}\n"
            f"  📅 {date_str} | 📦 {t.get('lot_size', 0)} lots\n"
            f"  🔵 Entry: `{t.get('entry_price', 'N/A')}` → 🔴 Exit: `{t.get('exit_price', 'Open')}`\n"
            f"  {pnl_emoji} P&L: *{pnl_str}*"
        )
        if t.get("strategy"):
            msg += f" | 📋 {t['strategy']}"
        msg += "\n\n"

    msg += "_`/edittrade <id>` se edit karein_"
    return msg


def format_trade_detail(trade: Dict) -> str:
    """Format a single trade in detail"""
    pnl = trade.get("profit_loss", 0)
    pnl_emoji = "💰" if pnl >= 0 else "📉"
    pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

    entry_time = trade.get("entry_time", "N/A")
    exit_time = trade.get("exit_time", "N/A") or "Open"

    return (
        f"📊 *Trade #{trade['id']} Details*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💱 Pair: *{trade['pair']}*\n"
        f"📊 Direction: *{trade['direction']}*\n"
        f"🔵 Entry: *{trade.get('entry_price', 'N/A')}*\n"
        f"🔴 Exit: *{trade.get('exit_price', 'Open')}*\n"
        f"🛑 SL: *{trade.get('sl_price', 'N/A')}*\n"
        f"🎯 TP: *{trade.get('tp_price', 'N/A')}*\n"
        f"📦 Lot: *{trade.get('lot_size', 'N/A')}*\n"
        f"📐 Pips: *{trade.get('pips', 0):.1f}*\n"
        f"{pnl_emoji} P&L: *{pnl_str}*\n\n"
        f"📋 Strategy: *{trade.get('strategy', 'N/A') or 'N/A'}*\n"
        f"📝 Notes: _{trade.get('notes', 'None') or 'None'}_\n\n"
        f"⏰ Entry Time: `{str(entry_time)[:16]}`\n"
        f"⏰ Exit Time: `{str(exit_time)[:16]}`\n"
        f"📌 Status: *{trade.get('status', 'N/A')}*"
    )


def format_trade_confirmation(trade_data: Dict, trade_id: int) -> str:
    """Format trade confirmation after quick-add"""
    pnl = trade_data.get("profit_loss", 0)
    pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

    sl_str = f"`{trade_data['sl_price']}`" if trade_data.get("sl_price") else "_Not set_"
    tp_str = f"`{trade_data['tp_price']}`" if trade_data.get("tp_price") else "_Not set_"

    return (
        f"✅ *Trade #{trade_id} Logged!*\n\n"
        f"💱 *{trade_data['pair']}* {trade_data['direction']}\n"
        f"🔵 Entry: `{trade_data['entry_price']}`\n"
        f"🛑 SL: {sl_str}\n"
        f"🎯 TP: {tp_str}\n"
        f"📦 Lot: `{trade_data.get('lot_size', 0.01)}`\n\n"
        f"_Trade saved! `/trades` se dekhein._"
    )


def format_detailed_report(
    stats: Dict,
    trades: List[Dict],
    title: str,
    start_date: str,
    end_date: str
) -> str:
    """Format a detailed weekly/monthly report"""
    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    pnl = stats.get("total_pnl", 0)
    avg_win = stats.get("avg_win", 0)
    avg_loss = stats.get("avg_loss", 0)
    profit_factor = stats.get("profit_factor", 0)
    best_pair = stats.get("best_pair", "N/A")
    worst_pair = stats.get("worst_pair", "N/A")

    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
    pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
    pf_str = f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞"

    # Best trades
    top_trades = sorted(trades, key=lambda x: x.get("profit_loss", 0), reverse=True)
    best_trade = top_trades[0] if top_trades else None
    worst_trade = top_trades[-1] if top_trades else None

    msg = (
        f"{title}\n"
        f"_{start_date} → {end_date}_\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 *Summary*\n"
        f"Trades: *{total}* | Wins: *{wins}* | Losses: *{losses}*\n"
        f"🎯 Win Rate: *{win_rate:.1f}%*\n"
        f"{pnl_emoji} Total P&L: *{pnl_str}*\n\n"
        f"📊 *Metrics*\n"
        f"Avg Win: *+${avg_win:.2f}* | Avg Loss: *-${avg_loss:.2f}*\n"
        f"Profit Factor: *{pf_str}*\n\n"
        f"💎 Best Pair: *{best_pair}*\n"
        f"💀 Worst Pair: *{worst_pair}*\n"
    )

    if best_trade:
        bt_pnl = best_trade.get("profit_loss", 0)
        msg += f"\n🏆 Best Trade: #{best_trade['id']} {best_trade['pair']} *+${bt_pnl:.2f}*\n"

    if worst_trade and worst_trade != best_trade:
        wt_pnl = worst_trade.get("profit_loss", 0)
        msg += f"💀 Worst Trade: #{worst_trade['id']} {worst_trade['pair']} *-${abs(wt_pnl):.2f}*\n"

    msg += "\n_/equity se equity curve dekhein_ 📈"
    return msg
