"""
✅ INPUT VALIDATORS
ForexBot Pro - Input Validation Utilities
"""

import re
from typing import Optional, Dict

# All valid trading pairs (from config)
VALID_PAIRS = [
    # Major Pairs
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD",
    # Minor Pairs
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
    "CADJPY", "CHFJPY", "EURCHF", "GBPCHF",
    "AUDCAD", "AUDCHF", "AUDNZD", "CADCHF",
    "EURAUD", "EURCAD", "EURNZD", "GBPAUD",
    "GBPCAD", "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY",
    # Exotic Pairs
    "USDINR", "USDSGD", "USDHKD", "USDMXN",
    "USDZAR", "USDTRY", "USDBRL", "USDCNH",
    # Commodities
    "XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD",
    "USOIL", "UKOIL",
    # Crypto
    "BTCUSD", "ETHUSD", "BNBUSD", "XRPUSD",
    "ADAUSD", "SOLUSD",
]


def validate_pair(pair: str) -> bool:
    """Validate if a currency pair is supported"""
    return pair.upper().strip() in VALID_PAIRS


def validate_price(price_str: str) -> Optional[float]:
    """Validate and parse a price string. Returns float or None."""
    try:
        price = float(price_str.strip())
        if price <= 0:
            return None
        return price
    except ValueError:
        return None


def validate_lot(lot_str: str) -> Optional[float]:
    """Validate lot size. Returns float or None."""
    try:
        lot = float(lot_str.strip())
        if lot <= 0 or lot > 1000:
            return None
        return lot
    except ValueError:
        return None


def validate_percentage(pct_str: str) -> Optional[float]:
    """Validate percentage value (0-100). Returns float or None."""
    try:
        pct = float(pct_str.strip().replace("%", ""))
        if pct <= 0 or pct > 100:
            return None
        return pct
    except ValueError:
        return None


def validate_date(date_str: str) -> bool:
    """Validate YYYY-MM-DD date format"""
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        return False
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """Validate HH:MM time format"""
    pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
    return bool(re.match(pattern, time_str.strip()))


def parse_quick_trade(text: str) -> Optional[Dict]:
    """
    Parse quick trade format:
    EURUSD BUY 1.0850 SL:1.0830 TP:1.0890
    Returns dict or None if format invalid.
    """
    try:
        parts = text.upper().strip().split()
        if len(parts) < 3:
            return None

        pair = parts[0]
        if not validate_pair(pair):
            return None

        direction = parts[1]
        if direction not in ["BUY", "SELL"]:
            return None

        entry = validate_price(parts[2])
        if not entry:
            return None

        trade = {
            "pair": pair,
            "direction": direction,
            "entry_price": entry,
            "status": "OPEN",
            "lot_size": 0.01,
            "profit_loss": 0,
            "sl_price": None,
            "tp_price": None,
        }

        # Parse optional SL and TP
        for part in parts[3:]:
            if part.startswith("SL:"):
                sl = validate_price(part[3:])
                if sl:
                    trade["sl_price"] = sl
            elif part.startswith("TP:"):
                tp = validate_price(part[3:])
                if tp:
                    trade["tp_price"] = tp
            elif part.startswith("LOT:"):
                lot = validate_lot(part[4:])
                if lot:
                    trade["lot_size"] = lot

        return trade

    except Exception:
        return None


def sanitize_text(text: str, max_length: int = 500) -> str:
    """Sanitize user text input"""
    if not text:
        return ""
    # Remove SQL injection attempts (basic)
    text = text.replace("'", "''")
    # Trim whitespace and limit length
    return text.strip()[:max_length]
