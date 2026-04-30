"""
⚙️ CONFIGURATION SETTINGS
ForexBot Pro Configuration
"""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Main configuration class"""

    # Bot Settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_USER_ID: int = int(os.getenv("ADMIN_USER_ID", "0"))

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/trades.db")

    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

    # Trading Defaults
    DEFAULT_RISK_PERCENT: float = float(os.getenv("DEFAULT_RISK_PERCENT", "1.0"))
    DEFAULT_ACCOUNT_BALANCE: float = float(os.getenv("DEFAULT_ACCOUNT_BALANCE", "10000"))
    DEFAULT_BASE_CURRENCY: str = os.getenv("DEFAULT_BASE_CURRENCY", "USD")

    # Scheduled Tasks
    DAILY_SUMMARY_TIME: str = "23:59"
    WEEKLY_REPORT_DAY: str = "sunday"
    WEEKLY_REPORT_TIME: str = "20:00"

    # Chart Settings
    CHART_STYLE: str = "dark_background"
    CHART_DPI: int = 150
    CHART_TEMP_DIR: str = "data/charts"

    # Alert Check Interval (seconds)
    ALERT_CHECK_INTERVAL: int = 60

    # Supported Currency Pairs
    MAJOR_PAIRS: List[str] = None
    MINOR_PAIRS: List[str] = None
    EXOTIC_PAIRS: List[str] = None
    COMMODITIES: List[str] = None
    CRYPTO: List[str] = None

    def __post_init__(self):
        self.MAJOR_PAIRS = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
            "AUDUSD", "USDCAD", "NZDUSD"
        ]
        self.MINOR_PAIRS = [
            "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
            "CADJPY", "CHFJPY", "EURCHF", "GBPCHF",
            "AUDCAD", "AUDCHF", "AUDNZD", "CADCHF",
            "EURAUD", "EURCAD", "EURNZD", "GBPAUD",
            "GBPCAD", "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY"
        ]
        self.EXOTIC_PAIRS = [
            "USDINR", "USDSGD", "USDHKD", "USDMXN",
            "USDZAR", "USDTRY", "USDBRL", "USDCNH"
        ]
        self.COMMODITIES = [
            "XAUUSD",  # Gold
            "XAGUSD",  # Silver
            "XPTUSD",  # Platinum
            "XPDUSD",  # Palladium
            "USOIL",   # Crude Oil
            "UKOIL",   # Brent Oil
        ]
        self.CRYPTO = [
            "BTCUSD",  # Bitcoin
            "ETHUSD",  # Ethereum
            "BNBUSD",  # Binance Coin
            "XRPUSD",  # Ripple
            "ADAUSD",  # Cardano
            "SOLUSD",  # Solana
        ]

        # Create directories
        os.makedirs("data/charts", exist_ok=True)
        os.makedirs("data/exports", exist_ok=True)
        os.makedirs("data/backups", exist_ok=True)
        os.makedirs("data", exist_ok=True)

    @property
    def ALL_PAIRS(self) -> List[str]:
        return self.MAJOR_PAIRS + self.MINOR_PAIRS + self.EXOTIC_PAIRS + self.COMMODITIES + self.CRYPTO

    def is_valid_pair(self, pair: str) -> bool:
        return pair.upper() in self.ALL_PAIRS


# Pip values for major pairs (per standard lot, in USD)
PIP_VALUES = {
    "EURUSD": 10.0, "GBPUSD": 10.0, "AUDUSD": 10.0, "NZDUSD": 10.0,
    "USDJPY": 9.09, "USDCHF": 10.10, "USDCAD": 7.69,
    "EURGBP": 12.75, "EURJPY": 9.09, "GBPJPY": 9.09,
    "AUDJPY": 9.09, "CADJPY": 9.09, "CHFJPY": 9.09,
    "EURCHF": 10.10, "GBPCHF": 10.10,
    "XAUUSD": 10.0, "XAGUSD": 50.0,  # Gold & Silver
    "BTCUSD": 10.0, "ETHUSD": 10.0,  # Crypto
}

# Market session times (UTC)
MARKET_SESSIONS = {
    "Tokyo": {"open": "00:00", "close": "09:00", "emoji": "🇯🇵"},
    "London": {"open": "08:00", "close": "17:00", "emoji": "🇬🇧"},
    "New York": {"open": "13:00", "close": "22:00", "emoji": "🇺🇸"},
    "Sydney": {"open": "22:00", "close": "07:00", "emoji": "🇦🇺"},
}

# Conversation states
(
    TRADE_PAIR, TRADE_DIRECTION, TRADE_ENTRY, TRADE_EXIT,
    TRADE_LOT, TRADE_PNL, TRADE_STRATEGY, TRADE_NOTES,
    EDIT_FIELD, EDIT_VALUE,
    LOTSIZE_BALANCE, LOTSIZE_RISK, LOTSIZE_PAIR, LOTSIZE_SL,
    PNL_PAIR, PNL_LOT, PNL_ENTRY, PNL_EXIT, PNL_DIRECTION,
    GOAL_TYPE, GOAL_AMOUNT, GOAL_DATES,
    ALERT_PAIR, ALERT_PRICE, ALERT_CONDITION,
    JOURNAL_CONTENT, JOURNAL_TAGS,
    IDEA_PAIR, IDEA_CONTENT,
    MAXLOSS_AMOUNT, MAXLOSS_TYPE,
    REMINDER_TEXT, REMINDER_TIME,
) = range(33)
