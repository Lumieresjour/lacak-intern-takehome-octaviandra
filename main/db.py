"""Menyediakan penyimpanan SQLite untuk hasil trip yang sudah dihitung."""

import sqlite3
from datetime import timezone

from .config import DATABASE_PATH, TRIP_COLUMNS

def init_database():
    """Membuat tabel dan indeks hasil perhitungan bila belum tersedia."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hasil_kalkulasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            distance_km REAL NOT NULL,
            max_speed_kph REAL NOT NULL,
            avg_speed_kph REAL NOT NULL,
            start_latitude REAL NOT NULL,
            start_longitude REAL NOT NULL,
            end_latitude REAL NOT NULL,
            end_longitude REAL NOT NULL,
            point_count INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hasil_device_start
        ON hasil_kalkulasi(device_id, start_time)
    """)
    conn.commit()
    return conn

def persist_trips(conn, all_trips):
    """Mengganti isi tabel dengan hasil import terbaru."""
    rows = [
        tuple(trip[column] for column in TRIP_COLUMNS)
        for trips in all_trips.values()
        for trip in trips
    ]
    conn.execute("DELETE FROM hasil_kalkulasi")
    conn.executemany("""
        INSERT INTO hasil_kalkulasi (
            device_id, start_time, end_time, duration_seconds,
            distance_km, max_speed_kph, avg_speed_kph,
            start_latitude, start_longitude, end_latitude,
            end_longitude, point_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()

def fetch_trips(device_id, from_dt=None, to_dt=None):
    """Mengambil trip kendaraan dengan filter waktu opsional."""
    clauses = ["device_id = ?"]
    params = [device_id]
    if from_dt is not None:
        clauses.append("start_time >= ?")
        params.append(fmt_iso_utc(from_dt))
    if to_dt is not None:
        clauses.append("start_time < ?")
        params.append(fmt_iso_utc(to_dt))
    query = """
        SELECT device_id, start_time, end_time, duration_seconds,
               distance_km, max_speed_kph, avg_speed_kph,
               start_latitude, start_longitude, end_latitude,
               end_longitude, point_count
        FROM hasil_kalkulasi
        WHERE %s
        ORDER BY start_time ASC
    """ % " AND ".join(clauses)
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(zip(TRIP_COLUMNS, row)) for row in rows]

def fmt_iso_utc(dt):
    """Memformat datetime aware menjadi format UTC API."""
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')