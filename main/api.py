"""Menyediakan endpoint HTTP dan membentuk respons JSON layanan."""

import json
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from .db import fetch_trips
from .processing import parse_iso_to_utc, round_exact

def make_handler(vehicles, get_summary, data_lock):
    """Membuat handler yang memakai state aplikasi yang diberikan."""
    class Handler(BaseHTTPRequestHandler):
        server_version = 'takehome/0.1'
        def _send_json(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            try:
                if path == '/health':
                    self._send_json(200, {'status': 'ok'})
                    return
                with data_lock:
                    pass
                if path == '/vehicles':
                    result = []
                    for device_id, metadata in vehicles.items():
                        trips = fetch_trips(device_id)
                        result.append({
                            'device_id': device_id,
                            'plate_number': metadata.get('plate_number', ''),
                            'vehicle_type': metadata.get('vehicle_type', ''),
                            'operator': metadata.get('operator', ''),
                            'trip_count': len(trips),
                            'total_distance_km': round_exact(sum(trip['distance_km'] for trip in trips), 3),
                        })
                    self._send_json(200, {'vehicles': result})
                    return
                if path.startswith('/vehicles/') and path.endswith('/trips'):
                    parts = path.split('/')
                    device_id = parts[2] if len(parts) >= 3 else ''
                    if device_id not in vehicles:
                        self._send_json(404, {'error': 'device not found'})
                        return
                    from_dt = self._parse_query_time(query, 'from')
                    if from_dt == 'invalid':
                        return
                    to_dt = self._parse_query_time(query, 'to')
                    if to_dt == 'invalid':
                        return
                    if from_dt is not None and to_dt is not None and from_dt > to_dt:
                        self._send_json(400, {'error': 'from > to'})
                        return
                    trips = fetch_trips(device_id, from_dt, to_dt)
                    self._send_json(200, {'device_id': device_id, 'trip_count': len(trips), 'trips': trips})
                    return
                if path == '/summary':
                    self._send_json(200, get_summary())
                    return
                self._send_json(404, {'error': 'not found'})
            except Exception as error:
                self.log_message('Error handling request: %s', repr(error))
                self._send_json(500, {'error': 'server error'})
        def _parse_query_time(self, query, name):
            value = query.get(name, [None])[0]
            if value is None:
                return None
            parsed = parse_iso_to_utc(value)
            if parsed is None:
                self._send_json(400, {'error': f'{name} not valid ISO-8601'})
                return 'invalid'
            return parsed
        def log_message(self, format_string, *args):
            sys.stderr.write('%s - - [%s] %s\n' % (
                self.client_address[0], self.log_date_time_string(), format_string % args
            ))

    return Handler