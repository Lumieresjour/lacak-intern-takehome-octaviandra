#!/usr/bin/env python3
"""
Pemeriksa kontrak API untuk take-home Lacak.

  python3 verify/verify.py http://localhost:8080

Python 3.9+, tanpa dependensi eksternal.

Skrip ini memeriksa BENTUK dan KONSISTENSI INTERNAL API Anda. Skrip ini TIDAK
tahu jawaban yang benar dan TIDAK menilai kebenaran perhitungan Anda.
Lulus semua cek di sini adalah syarat minimum, bukan jaminan nilai bagus.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TIMEOUT = 15
FLEET_SIZE = 8
KNOWN_DEVICE = "864636051234501"
UNKNOWN_DEVICE = "000000000000000"

passed, failed, warned = [], [], []


def ok(msg):
    passed.append(msg); print(f"  \033[32mPASS\033[0m  {msg}")


def bad(msg, detail=""):
    failed.append(msg); print(f"  \033[31mFAIL\033[0m  {msg}")
    if detail:
        print(f"        \033[90m{detail}\033[0m")


def warn(msg, detail=""):
    warned.append(msg); print(f"  \033[33mWARN\033[0m  {msg}")
    if detail:
        print(f"        \033[90m{detail}\033[0m")


def get(base, path, params=None):
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)


def get_json(base, path, params=None):
    status, body = get(base, path, params)
    if status is None:
        return None, None, body
    try:
        return status, json.loads(body), None
    except json.JSONDecodeError:
        return status, None, f"respons bukan JSON: {body[:200]}"


def parse_iso(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


TRIP_FIELDS = {
    "device_id": str,
    "start_time": str,
    "end_time": str,
    "duration_seconds": (int,),
    "distance_km": (int, float),
    "max_speed_kph": (int, float),
    "avg_speed_kph": (int, float),
    "start_latitude": (int, float),
    "start_longitude": (int, float),
    "end_latitude": (int, float),
    "end_longitude": (int, float),
    "point_count": (int,),
}


def check_health(base):
    print("\n\033[1m[1/6] GET /health\033[0m")
    st, data, err = get_json(base, "/health")
    if st is None:
        bad("layanan bisa dihubungi", data or err); return False
    if st != 200:
        bad("/health mengembalikan 200", f"dapat {st}"); return False
    ok("/health mengembalikan 200")
    if isinstance(data, dict) and data.get("status") == "ok":
        ok('body memuat {"status": "ok"}')
    else:
        bad('body memuat {"status": "ok"}', f"dapat {json.dumps(data)[:150]}")
    return True


def check_vehicles(base):
    print("\n\033[1m[2/6] GET /vehicles\033[0m")
    st, data, err = get_json(base, "/vehicles")
    if st != 200 or not isinstance(data, dict):
        bad("/vehicles mengembalikan 200 + objek JSON", err or f"status {st}"); return []
    ok("/vehicles mengembalikan 200")
    vs = data.get("vehicles")
    if not isinstance(vs, list):
        bad('body punya array "vehicles"', f"dapat {type(vs).__name__}"); return []
    ok('body punya array "vehicles"')
    if len(vs) == FLEET_SIZE:
        ok(f"{FLEET_SIZE} kendaraan dikembalikan")
    else:
        bad(f"{FLEET_SIZE} kendaraan dikembalikan",
            f"dapat {len(vs)} — kendaraan tanpa trip tetap harus muncul")
    req = ["device_id", "plate_number", "vehicle_type", "operator", "trip_count", "total_distance_km"]
    missing = {f for v in vs if isinstance(v, dict) for f in req if f not in v}
    if missing:
        bad("setiap kendaraan punya field wajib", f"hilang: {sorted(missing)}")
    else:
        ok("setiap kendaraan punya field wajib")
    return vs


def check_trips(base):
    print("\n\033[1m[3/6] GET /vehicles/{device_id}/trips\033[0m")
    st, data, err = get_json(base, f"/vehicles/{KNOWN_DEVICE}/trips")
    if st != 200 or not isinstance(data, dict):
        bad("perangkat yang dikenal mengembalikan 200", err or f"status {st}"); return []
    ok("perangkat yang dikenal mengembalikan 200")

    trips = data.get("trips")
    if not isinstance(trips, list):
        bad('body punya array "trips"', f"dapat {type(trips).__name__}"); return []
    ok(f'body punya array "trips" ({len(trips)} trip)')

    if data.get("trip_count") == len(trips):
        ok("trip_count cocok dengan panjang array")
    else:
        bad("trip_count cocok dengan panjang array",
            f"trip_count={data.get('trip_count')}, len(trips)={len(trips)}")

    if not trips:
        warn("tidak ada trip untuk diperiksa", "perangkat ini seharusnya punya beberapa trip")
        return []

    bad_type = []
    for t in trips:
        for f, ty in TRIP_FIELDS.items():
            if f not in t:
                bad_type.append(f"{f}: hilang")
            elif isinstance(ty, tuple):
                if isinstance(t[f], bool) or not isinstance(t[f], ty):
                    bad_type.append(f"{f}: bukan angka")
            elif not isinstance(t[f], ty):
                bad_type.append(f"{f}: bukan {ty.__name__}")
    if bad_type:
        bad("setiap trip punya field wajib dengan tipe benar", ", ".join(sorted(set(bad_type))[:8]))
    else:
        ok("setiap trip punya field wajib dengan tipe benar")

    starts = [parse_iso(t.get("start_time")) for t in trips]
    if any(s is None for s in starts):
        bad("start_time bisa di-parse sebagai ISO-8601")
    else:
        ok("start_time bisa di-parse sebagai ISO-8601")
        if all(starts[i] <= starts[i + 1] for i in range(len(starts) - 1)):
            ok("trip terurut naik berdasarkan start_time")
        else:
            bad("trip terurut naik berdasarkan start_time")

    print("\n\033[1m       konsistensi internal tiap trip\033[0m")
    errs = {"dur": 0, "avg": 0, "min": 0}
    for t in trips:
        s, e = parse_iso(t.get("start_time")), parse_iso(t.get("end_time"))
        if s and e:
            expect = int((e - s).total_seconds())
            if abs(expect - t.get("duration_seconds", -1)) > 1:
                errs["dur"] += 1
        d, dur, avg = t.get("distance_km"), t.get("duration_seconds"), t.get("avg_speed_kph")
        if isinstance(d, (int, float)) and isinstance(dur, (int, float)) and dur > 0 \
                and isinstance(avg, (int, float)):
            want = d / (dur / 3600.0)
            if want > 0 and abs(want - avg) / want > 0.01:
                errs["avg"] += 1
        if (t.get("point_count", 0) < 2 or (dur or 0) < 60 or (d or 0) < 0.2):
            errs["min"] += 1

    if errs["dur"]:
        bad("duration_seconds == end_time − start_time", f"{errs['dur']} trip meleset")
    else:
        ok("duration_seconds == end_time − start_time")
    if errs["avg"]:
        bad("avg_speed_kph == distance_km / (duration_seconds/3600)",
            f"{errs['avg']} trip meleset >1% — ini kecepatan berbasis jarak, "
            "bukan rata-rata kolom speed_kph")
    else:
        ok("avg_speed_kph == distance_km / (duration_seconds/3600)")
    if errs["min"]:
        bad("tidak ada trip di bawah ambang minimum",
            f"{errs['min']} trip melanggar point_count>=2 / durasi>=60s / jarak>=0.2km")
    else:
        ok("tidak ada trip di bawah ambang minimum")
    return trips


def check_filters(base, trips):
    print("\n\033[1m[4/6] filter from / to\033[0m")
    if len(trips) < 2:
        warn("filter dilewati", "butuh minimal 2 trip untuk diuji"); return

    starts = sorted(parse_iso(t["start_time"]) for t in trips)
    pivot = starts[len(starts) // 2]
    ps = pivot.strftime("%Y-%m-%dT%H:%M:%SZ")

    st, data, err = get_json(base, f"/vehicles/{KNOWN_DEVICE}/trips", {"from": ps})
    if st == 200 and isinstance(data, dict) and isinstance(data.get("trips"), list):
        got = {t["start_time"] for t in data["trips"]}
        want = {t["start_time"] for t in trips if parse_iso(t["start_time"]) >= pivot}
        if got == want:
            ok("from inklusif — trip tepat di batas ikut terhitung")
        else:
            bad("from inklusif — trip tepat di batas ikut terhitung",
                f"dapat {len(got)} trip, harusnya {len(want)}")
    else:
        bad("from menghasilkan 200", err or f"status {st}")

    st, data, err = get_json(base, f"/vehicles/{KNOWN_DEVICE}/trips", {"to": ps})
    if st == 200 and isinstance(data, dict) and isinstance(data.get("trips"), list):
        got = {t["start_time"] for t in data["trips"]}
        want = {t["start_time"] for t in trips if parse_iso(t["start_time"]) < pivot}
        if got == want:
            ok("to eksklusif — trip tepat di batas TIDAK ikut terhitung")
        else:
            bad("to eksklusif — trip tepat di batas TIDAK ikut terhitung",
                f"dapat {len(got)} trip, harusnya {len(want)}")
    else:
        bad("to menghasilkan 200", err or f"status {st}")

    st, _, _ = get_json(base, f"/vehicles/{KNOWN_DEVICE}/trips",
                        {"from": "2030-01-01T00:00:00Z", "to": "2030-01-02T00:00:00Z"})
    if st == 200:
        ok("rentang tanpa hasil tetap mengembalikan 200")
    else:
        bad("rentang tanpa hasil tetap mengembalikan 200", f"dapat {st}")


def check_errors(base):
    print("\n\033[1m[5/6] penanganan error\033[0m")
    cases = [
        (f"/vehicles/{UNKNOWN_DEVICE}/trips", None, 404, "perangkat tak dikenal -> 404"),
        (f"/vehicles/{KNOWN_DEVICE}/trips", {"from": "kemarin"}, 400, "tanggal tak valid -> 400"),
        (f"/vehicles/{KNOWN_DEVICE}/trips", {"from": "2026-08-10T00:00:00Z",
                                             "to": "2026-08-03T00:00:00Z"}, 400,
         "rentang terbalik (from > to) -> 400"),
    ]
    for path, params, want, label in cases:
        st, _ = get(base, path, params)
        if st == want:
            ok(label)
        else:
            bad(label, f"dapat {st}")


def check_summary(base, vehicles):
    print("\n\033[1m[6/6] GET /summary\033[0m")
    st, data, err = get_json(base, "/summary")
    if st != 200 or not isinstance(data, dict):
        bad("/summary mengembalikan 200 + objek JSON", err or f"status {st}"); return
    ok("/summary mengembalikan 200")

    req = ["from", "to", "total_trips", "total_distance_km",
           "total_duration_seconds", "active_vehicles", "top_vehicles_by_distance"]
    miss = [f for f in req if f not in data]
    if miss:
        bad("summary punya semua field wajib", f"hilang: {miss}")
    else:
        ok("summary punya semua field wajib")

    top = data.get("top_vehicles_by_distance")
    if isinstance(top, list):
        if len(top) <= 5:
            ok("top_vehicles_by_distance maksimal 5 entri")
        else:
            bad("top_vehicles_by_distance maksimal 5 entri", f"dapat {len(top)}")
        ds = [v.get("total_distance_km", 0) for v in top if isinstance(v, dict)]
        if all(ds[i] >= ds[i + 1] for i in range(len(ds) - 1)):
            ok("top_vehicles_by_distance terurut menurun")
        else:
            bad("top_vehicles_by_distance terurut menurun")
    else:
        bad('top_vehicles_by_distance adalah array')

    if vehicles:
        vt = sum(v.get("trip_count", 0) for v in vehicles if isinstance(v, dict))
        vd = sum(v.get("total_distance_km", 0) for v in vehicles if isinstance(v, dict))
        if data.get("total_trips") == vt:
            ok("total_trips cocok dengan jumlah dari /vehicles")
        else:
            bad("total_trips cocok dengan jumlah dari /vehicles",
                f"summary={data.get('total_trips')}, /vehicles={vt}")
        sd = data.get("total_distance_km", 0)
        if vd > 0 and abs(sd - vd) / vd <= 0.01:
            ok("total_distance_km cocok dengan jumlah dari /vehicles")
        else:
            bad("total_distance_km cocok dengan jumlah dari /vehicles",
                f"summary={sd}, /vehicles={round(vd, 3)}")


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    print(f"\n\033[1mPemeriksa kontrak API take-home Lacak\033[0m")
    print(f"Target: {base}")

    if not check_health(base):
        print("\n\033[31mLayanan tidak bisa dihubungi. Pastikan sudah berjalan, "
              "lalu jalankan ulang skrip ini.\033[0m\n")
        sys.exit(2)

    vehicles = check_vehicles(base)
    trips = check_trips(base)
    check_filters(base, trips)
    check_errors(base)
    check_summary(base, vehicles)

    total = len(passed) + len(failed)
    print("\n" + "─" * 62)
    print(f"  \033[32m{len(passed)} lulus\033[0m   "
          f"\033[31m{len(failed)} gagal\033[0m   "
          f"\033[33m{len(warned)} peringatan\033[0m   (dari {total} cek)")
    print("─" * 62)
    if failed:
        print("\nYang gagal:")
        for f in failed:
            print(f"  · {f}")
        print("\n\033[31mKontrak API belum terpenuhi.\033[0m\n")
        sys.exit(1)
    print("\n\033[32mKontrak API terpenuhi.\033[0m")
    print("\033[90mIngat: ini hanya memeriksa bentuk API, bukan kebenaran angka Anda.")
    print("Cocokkan hasil Anda dengan examples/expected-output.json.\033[0m\n")


if __name__ == "__main__":
    main()
