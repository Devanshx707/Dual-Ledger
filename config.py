"""Settings shared by every module: categories, database name, themes, font.

Colors are roles, not fixed values. Other files read them as cfg.WHITE, cfg.TEXT and so on.
apply_theme() swaps the whole palette, so the next screen the app builds uses the new colors.
"""

CATEGORIES = ["Food", "Transport", "Utilities", "Entertainment", "Other"]
INVESTMENT_TYPES = ["Stocks", "Mutual Fund", "SIP", "Fixed Deposit", "Gold", "Crypto", "Other"]
DB_NAME = "finance_tracker.db"
FONT = "Segoe UI"

# Roles. WHITE is the card surface. ONBLUE is text on a blue background. SELECT tints a chosen row.
THEMES = {
    "light": {
        "BLUE": "#2563EB", "BLUE_DARK": "#1D4ED8", "BLUE_LIGHT": "#DBEAFE", "SELECT": "#DBEAFE",
        "ONBLUE": "#FFFFFF", "WHITE": "#FFFFFF", "BG": "#F3F4F6", "INPUT": "#FFFFFF",
        "SIDEBAR": "#2563EB", "SIDE_ACTIVE": "#1D4ED8",
        "BORDER": "#E5E7EB", "TRACK": "#E5E7EB", "HOVER": "#D1D5DB",
        "TEXT": "#1F2937", "MUTED": "#6B7280",
    },
    "dark": {
        "BLUE": "#3B82F6", "BLUE_DARK": "#2563EB", "BLUE_LIGHT": "#DBEAFE", "SELECT": "#1E3A8A",
        "ONBLUE": "#FFFFFF", "WHITE": "#1F2937", "BG": "#111827", "INPUT": "#111827",
        "SIDEBAR": "#172554", "SIDE_ACTIVE": "#1E40AF",
        "BORDER": "#374151", "TRACK": "#374151", "HOVER": "#4B5563",
        "TEXT": "#F3F4F6", "MUTED": "#9CA3AF",
    },
}

THEME = "light"


def apply_theme(name):
    global THEME
    THEME = name if name in THEMES else "light"
    globals().update(THEMES[THEME])


apply_theme("light")
