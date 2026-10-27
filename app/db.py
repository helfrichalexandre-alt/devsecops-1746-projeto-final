"""Acesso a dados do Clube Aurora (SQLite)."""

import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_db():
    """Retorna a conexão da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Recria o banco a partir do schema e cria os usuários de exemplo."""
    db = get_db()
    db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    seed_password = current_app.config["SEED_PASSWORD"]
    users = [
        ("armando@clubeaurora.com", "admin", "Armando Lacerda"),
        ("carla@clubeaurora.com", "staff", "Carla Nogueira"),
        ("leo@clubeaurora.com", "staff", "Leonardo Lacerda"),
    ]
    for email, role, name in users:
        create_user(email, seed_password, name, role)
    bookings = [
        (1, 2, 'viagem', 'Maldivas - voo fretado', '2026-12-20T09:00:00', 185000.00),
        (1, 3, 'arte', 'Leilão privado - Genebra', '2027-01-15T19:00:00', 950000.00),
        (2, 3, 'evento', 'Jantar exclusivo - Fasano', '2026-11-08T20:30:00', 42000.00),
        (3, 2, 'viagem', 'Patagônia - lodge privativo', '2027-02-03T07:00:00', 120000.00),
        (4, 3, 'evento', 'Camarote - GP de Interlagos', '2026-11-09T12:00:00', 68000.00),
        (5, 2, 'arte', 'Visita privada - galeria em NY', '2027-03-10T15:00:00', 15000.00),
    ]
    for cid, uid, srv, dest, dt, val in bookings:
        create_booking(cid, uid, srv, dest, dt, val)
    db.commit()


def row_to_dict(row):
    return dict(row) if row is not None else None


# ---------------------------------------------------------------- usuários

def create_user(email, password, full_name, role="staff"):
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
        (email, generate_password_hash(password), role, full_name),
    )
    db.commit()
    return cur.lastrowid


def get_user_by_email(email):
    return get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def list_users():
    rows = get_db().execute("SELECT id, email, role, full_name FROM users ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


def set_user_role(user_id, role):
    db = get_db()
    cur = db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    db.commit()
    return cur.rowcount


# ---------------------------------------------------------------- clientes

def list_clients():
    rows = get_db().execute("SELECT * FROM clients ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


def get_client(client_id):
    return row_to_dict(get_db().execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone())


def search_clients(name):
    rows = get_db().execute(
        "SELECT * FROM clients WHERE full_name LIKE ? ORDER BY id",
        (f"%{name}%",),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


# ---------------------------------------------------------------- reservas

def list_bookings(client_id):
    rows = get_db().execute(
        "SELECT * FROM bookings WHERE client_id = ? ORDER BY starts_at", (client_id,)
    ).fetchall()
    return [row_to_dict(r) for r in rows]


def create_booking(client_id, created_by, service, destination, starts_at, amount):
    db = get_db()
    cur = db.execute(
        "INSERT INTO bookings (client_id, created_by, service, destination, starts_at, amount) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (client_id, created_by, service, destination, starts_at, amount),
    )
    db.commit()
    return cur.lastrowid


# ---------------------------------------------------------------- auditoria

def log_action(user_id, action):
    db = get_db()
    db.execute("INSERT INTO audit_log (user_id, action) VALUES (?, ?)", (user_id, action))
    db.commit()
