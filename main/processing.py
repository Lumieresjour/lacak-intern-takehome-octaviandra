"""Membaca, membersihkan, dan mengubah posisi GPS menjadi trip."""

import csv
import json
import math
from datetime import datetime, timezone

from .config import (
    EARTH_RADIUS_KM,
    GAP_TIMEOUT_SECONDS,
    MOVING_THRESHOLD_KPH,
    POSITIONS_NDJSON,
    STOP_TIMEOUT_SECONDS,
    VEHICLES_CSV,
)
from .db import fmt_iso_utc

def parse_iso_to_utc(value):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return None

def haversine_km(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))

def round_exact(value, digits):
    return round(value + 0.0, digits)

def load_vehicles():
    vehicles = {}
    try:
        with open(VEHICLES_CSV, newline='', encoding='utf-8') as file:
            for row in csv.DictReader(file):
                device_id = row.get('device_id')
                if device_id:
                    vehicles[device_id] = {
                        'device_id': device_id,
                        'plate_number': row.get('plate_number') or '',
                        'vehicle_type': row.get('vehicle_type') or '',
                        'operator': row.get('operator') or '',
                    }
    except FileNotFoundError:
        print(f'vehicles.csv not found at {VEHICLES_CSV}')
    return vehicles

def load_and_clean_positions(vehicles):
    """Menerapkan aturan pembersihan 1-7 lalu mendeteksi trip per kendaraan."""
    positions_by_device = {device_id: [] for device_id in vehicles}
    seen_pairs = set()
    try:
        with open(POSITIONS_NDJSON, encoding='utf-8') as file:
            for line in file:
                try:
                    obj = json.loads(line.strip())
                except Exception:
                    continue
                device_id = obj.get('device_id')
                if device_id not in vehicles:
                    continue
                recorded_at = parse_iso_to_utc(obj.get('recorded_at'))
                if recorded_at is None:
                    continue
                instant_key = (device_id, fmt_iso_utc(recorded_at))
                if instant_key in seen_pairs:
                    continue
                seen_pairs.add(instant_key)
                latitude, longitude = obj.get('latitude'), obj.get('longitude')
                if latitude is None or longitude is None:
                    continue
                try:
                    latitude, longitude = float(latitude), float(longitude)
                    speed = float(obj.get('speed_kph', 0.0))
                except Exception:
                    continue
                if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
                    continue
                if latitude == 0.0 and longitude == 0.0 or speed < 0.0 or speed > 200.0:
                    continue
                positions_by_device[device_id].append({
                    'device_id': device_id,
                    'recorded_at': recorded_at,
                    'latitude': latitude,
                    'longitude': longitude,
                    'speed_kph': speed,
                    'raw': obj,
                })
    except FileNotFoundError:
        print(f'positions.ndjson not found at {POSITIONS_NDJSON}')

    for device_id, records in positions_by_device.items():
        records.sort(key=lambda record: record['recorded_at'])
        kept = []
        for record in records:
            if not kept:
                kept.append(record)
                continue
            previous = kept[-1]
            seconds = (record['recorded_at'] - previous['recorded_at']).total_seconds()
            distance = haversine_km(previous['latitude'], previous['longitude'], record['latitude'], record['longitude'])
            implied_speed = distance / (seconds / 3600.0) if seconds > 0 else float('inf')
            if implied_speed <= 200.0:
                kept.append(record)
        positions_by_device[device_id] = kept

    return {
        device_id: detect_trips_for_device(device_id, records)
        for device_id, records in positions_by_device.items()
    }

def detect_trips_for_device(device_id, records):
    trips, open_trip = [], []
    last_moving_index = None
    previous = None
    for record in records:
        if previous is not None and (record['recorded_at'] - previous['recorded_at']).total_seconds() > GAP_TIMEOUT_SECONDS:
            closed = close_trip(open_trip, last_moving_index, device_id)
            if closed:
                trips.append(closed)
            open_trip, last_moving_index = [], None
        if open_trip and last_moving_index is not None:
            elapsed = (record['recorded_at'] - open_trip[last_moving_index]['recorded_at']).total_seconds()
            if elapsed >= STOP_TIMEOUT_SECONDS:
                closed = close_trip(open_trip, last_moving_index, device_id)
                if closed:
                    trips.append(closed)
                open_trip, last_moving_index = [], None
        moving = record['speed_kph'] >= MOVING_THRESHOLD_KPH
        if not open_trip:
            if moving:
                open_trip, last_moving_index = [record], 0
        else:
            open_trip.append(record)
            if moving:
                last_moving_index = len(open_trip) - 1
        previous = record
    closed = close_trip(open_trip, last_moving_index, device_id)
    if closed:
        trips.append(closed)
    return trips

def close_trip(open_trip, last_moving_index, device_id):
    if last_moving_index is None:
        return None
    points = open_trip[:last_moving_index + 1]
    if len(points) < 2:
        return None
    start, end = points[0], points[-1]
    duration = int((end['recorded_at'] - start['recorded_at']).total_seconds())
    distance = sum(haversine_km(a['latitude'], a['longitude'], b['latitude'], b['longitude']) for a, b in zip(points, points[1:]))
    if duration < 60 or distance < 0.2:
        return None
    return {
        'device_id': device_id,
        'start_time': fmt_iso_utc(start['recorded_at']),
        'end_time': fmt_iso_utc(end['recorded_at']),
        'duration_seconds': duration,
        'distance_km': round_exact(distance, 3),
        'max_speed_kph': round_exact(max(point['speed_kph'] for point in points), 1),
        'avg_speed_kph': round_exact(distance / (duration / 3600.0), 2),
        'start_latitude': round_exact(start['latitude'], 6),
        'start_longitude': round_exact(start['longitude'], 6),
        'end_latitude': round_exact(end['latitude'], 6),
        'end_longitude': round_exact(end['longitude'], 6),
        'point_count': len(points),
    }

def compute_summary(trips_by_device, vehicles):
    per_vehicle = []
    total_trips = total_distance = total_duration = active_vehicles = 0
    for device_id, trips in trips_by_device.items():
        if trips:
            active_vehicles += 1
        distance = sum(trip['distance_km'] for trip in trips)
        total_trips += len(trips)
        total_distance += distance
        total_duration += sum(trip['duration_seconds'] for trip in trips)
        per_vehicle.append((device_id, vehicles.get(device_id, {}).get('plate_number', ''), distance, len(trips)))
    per_vehicle.sort(key=lambda item: item[2], reverse=True)
    return {
        'from': None,
        'to': None,
        'total_trips': total_trips,
        'total_distance_km': round_exact(total_distance, 2),
        'total_duration_seconds': total_duration,
        'active_vehicles': active_vehicles,
        'top_vehicles_by_distance': [
            {'device_id': device_id, 'plate_number': plate, 'total_distance_km': round_exact(distance, 3), 'trip_count': count}
            for device_id, plate, distance, count in per_vehicle[:5]
        ],
    }