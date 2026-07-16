import os
import sqlite3
from pathlib import Path

APP_NAME = "Retry Action App"

def get_app_dir():
    appdata = os.getenv('APPDATA') or os.path.expanduser('~')
    path = Path(appdata) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_db_path():
    return str(get_app_dir() / "failures.db")

INITIAL_ACTIONS = [
    "Pin Replaced",
    "Socket Aligned",
    "Type of Pin Changed",
    "Cleaning",
    "Otro"
]

def connect():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=True)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS failures (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      pin TEXT NOT NULL,
      action TEXT NOT NULL,
      technician TEXT,
      comments TEXT,
      status TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS actions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );
    """)
    conn.commit()
    for a in INITIAL_ACTIONS:
        try:
            cur.execute("INSERT OR IGNORE INTO actions (name) VALUES (?);", (a,))
        except Exception:
            pass
    conn.commit()
    conn.close()

def add_action(name):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO actions (name) VALUES (?);", (name,))
    conn.commit()
    cur.execute("SELECT name FROM actions ORDER BY name COLLATE NOCASE;")
    rows = [r["name"] for r in cur.fetchall()]
    conn.close()
    return rows

def get_actions():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM actions ORDER BY name COLLATE NOCASE;")
    rows = [r["name"] for r in cur.fetchall()]
    conn.close()
    return rows

def add_failure(pin, action, technician, comments, status):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO failures (pin, action, technician, comments, status)
      VALUES (?, ?, ?, ?, ?);
    """, (pin, action, technician, comments, status))
    conn.commit()
    conn.close()

def add_failure_with_time(pin, action, technician, comments, status, created_at_str):
    """
    Inserta un failure preservando created_at (string en formato 'YYYY-MM-DD HH:MM:SS').
    No inserta si ya existe un registro con mismo pin y misma created_at (evita duplicados).
    Devuelve True si insertó, False si omitido.
    """
    conn = connect()
    cur = conn.cursor()
    # check duplicate: same pin and same timestamp
    cur.execute("""
      SELECT 1 FROM failures
      WHERE pin = ? AND datetime(created_at) = datetime(?)
      LIMIT 1;
    """, (pin, created_at_str))
    exists = cur.fetchone()
    if exists:
        conn.close()
        return False
    # ensure action exists
    cur.execute("INSERT OR IGNORE INTO actions (name) VALUES (?);", (action,))
    cur.execute("""
      INSERT INTO failures (pin, action, technician, comments, status, created_at)
      VALUES (?, ?, ?, ?, ?, ?);
    """, (pin, action, technician, comments, status, created_at_str))
    conn.commit()
    conn.close()
    return True

def exists_failure(pin, created_at_str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
      SELECT 1 FROM failures
      WHERE pin = ? AND datetime(created_at) = datetime(?)
      LIMIT 1;
    """, (pin, created_at_str))
    r = cur.fetchone()
    conn.close()
    return bool(r)

def get_total_count():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM failures;")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def get_recent(limit=20):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
      SELECT id, pin, action, technician, comments, status, created_at
      FROM failures
      ORDER BY datetime(created_at) DESC
      LIMIT ?;
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_recent_after_time(limit=20, time_threshold="08:00:00", today_only=True):
    """
    Devuelve registros con hora >= time_threshold.
    Si today_only=True devuelve solo registros de la fecha local de hoy.
    """
    conn = connect()
    cur = conn.cursor()
    if today_only:
        cur.execute("""
          SELECT id, pin, action, technician, comments, status, created_at
          FROM failures
          WHERE date(created_at, 'localtime') = date('now','localtime')
            AND time(created_at, 'localtime') >= ?
          ORDER BY datetime(created_at) DESC
          LIMIT ?;
        """, (time_threshold, limit))
    else:
        cur.execute("""
          SELECT id, pin, action, technician, comments, status, created_at
          FROM failures
          WHERE time(created_at, 'localtime') >= ?
          ORDER BY datetime(created_at) DESC
          LIMIT ?;
        """, (time_threshold, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_by_date(date_str):
    """
    date_str: 'YYYY-MM-DD' (date in localtime)
    Devuelve todos los registros de esa fecha (en hora local), ordenados por hora descendente.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
      SELECT id, pin, action, technician, comments, status, created_at
      FROM failures
      WHERE date(created_at, 'localtime') = ?
      ORDER BY datetime(created_at) DESC;
    """, (date_str,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Initialize DB at import
init_db()
