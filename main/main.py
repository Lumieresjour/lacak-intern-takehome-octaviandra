"""Titik masuk aplikasi: memuat data dan menjalankan HTTP server."""

import sys
import threading
from http.server import ThreadingHTTPServer

from .config import DATABASE_PATH, PORT
from .db import init_database, persist_trips
from .api import make_handler
from .processing import compute_summary, load_and_clean_positions, load_vehicles

vehicles = {}
_summary = None
_data_lock = threading.Lock()

def load_all_data():
    global vehicles, _summary
    with _data_lock:
        loaded_vehicles = load_vehicles()
        vehicles.clear()
        vehicles.update(loaded_vehicles)
        trips_by_device = load_and_clean_positions(vehicles)
        with init_database() as connection:
            persist_trips(connection, trips_by_device)
        _summary = compute_summary(trips_by_device, vehicles)
        print('Data loaded: vehicles=%d; SQLite database=%s' % (len(vehicles), DATABASE_PATH))

def get_summary():
    return dict(_summary) if _summary is not None else compute_summary({}, vehicles)

def main():
    port = PORT
    if '--port' in sys.argv:
        try:
            port = int(sys.argv[sys.argv.index('--port') + 1])
        except Exception:
            pass
    loader = threading.Thread(target=load_all_data, daemon=True)
    loader.start()
    handler = make_handler(vehicles, get_summary, _data_lock)
    httpd = ThreadingHTTPServer(('', port), handler)
    print(f'Serving on port {port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        httpd.shutdown()

if __name__ == '__main__':
    main()