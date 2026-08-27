"""Konfigurasi yang dipakai oleh seluruh layanan."""

import os

MOVING_THRESHOLD_KPH = 3.0
STOP_TIMEOUT_SECONDS = 300
GAP_TIMEOUT_SECONDS = 1800
EARTH_RADIUS_KM = 6371.0088
PORT = 8080
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
VEHICLES_CSV = os.path.join(DATA_DIR, 'vehicles.csv')
POSITIONS_NDJSON = os.path.join(DATA_DIR, 'positions.ndjson')
DATABASE_PATH = os.path.join(BASE_DIR, 'hasil_bonus.db')

TRIP_COLUMNS = (
    'device_id', 'start_time', 'end_time', 'duration_seconds',
    'distance_km', 'max_speed_kph', 'avg_speed_kph',
    'start_latitude', 'start_longitude', 'end_latitude',
    'end_longitude', 'point_count'
)