# ============================================================
#  config.py — Configuración centralizada del bot
#  Todos los valores se cargan desde variables de entorno (.env)
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

def _get_int(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default

def _get_int_list(key: str) -> list[int]:
    raw = os.getenv(key, "")
    if not raw.strip():
        return []
    try:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError:
        return []

# ── IDs de canales ───────────────────────────────────────────
WELCOME_CHANNEL_ID  = _get_int("WELCOME_CHANNEL_ID")
WARN_CHANNEL_ID     = _get_int("WARN_CHANNEL_ID")
ECO_CHANNEL_ID      = _get_int("ECO_CHANNEL_ID")   # Canal exclusivo para comandos de economía

# ── IDs de categorías / roles ────────────────────────────────
TICKET_CATEGORY_ID  = _get_int("TICKET_CATEGORY_ID")
MOD_ROLE_ID         = _get_int("MOD_ROLE_ID")
ROLES_IDS           = _get_int_list("ROLES_IDS")

# ── Usuarios especiales ──────────────────────────────────────
USER_ID_NO_MENCIONAR = _get_int("USER_ID_NO_MENCIONAR")  # 0 = desactivado

# ── Presencia del bot ────────────────────────────────────────
BOT_STREAMING_NAME = os.getenv("BOT_STREAMING_NAME", "Mi Bot")
BOT_STREAMING_URL  = os.getenv("BOT_STREAMING_URL",  "https://www.twitch.tv/")

# ── Servidor ─────────────────────────────────────────────────
SERVER_NAME      = os.getenv("SERVER_NAME",      "Mi Servidor")
WELCOME_IMAGE_URL = os.getenv("WELCOME_IMAGE_URL", "")
SERVER_LOGO_URL   = os.getenv("SERVER_LOGO_URL",   "")

# ── Economía ─────────────────────────────────────────────────
ECO_DB_NAME  = "economy.db"
WARN_DB_NAME = "warnings.db"
DAILY_AMOUNT = _get_int("DAILY_AMOUNT", 200)
WORK_MIN     = _get_int("WORK_MIN",     100)
WORK_MAX     = _get_int("WORK_MAX",     500)
