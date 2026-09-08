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

# Fleet types that used to be hardcoded in the form template. They are seeded as real
# rows by migration 0022 so they can carry a reminder policy, and are hidden again when
# the "Use default fleet types" setting is switched off.
DEFAULT_FLEET_TYPES = (
    ("Roaming", "#81FD2D"),
    ("Home Defense", "#F1C40F"),
    ("StratOP", "#E67E22"),
    ("CTA", "#E91E63"),
)

DEFAULT_FLEET_TYPE_NAMES = tuple(name for name, _embed_color in DEFAULT_FLEET_TYPES)

# All internal URLs need to start with this prefix
INTERNAL_URL_PREFIX = "-"
