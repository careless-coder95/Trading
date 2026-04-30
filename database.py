"""
💾 DATABASE OPERATIONS
SQLite database management for ForexBot Pro
"""

import sqlite3
import logging
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from config import Config

logger = logging.getLogger(__name__)
config = Config()


class Database:
    """SQLite database handler"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """Create all tables"""
        with self.get_connection() as conn:
            conn.executescript("""
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    account_balance REAL DEFAULT 10000,
                    base_currency TEXT DEFAULT 'USD',
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    default_risk_percent REAL DEFAULT 1.0,
                    max_daily_loss REAL DEFAULT 0,
                    max_weekly_loss REAL DEFAULT 0,
                    notifications_enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Trades table
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pair TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('BUY', 'SELL')),
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    lot_size REAL NOT NULL,
                    profit_loss REAL DEFAULT 0,
                    pips REAL DEFAULT 0,
                    strategy TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    status TEXT DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED', 'CANCELLED')),
                    sl_price REAL,
                    tp_price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Goals table
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_type TEXT NOT NULL CHECK(goal_type IN ('daily', 'weekly', 'monthly')),
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    achieved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Alerts table
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pair TEXT NOT NULL,
                    price REAL NOT NULL,
                    condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
                    active INTEGER DEFAULT 1,
                    triggered_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Journal table
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    entry_date DATE DEFAULT (date('now')),
                    entry_type TEXT DEFAULT 'journal' CHECK(entry_type IN ('journal', 'idea', 'note')),
                    content TEXT NOT NULL,
                    pair TEXT DEFAULT '',
                    tags TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Reminders table
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reminder_text TEXT NOT NULL,
                    remind_at TIMESTAMP NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Settings table
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    account_balance REAL DEFAULT 10000,
                    base_currency TEXT DEFAULT 'USD',
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    default_risk REAL DEFAULT 1.0,
                    notifications INTEGER DEFAULT 1,
                    weekly_report_day TEXT DEFAULT 'sunday',
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);
                CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(entry_time);
                CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id, active);
                CREATE INDEX IF NOT EXISTS idx_journal_user ON journal(user_id);
            """)
        logger.info("✅ Database tables created successfully")

    # ═══════════════════════════════════════
    # TRADE OPERATIONS
    # ═══════════════════════════════════════

    def add_trade(self, user_id: int, trade_data: Dict) -> int:
        """Add a new trade"""
        self.ensure_user(user_id)
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO trades 
                (user_id, pair, direction, entry_price, exit_price, lot_size,
                 profit_loss, pips, strategy, notes, entry_time, exit_time, 
                 status, sl_price, tp_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                trade_data.get("pair", "").upper(),
                trade_data.get("direction", "BUY").upper(),
                trade_data.get("entry_price", 0),
                trade_data.get("exit_price"),
                trade_data.get("lot_size", 0.01),
                trade_data.get("profit_loss", 0),
                trade_data.get("pips", 0),
                trade_data.get("strategy", ""),
                trade_data.get("notes", ""),
                trade_data.get("entry_time", datetime.now()),
                trade_data.get("exit_time"),
                trade_data.get("status", "CLOSED"),
                trade_data.get("sl_price"),
                trade_data.get("tp_price"),
            ))
            return cursor.lastrowid

    def get_trades(self, user_id: int, limit: int = 10,
                   start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get trades for a user"""
        query = "SELECT * FROM trades WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND date(entry_time) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date(entry_time) <= ?"
            params.append(end_date)

        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_trade_by_id(self, trade_id: int, user_id: int) -> Optional[Dict]:
        """Get specific trade"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM trades WHERE id = ? AND user_id = ?",
                (trade_id, user_id)
            ).fetchone()
            return dict(row) if row else None

    def update_trade(self, trade_id: int, user_id: int, updates: Dict) -> bool:
        """Update a trade"""
        allowed = ["exit_price", "lot_size", "profit_loss", "pips",
                   "strategy", "notes", "exit_time", "status", "sl_price", "tp_price"]
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in filtered])
        values = list(filtered.values()) + [trade_id, user_id]

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE trades SET {set_clause} WHERE id = ? AND user_id = ?",
                values
            )
        return True

    def delete_trade(self, trade_id: int, user_id: int) -> bool:
        """Delete a trade"""
        with self.get_connection() as conn:
            result = conn.execute(
                "DELETE FROM trades WHERE id = ? AND user_id = ?",
                (trade_id, user_id)
            )
            return result.rowcount > 0

    def get_stats(self, user_id: int, start_date: str = None, end_date: str = None) -> Dict:
        """Get trading statistics"""
        query = "SELECT * FROM trades WHERE user_id = ? AND status = 'CLOSED'"
        params = [user_id]

        if start_date:
            query += " AND date(entry_time) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date(entry_time) <= ?"
            params.append(end_date)

        with self.get_connection() as conn:
            trades = [dict(r) for r in conn.execute(query, params).fetchall()]

        if not trades:
            return {"total_trades": 0, "win_rate": 0, "total_pnl": 0,
                    "avg_win": 0, "avg_loss": 0, "profit_factor": 0,
                    "best_pair": "N/A", "worst_pair": "N/A", "wins": 0, "losses": 0}

        wins = [t for t in trades if t["profit_loss"] > 0]
        losses = [t for t in trades if t["profit_loss"] < 0]

        total_pnl = sum(t["profit_loss"] for t in trades)
        total_wins = sum(t["profit_loss"] for t in wins)
        total_losses = abs(sum(t["profit_loss"] for t in losses))

        # Best/worst pairs
        pair_pnl = {}
        for t in trades:
            pair_pnl[t["pair"]] = pair_pnl.get(t["pair"], 0) + t["profit_loss"]

        best_pair = max(pair_pnl, key=pair_pnl.get) if pair_pnl else "N/A"
        worst_pair = min(pair_pnl, key=pair_pnl.get) if pair_pnl else "N/A"

        return {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / len(trades) * 100) if trades else 0,
            "total_pnl": total_pnl,
            "avg_win": (total_wins / len(wins)) if wins else 0,
            "avg_loss": (total_losses / len(losses)) if losses else 0,
            "profit_factor": (total_wins / total_losses) if total_losses > 0 else float('inf'),
            "best_pair": best_pair,
            "worst_pair": worst_pair,
            "best_pair_pnl": pair_pnl.get(best_pair, 0),
            "worst_pair_pnl": pair_pnl.get(worst_pair, 0),
        }

    def get_equity_curve(self, user_id: int) -> List[Dict]:
        """Get all closed trades for equity curve (returns list of dicts)"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT profit_loss, exit_time, entry_time, pair, direction
                FROM trades
                WHERE user_id = ? AND status = 'CLOSED'
                ORDER BY COALESCE(exit_time, entry_time)
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_monthly_pnl(self, user_id: int, year: int) -> List[Dict]:
        """Get monthly P&L breakdown"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT strftime('%m', entry_time) as month,
                       SUM(profit_loss) as total_pnl,
                       COUNT(*) as trade_count,
                       SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins
                FROM trades
                WHERE user_id = ? AND status = 'CLOSED'
                AND strftime('%Y', entry_time) = ?
                GROUP BY month
                ORDER BY month
            """, (user_id, str(year))).fetchall()
            return [dict(r) for r in rows]

    # ═══════════════════════════════════════
    # GOALS OPERATIONS
    # ═══════════════════════════════════════

    def add_goal(self, user_id: int, goal_data: Dict) -> int:
        """Add a new goal"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO goals (user_id, goal_type, target_amount, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, goal_data["type"], goal_data["target"],
                  goal_data["start_date"], goal_data["end_date"]))
            return cursor.lastrowid

    def get_goals(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get user goals"""
        query = "SELECT * FROM goals WHERE user_id = ?"
        params = [user_id]
        if active_only:
            query += " AND date(end_date) >= date('now')"
        query += " ORDER BY created_at DESC"

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def update_goal_progress(self, user_id: int) -> None:
        """Update goal progress based on current trades"""
        with self.get_connection() as conn:
            goals = conn.execute(
                "SELECT * FROM goals WHERE user_id = ? AND date(end_date) >= date('now')",
                (user_id,)
            ).fetchall()

            for goal in goals:
                pnl = conn.execute("""
                    SELECT COALESCE(SUM(profit_loss), 0) as total
                    FROM trades
                    WHERE user_id = ? AND status = 'CLOSED'
                    AND date(entry_time) BETWEEN ? AND ?
                """, (user_id, goal["start_date"], goal["end_date"])).fetchone()["total"]

                achieved = 1 if pnl >= goal["target_amount"] else 0
                conn.execute(
                    "UPDATE goals SET current_amount = ?, achieved = ? WHERE id = ?",
                    (pnl, achieved, goal["id"])
                )

    # ═══════════════════════════════════════
    # ALERTS OPERATIONS
    # ═══════════════════════════════════════

    def add_alert(self, user_id: int, pair: str, price: float, condition: str) -> int:
        """Add price alert"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO alerts (user_id, pair, price, condition)
                VALUES (?, ?, ?, ?)
            """, (user_id, pair.upper(), price, condition))
            return cursor.lastrowid

    def get_alerts(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get user alerts"""
        query = "SELECT * FROM alerts WHERE user_id = ?"
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY created_at DESC"

        with self.get_connection() as conn:
            rows = conn.execute(query, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_all_active_alerts(self) -> List[Dict]:
        """Get all active alerts (for scheduler)"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE active = 1"
            ).fetchall()
            return [dict(r) for r in rows]

    def deactivate_alert(self, alert_id: int) -> None:
        """Mark alert as triggered"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE alerts SET active = 0, triggered_at = ? WHERE id = ?",
                (datetime.now(), alert_id)
            )

    def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert"""
        with self.get_connection() as conn:
            result = conn.execute(
                "DELETE FROM alerts WHERE id = ? AND user_id = ?",
                (alert_id, user_id)
            )
            return result.rowcount > 0

    # ═══════════════════════════════════════
    # JOURNAL OPERATIONS
    # ═══════════════════════════════════════

    def add_journal(self, user_id: int, content: str,
                    entry_type: str = "journal", pair: str = "", tags: str = "") -> int:
        """Add journal entry"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO journal (user_id, content, entry_type, pair, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, content, entry_type, pair, tags))
            return cursor.lastrowid

    def get_journal(self, user_id: int, entry_type: str = None,
                    limit: int = 10) -> List[Dict]:
        """Get journal entries"""
        query = "SELECT * FROM journal WHERE user_id = ?"
        params = [user_id]
        if entry_type:
            query += " AND entry_type = ?"
            params.append(entry_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # ═══════════════════════════════════════
    # USER OPERATIONS
    # ═══════════════════════════════════════

    def ensure_user(self, user_id: int, username: str = "", first_name: str = "") -> None:
        """Ensure user exists in database"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            """, (user_id, username, first_name))

    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings including max_loss limits"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

        if row:
            d = dict(row)
            d.setdefault("max_loss_daily", 0)
            d.setdefault("max_loss_weekly", 0)
            d.setdefault("max_loss_monthly", 0)
            return d
        return {
            "account_balance": 10000,
            "base_currency": "USD",
            "timezone": "Asia/Kolkata",
            "default_risk_percent": 1.0,
            "max_loss_daily": 0,
            "max_loss_weekly": 0,
            "max_loss_monthly": 0,
        }

    def update_user_setting(self, user_id: int, key: str, value: Any) -> None:
        """Update a user setting"""
        allowed_keys = ["account_balance", "base_currency", "timezone",
                        "default_risk_percent", "max_daily_loss", "max_weekly_loss"]
        if key not in allowed_keys:
            return

        with self.get_connection() as conn:
            conn.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))

    def get_streak(self, user_id: int) -> Dict:
        """Calculate win/loss streak with full stats"""
        with self.get_connection() as conn:
            trades = conn.execute("""
                SELECT profit_loss FROM trades
                WHERE user_id = ? AND status = 'CLOSED'
                ORDER BY COALESCE(exit_time, entry_time) DESC
                LIMIT 100
            """, (user_id,)).fetchall()

        if not trades:
            return {
                "current_streak": 0,
                "streak_type": "none",
                "longest_win_streak": 0,
                "longest_loss_streak": 0,
            }

        results = [1 if t["profit_loss"] > 0 else -1 for t in trades]

        current_streak = 1
        for i in range(1, len(results)):
            if results[i] == results[0]:
                current_streak += 1
            else:
                break

        streak_type = "win" if results[0] > 0 else "loss"

        max_win = cur_win = 0
        max_loss = cur_loss = 0
        for r in reversed(results):
            if r > 0:
                cur_win += 1
                cur_loss = 0
                max_win = max(max_win, cur_win)
            else:
                cur_loss += 1
                cur_win = 0
                max_loss = max(max_loss, cur_loss)

        return {
            "current_streak": current_streak,
            "streak_type": streak_type,
            "longest_win_streak": max_win,
            "longest_loss_streak": max_loss,
        }

    # ═══════════════════════════════════════
    # MISSING METHODS — ADDED
    # ═══════════════════════════════════════

    def set_goal(self, user_id: int, goal_type: str, target_amount: float,
                 start_date, end_date) -> int:
        """Create a new goal (called by goals.py)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO goals (user_id, goal_type, target_amount, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, goal_type, target_amount, str(start_date), str(end_date)))
            return cursor.lastrowid

    def set_max_loss_limit(self, user_id: int, limit_type: str, amount: float) -> None:
        """Save max loss limit (called by risk.py)"""
        col_map = {
            "daily":   "max_loss_daily",
            "weekly":  "max_loss_weekly",
            "monthly": "max_loss_monthly",
        }
        col = col_map.get(limit_type)
        if not col:
            return
        with self.get_connection() as conn:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} REAL DEFAULT 0")
            except Exception:
                pass  # Column already exists
            conn.execute(
                f"UPDATE users SET {col} = ? WHERE user_id = ?",
                (amount, user_id)
            )

    def add_journal_entry(self, user_id: int, entry_date, content: str,
                          tags: str = "") -> int:
        """Add a journal entry (called by journal.py)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO journal (user_id, entry_date, content, tags, entry_type)
                VALUES (?, ?, ?, ?, 'journal')
            """, (user_id, str(entry_date), content, tags))
            return cursor.lastrowid

    def get_journal_entries(self, user_id: int, limit: int = 10,
                            date_filter: str = None) -> List[Dict]:
        """Get journal entries (called by journal.py)"""
        query = """
            SELECT id, entry_date, content, tags, created_at
            FROM journal
            WHERE user_id = ? AND entry_type = 'journal'
        """
        params: list = [user_id]
        if date_filter:
            query += " AND entry_date = ?"
            params.append(date_filter)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def add_trade_idea(self, user_id: int, pair: str, content: str) -> int:
        """Save a trade idea (called by journal.py)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO journal (user_id, content, pair, entry_type)
                VALUES (?, ?, ?, 'idea')
            """, (user_id, content, pair.upper()))
            return cursor.lastrowid

    def get_drawdown(self, user_id: int) -> Dict:
        """Calculate current drawdown"""
        settings = self.get_user_settings(user_id)
        balance = settings.get("account_balance", 10000)

        with self.get_connection() as conn:
            trades = conn.execute("""
                SELECT profit_loss, entry_time FROM trades
                WHERE user_id = ? AND status = 'CLOSED'
                ORDER BY entry_time
            """, (user_id,)).fetchall()

        if not trades:
            return {"current_dd": 0, "max_dd": 0, "current_dd_pct": 0}

        equity = balance
        peak = balance
        max_dd = 0

        for t in trades:
            equity += t["profit_loss"]
            if equity > peak:
                peak = equity
            dd = peak - equity
            max_dd = max(max_dd, dd)

        current_dd = peak - equity
        current_dd_pct = (current_dd / peak * 100) if peak > 0 else 0

        return {
            "current_dd": current_dd,
            "max_dd": max_dd,
            "current_dd_pct": current_dd_pct,
            "current_equity": equity,
            "peak_equity": peak,
        }

    def get_all_users(self) -> List[int]:
        """Get all user IDs"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
            return [r["user_id"] for r in rows]
