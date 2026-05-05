# ============================================================
#  database.py — Conexión a BD y clase UserEconomy
# ============================================================

import sqlite3
from datetime import datetime, timedelta
from config import ECO_DB_NAME, WARN_DB_NAME


# ── Economía ─────────────────────────────────────────────────

def get_eco_connection() -> sqlite3.Connection:
    """Devuelve una conexión a la base de datos de economía."""
    conn = sqlite3.connect(ECO_DB_NAME, check_same_thread=False)
    return conn


def init_economy_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Inicializa la BD de economía y devuelve (conn, cursor)."""
    conn = get_eco_connection()
    cur  = conn.cursor()

    cur.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            balance      INTEGER DEFAULT 0,
            bank_balance INTEGER DEFAULT 0,
            last_daily   TEXT,
            last_work    TEXT
        );

        CREATE TABLE IF NOT EXISTS items (
            item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            price       INTEGER,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS inventory (
            user_id  INTEGER,
            item_id  INTEGER,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, item_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        );

        CREATE TABLE IF NOT EXISTS hall_of_fame (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            month   INTEGER,
            year    INTEGER,
            user_id INTEGER,
            balance INTEGER
        );

        CREATE TABLE IF NOT EXISTS task_state (
            key            TEXT PRIMARY KEY,
            last_processed TEXT
        );
    ''')
    conn.commit()

    # Migración: añadir bank_balance si la BD ya existía sin él
    try:
        cur.execute("ALTER TABLE users ADD COLUMN bank_balance INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    return conn, cur


# ── Advertencias ─────────────────────────────────────────────

def get_warn_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Abre una conexión a la BD de advertencias y crea la tabla si no existe."""
    conn = sqlite3.connect(WARN_DB_NAME, check_same_thread=False)
    cur  = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER,
            reason  TEXT
        )
    ''')
    conn.commit()
    return conn, cur


# ── Clase UserEconomy ────────────────────────────────────────

class UserEconomy:
    """Métodos estáticos para gestionar la economía de los usuarios."""

    def __init__(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        self._conn   = conn
        self._cursor = cursor

    # ── Helpers internos ──────────────────────────────────────
    def _get_user(self, user_id: int):
        self._cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self._cursor.fetchone()

    def _ensure_user(self, user_id: int) -> None:
        if not self._get_user(user_id):
            self._cursor.execute(
                "INSERT INTO users (user_id, balance) VALUES (?, 0)", (user_id,)
            )
            self._conn.commit()

    # ── API pública ───────────────────────────────────────────
    def get_balance(self, user_id: int) -> int:
        self._ensure_user(user_id)
        self._cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = self._cursor.fetchone()
        return row[0] if row else 0

    def update_balance(self, user_id: int, amount: int) -> None:
        self._ensure_user(user_id)
        self._cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id)
        )
        self._conn.commit()

    def set_last_daily(self, user_id: int) -> None:
        self._cursor.execute(
            "UPDATE users SET last_daily = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        self._conn.commit()

    def can_claim_daily(self, user_id: int) -> bool:
        self._ensure_user(user_id)
        self._cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
        row = self._cursor.fetchone()
        if not row or not row[0]:
            return True
        return datetime.now() - datetime.fromisoformat(row[0]) >= timedelta(hours=24)

    def set_last_work(self, user_id: int) -> None:
        self._cursor.execute(
            "UPDATE users SET last_work = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        self._conn.commit()

    def can_work(self, user_id: int) -> bool:
        self._ensure_user(user_id)
        self._cursor.execute("SELECT last_work FROM users WHERE user_id = ?", (user_id,))
        row = self._cursor.fetchone()
        if not row or not row[0]:
            return True
        return datetime.now() - datetime.fromisoformat(row[0]) >= timedelta(hours=1)

    def reset_all_balances(self) -> None:
        self._cursor.execute("UPDATE users SET balance = 0, bank_balance = 0")
        self._conn.commit()

    # ── Banco ───────────────────────────────────────────────
    def get_bank_balance(self, user_id: int) -> int:
        self._ensure_user(user_id)
        self._cursor.execute("SELECT bank_balance FROM users WHERE user_id = ?", (user_id,))
        row = self._cursor.fetchone()
        return row[0] if row else 0

    def deposit_bank(self, user_id: int, amount: int) -> None:
        """Mueve monedas de la cartera al banco."""
        self._cursor.execute(
            "UPDATE users SET balance = balance - ?, bank_balance = bank_balance + ? WHERE user_id = ?",
            (amount, amount, user_id)
        )
        self._conn.commit()

    def withdraw_bank(self, user_id: int, amount: int) -> None:
        """Mueve monedas del banco a la cartera."""
        self._cursor.execute(
            "UPDATE users SET balance = balance + ?, bank_balance = bank_balance - ? WHERE user_id = ?",
            (amount, amount, user_id)
        )
        self._conn.commit()

    def count_warns(self, user_id: int) -> int:
        """Cuenta los warns de un usuario desde warnings.db."""
        from config import WARN_DB_NAME
        try:
            conn = sqlite3.connect(WARN_DB_NAME, check_same_thread=False)
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ?", (user_id,))
            count = cur.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def get_top_users(self, limit: int = 10):
        self._cursor.execute(
            "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,)
        )
        return self._cursor.fetchall()

    def save_hall_of_fame(self, month: int, year: int, user_id: int, balance: int) -> None:
        self._cursor.execute(
            "INSERT INTO hall_of_fame (month, year, user_id, balance) VALUES (?, ?, ?, ?)",
            (month, year, user_id, balance)
        )
        self._conn.commit()

    def get_hall_of_fame(self):
        self._cursor.execute(
            "SELECT month, year, user_id, balance FROM hall_of_fame ORDER BY year DESC, month DESC"
        )
        return self._cursor.fetchall()

    def get_task_state(self, key: str):
        self._cursor.execute("SELECT last_processed FROM task_state WHERE key = ?", (key,))
        return self._cursor.fetchone()

    def set_task_state(self, key: str, value: str) -> None:
        self._cursor.execute(
            "REPLACE INTO task_state (key, last_processed) VALUES (?, ?)", (key, value)
        )
        self._conn.commit()

    # ── Tienda e inventario ───────────────────────────────────
    def get_all_items(self):
        self._cursor.execute("SELECT * FROM items")
        return self._cursor.fetchall()

    def get_item(self, item_id: int):
        self._cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        return self._cursor.fetchone()

    def add_item(self, name: str, price: int, description: str) -> None:
        self._cursor.execute(
            "INSERT INTO items (name, price, description) VALUES (?, ?, ?)",
            (name, price, description)
        )
        self._conn.commit()

    def remove_item(self, item_id: int) -> int:
        """Devuelve el número de filas afectadas (0 si no existía)."""
        self._cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        self._conn.commit()
        return self._cursor.rowcount

    def buy_item(self, user_id: int, item_id: int, quantity: int, total_price: int) -> None:
        self.update_balance(user_id, -total_price)
        self._cursor.execute(
            '''INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)
               ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?''',
            (user_id, item_id, quantity, quantity)
        )
        self._conn.commit()

    def get_inventory(self, user_id: int):
        self._cursor.execute(
            '''SELECT items.item_id, items.name, items.description, inventory.quantity
               FROM inventory
               JOIN items ON inventory.item_id = items.item_id
               WHERE inventory.user_id = ?''',
            (user_id,)
        )
        return self._cursor.fetchall()
