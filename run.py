#!/usr/bin/env python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import csv
import sys
import threading
from datetime import datetime, timezone, timedelta
import math
import os

MOVING_THRESHOLD_KPH = 3.0
STOP_TIMEOUT_SECONDS = 300
GAP_TIMEOUT_SECONDS = 1800
EARTH_RADIUS_KM = 6371.0088
PORT = 8080
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
VEHICLES_CSV = os.path.join(DATA_DIR, 'vehicles.csv')
POSITIONS_NDJSON = os.path.join(DATA_DIR, 'positions.ndjson')

vehicles = {}
positions_by_device = {}
trips_by_device = {}
_summary = None
_data_loaded = False
_data_lock = threading.Lock()

def parse_iso_to_utc(s):
    if s is None:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return None

def fmt_iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def haversine_km(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2
    d = 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
    return d

def round_exact(val, digits):
    return round(val + 0.0, digits)

def load_vehicles():
    global vehicles
    vehicles = {}
    try:
        with open(VEHICLES_CSV, newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                did = row.get('device_id')
                if not did:
                    continue
                vehicles[did] = {
                    'device_id': did,
                    'plate_number': row.get('plate_number') or '',
                    'vehicle_type': row.get('vehicle_type') or '',
                    'operator': row.get('operator') or ''
                }
    except FileNotFoundError:
        print(f"vehicles.csv not found at {VEHICLES_CSV}")

def load_and_clean_positions():
    """Read NDJSON sequentially and apply rules 1..6 in order per record (file order).
    Then group per device, sort by time and apply rule 7 (teleport), then detect trips.
    """
    global positions_by_device, trips_by_device
    positions_by_device = {did: [] for did in vehicles.keys()}
    seen_pairs = set()
    try:
        with open(POSITIONS_NDJSON, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                device_id = obj.get('device_id')
                if device_id not in vehicles:
                    continue
                recorded_at_raw = obj.get('recorded_at')
                dt = parse_iso_to_utc(recorded_at_raw)
                if dt is None:
                    continue
                instant_key = (device_id, fmt_iso_utc(dt))
                if instant_key in seen_pairs:
                    continue
                seen_pairs.add(instant_key)
                lat = obj.get('latitude')
                lon = obj.get('longitude')
                if lat is None or lon is None:
                    continue
                try:
                    latf = float(lat)
                    lonf = float(lon)
                except Exception:
                    continue
                if not (-90.0 <= latf <= 90.0) or not (-180.0 <= lonf <= 180.0):
                    continue
                if latf == 0.0 and lonf == 0.0:
                    continue
                try:
                    speed = float(obj.get('speed_kph', 0.0))
                except Exception:
                    continue
                if speed < 0.0 or speed > 200.0:
                    continue
                rec = {
                    'device_id': device_id,
                    'recorded_at': dt,
                    'latitude': latf,
                    'longitude': lonf,
                    'speed_kph': speed,
                    'raw': obj
                }
                positions_by_device[device_id].append(rec)
    except FileNotFoundError:
        print(f"positions.ndjson not found at {POSITIONS_NDJSON}")

    for did, recs in positions_by_device.items():
        if not recs:
            positions_by_device[did] = []
            continue
        recs.sort(key=lambda r: r['recorded_at'])
        kept = []
        last_kept = None
        for r in recs:
            if last_kept is None:
                kept.append(r)
                last_kept = r
                continue
            dt_seconds = (r['recorded_at'] - last_kept['recorded_at']).total_seconds()
            if dt_seconds <= 0:
                drop = False
                if dt_seconds == 0:
                    drop = True if haversine_km(last_kept['latitude'], last_kept['longitude'], r['latitude'], r['longitude']) > 0 else False
                else:
                    hours = dt_seconds / 3600.0
                    if hours <= 0:
                        drop = True
                    else:
                        dist = haversine_km(last_kept['latitude'], last_kept['longitude'], r['latitude'], r['longitude'])
                        implied = dist / hours
                        drop = implied > 200.0
                if drop:
                    continue
                else:
                    kept.append(r)
                    last_kept = r
                    continue
            hours = dt_seconds / 3600.0
            dist = haversine_km(last_kept['latitude'], last_kept['longitude'], r['latitude'], r['longitude'])
            implied = dist / hours if hours > 0 else float('inf')
            if implied > 200.0:
                continue
            else:
                kept.append(r)
                last_kept = r
        positions_by_device[did] = kept

    trips_by_device = {}
    for did, recs in positions_by_device.items():
        trips = detect_trips_for_device(did, recs)
        trips_by_device[did] = trips
    return trips_by_device

def detect_trips_for_device(device_id, recs):
    trips = []
    if not recs:
        return trips
    open_trip = []
    last_moving_index = None
    prev_rec = None
    for r in recs:
        if prev_rec is not None:
            gap = (r['recorded_at'] - prev_rec['recorded_at']).total_seconds()
            if gap > GAP_TIMEOUT_SECONDS:
                if open_trip:
                    closed = close_trip(open_trip, last_moving_index, device_id)
                    if closed is not None:
                        trips.append(closed)
                open_trip = []
                last_moving_index = None
        if open_trip and last_moving_index is not None:
            time_since_last_moving = (r['recorded_at'] - open_trip[last_moving_index]['recorded_at']).total_seconds()
            if time_since_last_moving >= STOP_TIMEOUT_SECONDS:
                closed = close_trip(open_trip, last_moving_index, device_id)
                if closed is not None:
                    trips.append(closed)
                open_trip = []
                last_moving_index = None
        is_moving = r['speed_kph'] >= MOVING_THRESHOLD_KPH
        if not open_trip:
            if is_moving:
                open_trip = [r]
                last_moving_index = 0
            else:
                pass
        else:
            open_trip.append(r)
            if is_moving:
                last_moving_index = len(open_trip) - 1
        prev_rec = r
    if open_trip:
        closed = close_trip(open_trip, last_moving_index, device_id)
        if closed is not None:
            trips.append(closed)
    return trips

def close_trip(open_trip, last_moving_index, device_id):
    if last_moving_index is None:
        return None
    pts = open_trip[:last_moving_index + 1]
    if len(pts) < 2:
        return None
    start = pts[0]
    end = pts[-1]
    duration_seconds = int((end['recorded_at'] - start['recorded_at']).total_seconds())
    dist = 0.0
    for i in range(len(pts) - 1):
        a = pts[i]
        b = pts[i + 1]
        dist += haversine_km(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
    if duration_seconds < 60:
        return None
    if dist < 0.2:
        return None
    max_speed = max(p['speed_kph'] for p in pts)
    avg_speed = dist / (duration_seconds / 3600.0) if duration_seconds > 0 else 0.0
    trip = {
        'device_id': device_id,
        'start_time': fmt_iso_utc(start['recorded_at']),
        'end_time': fmt_iso_utc(end['recorded_at']),
        'duration_seconds': duration_seconds,
        'distance_km': round_exact(dist, 3),
        'max_speed_kph': round_exact(max_speed, 1),
        'avg_speed_kph': round_exact(avg_speed, 2),
        'start_latitude': round_exact(start['latitude'], 6),
        'start_longitude': round_exact(start['longitude'], 6),
        'end_latitude': round_exact(end['latitude'], 6),
        'end_longitude': round_exact(end['longitude'], 6),
        'point_count': len(pts)
    }
    return trip

def compute_summary(trips_by_device):
    total_trips = 0
    total_distance = 0.0
    total_duration = 0
    active_vehicles = 0
    per_vehicle = []
    for did, trips in trips_by_device.items():
        if trips:
            active_vehicles += 1
        vt = sum(t['distance_km'] for t in trips)
        vc = len(trips)
        total_trips += vc
        total_distance += vt
        total_duration += sum(t['duration_seconds'] for t in trips)
        per_vehicle.append((did, vehicles.get(did, {}).get('plate_number', ''), vt, vc))
    per_vehicle.sort(key=lambda x: x[2], reverse=True)
    top = []
    for did, plate, vt, vc in per_vehicle[:5]:
        top.append({'device_id': did, 'plate_number': plate, 'total_distance_km': round_exact(vt, 3), 'trip_count': vc})
    summary = {
        'from': None,
        'to': None,
        'total_trips': total_trips,
        'total_distance_km': round_exact(total_distance, 2),
        'total_duration_seconds': total_duration,
        'active_vehicles': active_vehicles,
        'top_vehicles_by_distance': top
    }
    return summary

def load_all_data():
    global _data_loaded, trips_by_device, _summary
    with _data_lock:
        load_vehicles()
        trips_by_device = load_and_clean_positions()
        _summary = compute_summary(trips_by_device)
        _data_loaded = True
        print('Data loaded: vehicles=%d devices with trips computed.' % (len(vehicles),))

class Handler(BaseHTTPRequestHandler):
    server_version = 'takehome/0.1'

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        try:
            if path == '/health':
                self._send_json(200, {'status': 'ok'})
                return
            elif path == '/vehicles':
                vs = []
                for did, meta in vehicles.items():
                    trips = trips_by_device.get(did, [])
                    total_distance = sum(t['distance_km'] for t in trips)
                    vs.append({
                        'device_id': did,
                        'plate_number': meta.get('plate_number', ''),
                        'vehicle_type': meta.get('vehicle_type', ''),
                        'operator': meta.get('operator', ''),
                        'trip_count': len(trips),
                        'total_distance_km': round_exact(total_distance, 3)
                    })
                self._send_json(200, {'vehicles': vs})
                return
            elif path.startswith('/vehicles/') and path.endswith('/trips'):
                parts = path.split('/')
                if len(parts) >= 3:
                    device_id = parts[2]
                else:
                    self._send_json(404, {'error': 'not found'})
                    return
                if device_id not in vehicles:
                    self._send_json(404, {'error': 'device not found'})
                    return
                from_s = qs.get('from', [None])[0]
                to_s = qs.get('to', [None])[0]
                from_dt = None
                to_dt = None
                if from_s is not None:
                    from_dt = parse_iso_to_utc(from_s)
                    if from_dt is None:
                        self._send_json(400, {'error': 'from not valid ISO-8601'})
                        return
                if to_s is not None:
                    to_dt = parse_iso_to_utc(to_s)
                    if to_dt is None:
                        self._send_json(400, {'error': 'to not valid ISO-8601'})
                        return
                if from_dt is not None and to_dt is not None and from_dt > to_dt:
                    self._send_json(400, {'error': 'from > to'})
                    return
                trips = trips_by_device.get(device_id, [])
                filtered = []
                for t in trips:
                    st = parse_iso_to_utc(t['start_time'])
                    if from_dt is not None and st < from_dt:
                        continue
                    if to_dt is not None and st >= to_dt:
                        continue
                    filtered.append(t)
                self._send_json(200, {'device_id': device_id, 'trip_count': len(filtered), 'trips': filtered})
                return
            elif path == '/summary':
                s = dict(_summary) if _summary is not None else compute_summary(trips_by_device)
                self._send_json(200, s)
                return
            else:
                self._send_json(404, {'error': 'not found'})
                return
        except Exception as e:
            self._send_json(500, {'error': 'server error', 'detail': str(e)})

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format%args))

def main():
    global PORT
    if '--port' in sys.argv:
        try:
            idx = sys.argv.index('--port')
            PORT = int(sys.argv[idx+1])
        except Exception:
            pass
    loader = threading.Thread(target=load_all_data, daemon=True)
    loader.start()
    addr = ('', PORT)
    httpd = ThreadingHTTPServer(addr, Handler)
    print(f"Serving on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        httpd.shutdown()

if __name__ == '__main__':
    main()