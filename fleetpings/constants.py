"""
Constants
"""

DISCORD_WEBHOOK_REGEX = r"https:\/\/discord\.com\/api\/webhooks\/[\d]+\/[a-zA-Z0-9_-]+$"

PRESET_REMINDER_INTERVALS = (
    (1440, "24h"),
    (720, "12h"),
    (480, "8h"),
    (180, "3h"),
    (60, "1h"),
    (15, "15m"),
)

# All internal URLs need to start with this prefix
INTERNAL_URL_PREFIX = "-"
