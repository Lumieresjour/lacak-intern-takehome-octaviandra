# Spesifikasi Teknis

Dokumen ini adalah **sumber kebenaran**. Kalau README dan SPEC berbeda, ikuti SPEC.

Semua nama field, nama endpoint, dan angka ambang di bawah bersifat **wajib** —
API Anda harus memakai persis nama-nama ini supaya bisa diperiksa otomatis.

---

## 1. Data masukan

### 1.1 `data/positions.ndjson`

NDJSON — satu objek JSON per baris, 9.076 baris. Urutan baris **acak**;
jangan berasumsi terurut waktu.

```json
{"device_id":"864636051234501","recorded_at":"2026-08-03T01:03:00Z","latitude":-6.1751,"longitude":106.865,"speed_kph":28.0,"heading":90,"ignition":true,"satellites":9}
```

| Field | Tipe | Catatan |
|---|---|---|
| `device_id` | string | IMEI perangkat. Bisa berisi perangkat di luar armada. |
| `recorded_at` | string | ISO-8601 **dengan** informasi zona waktu. Tiga varian muncul di data: `...Z`, `...+00:00`, dan `...+07:00`. Ketiganya valid dan harus dibaca dengan benar. |
| `latitude` | number \| null | Derajat desimal. Bisa `null`. |
| `longitude` | number \| null | Derajat desimal. Bisa `null`. |
| `speed_kph` | number | Kecepatan dari GPS. Bisa negatif atau tidak masuk akal. |
| `heading` | number | Arah dalam derajat. Tidak dipakai untuk perhitungan apa pun. |
| `ignition` | boolean | Status kunci kontak. Tidak dipakai untuk deteksi trip di spesifikasi ini. |
| `satellites` | number | Jumlah satelit terkunci. Informasi saja. |

> **Perhatian zona waktu.** `2026-08-03T08:03:00+07:00` dan `2026-08-03T01:03:00Z`
> adalah **waktu yang sama**. Kalau Anda memotong string tanggal alih-alih
> mem-parsing-nya sebagai instant, hasil Anda akan salah. Normalkan semuanya ke UTC.

### 1.2 `data/vehicles.csv`

```csv
device_id,plate_number,vehicle_type,operator
864636051234501,B 9114 SCA,truck,PT Andalan Logistik
```

File ini mendefinisikan **armada resmi**. `device_id` yang tidak ada di sini bukan
milik kami dan harus diabaikan.

---

## 2. Aturan pembersihan data

Terapkan **berurutan**, per record. Record yang gugur di satu langkah tidak diperiksa lagi
di langkah berikutnya. Urutan ini penting kalau Anda melaporkan jumlah per alasan.

| # | Aturan | Buang jika |
|---|---|---|
| 1 | **Perangkat asing** | `device_id` tidak ada di `vehicles.csv` |
| 2 | **Koordinat null** | `latitude` atau `longitude` bernilai `null` |
| 3 | **Koordinat di luar jangkauan** | `latitude` di luar `[-90, 90]` **atau** `longitude` di luar `[-180, 180]` |
| 4 | **Null Island** | `latitude == 0` **dan** `longitude == 0` |
| 5 | **Kecepatan tidak masuk akal** | `speed_kph < 0` **atau** `speed_kph > 200` |
| 6 | **Duplikat** | Pasangan (`device_id`, instant `recorded_at`) sudah pernah muncul. Simpan kemunculan **pertama** di file, buang sisanya. |

Setelah keenam aturan itu, **kelompokkan per `device_id` dan urutkan naik berdasarkan waktu**,
lalu terapkan:

| # | Aturan | Buang jika |
|---|---|---|
| 7 | **Lompatan mustahil (teleport)** | Kecepatan tersirat dari titik **terakhir yang diterima** melebihi **200 km/jam**. Rumus: `jarak_haversine_km / selisih_waktu_jam`. Titik yang ditolak **tidak** menjadi acuan untuk titik berikutnya — tetap bandingkan dengan titik terakhir yang diterima. |

> Aturan 7 harus dievaluasi setelah pengurutan waktu, dan bersifat berurutan —
> hasilnya bergantung pada titik mana saja yang sudah Anda terima sebelumnya.

**Angka acuan.** Dari 9.076 baris, **432 record** seharusnya terbuang dan
**8.644 record** lolos. Kalau angka Anda meleset jauh, kemungkinan ada aturan
yang salah tafsir. (Rincian per alasan tidak kami publikasikan — sengaja.)

---

## 3. Deteksi trip

Bekerja per kendaraan, atas record bersih yang sudah terurut waktu naik.

### 3.1 Konstanta

| Konstanta | Nilai |
|---|---|
| `MOVING_THRESHOLD_KPH` | `3.0` |
| `STOP_TIMEOUT_SECONDS` | `300` (5 menit) |
| `GAP_TIMEOUT_SECONDS` | `1800` (30 menit) |
| `EARTH_RADIUS_KM` | `6371.0088` |

Sebuah posisi disebut **bergerak** jika `speed_kph >= MOVING_THRESHOLD_KPH`.

### 3.2 Algoritma

Telusuri posisi satu per satu, sambil menyimpan trip yang sedang terbuka dan
indeks **posisi bergerak terakhir** di dalam trip itu.

Untuk setiap posisi `p`:

1. **Putus karena jeda transmisi.** Jika selisih waktu `p` dengan posisi **sebelumnya**
   lebih dari `GAP_TIMEOUT_SECONDS`, tutup trip yang sedang terbuka.
2. **Putus karena berhenti.** Jika ada trip terbuka dan selisih waktu `p` dengan
   **posisi bergerak terakhir** sudah mencapai `STOP_TIMEOUT_SECONDS` atau lebih,
   tutup trip itu.
3. **Mulai atau lanjutkan.**
   - Kalau tidak ada trip terbuka: `p` memulai trip baru **hanya jika** `p` bergerak.
   - Kalau ada trip terbuka: tambahkan `p` ke trip. Kalau `p` bergerak, perbarui
     penanda posisi bergerak terakhir.

Setelah posisi terakhir sebuah kendaraan habis, tutup trip yang masih terbuka.

**Menutup trip** berarti: potong trip pada **posisi bergerak terakhir**. Posisi diam
di ekor trip dibuang — trip berakhir di titik terakhir kendaraan benar-benar bergerak.
Posisi diam **di tengah** trip (misalnya berhenti di lampu merah selama 2 menit)
tetap dipertahankan dan tetap dihitung jaraknya.

### 3.3 Trip yang dibuang

Setelah dipotong, buang trip jika **salah satu** terpenuhi:

- jumlah posisi `< 2`
- `duration_seconds < 60`
- `distance_km < 0.2`

### 3.4 Perhitungan

Untuk posisi trip `p[0..n-1]`:

| Field | Cara hitung |
|---|---|
| `distance_km` | Jumlah jarak **haversine** antar posisi berurutan, `p[i] → p[i+1]`, untuk seluruh `i`. Dibulatkan **3 desimal**. |
| `duration_seconds` | `p[n-1].recorded_at − p[0].recorded_at`, dalam detik, sebagai bilangan bulat. |
| `max_speed_kph` | `speed_kph` terbesar di seluruh posisi trip. Dibulatkan **1 desimal**. |
| `avg_speed_kph` | `distance_km / (duration_seconds / 3600)`. Dibulatkan **2 desimal**. Ini kecepatan rata-rata **berbasis jarak**, bukan rata-rata dari kolom `speed_kph`. |
| `start_time` / `end_time` | ISO-8601 UTC, format `YYYY-MM-DDTHH:MM:SSZ`. |
| `start_latitude` / `start_longitude` | Koordinat `p[0]`, dibulatkan **6 desimal**. |
| `end_latitude` / `end_longitude` | Koordinat `p[n-1]`, dibulatkan **6 desimal**. |
| `point_count` | `n`. |

**Rumus haversine** (pakai persis ini supaya angka Anda cocok):

```
dφ = radians(lat₂ − lat₁)
dλ = radians(lon₂ − lon₁)
a  = sin²(dφ/2) + cos(radians(lat₁)) · cos(radians(lat₂)) · sin²(dλ/2)
d  = 2 · EARTH_RADIUS_KM · asin(√a)
```

**Toleransi penilaian.** Kami menerima selisih hingga **±0,5%** pada `distance_km`
dan `avg_speed_kph` untuk mengakomodasi perbedaan floating point antar bahasa.
`start_time`, `end_time`, `duration_seconds`, dan `point_count` harus **persis**.

---

## 4. Kontrak HTTP API

Layanan berjalan di **port `8080`** kecuali README Anda menyebutkan lain.
Semua respons `Content-Type: application/json`.

### `GET /health`

```json
{ "status": "ok" }
```
`200`. Harus merespons meski data belum selesai dimuat.

---

### `GET /vehicles`

```json
{
  "vehicles": [
    {
      "device_id": "864636051234501",
      "plate_number": "B 9114 SCA",
      "vehicle_type": "truck",
      "operator": "PT Andalan Logistik",
      "trip_count": 12,
      "total_distance_km": 234.567
    }
  ]
}
```
> Angka pada contoh di atas **ilustratif** — bukan jawaban dataset penuh.

Kedelapan kendaraan dari `vehicles.csv` harus muncul — termasuk yang `trip_count`-nya `0`.
Urutan bebas.

---

### `GET /vehicles/{device_id}/trips`

Parameter query (keduanya opsional):

| Parameter | Format | Arti |
|---|---|---|
| `from` | ISO-8601 | Sertakan trip yang `start_time`-nya **>=** nilai ini |
| `to` | ISO-8601 | Sertakan trip yang `start_time`-nya **<** nilai ini |

Filter dilakukan atas `start_time`, bukan `end_time`. Batas bawah inklusif,
batas atas eksklusif.

```json
{
  "device_id": "864636051234501",
  "trip_count": 2,
  "trips": [
    {
      "device_id": "864636051234501",
      "start_time": "2026-08-03T01:03:00Z",
      "end_time": "2026-08-03T01:07:30Z",
      "duration_seconds": 270,
      "distance_km": 1.741,
      "max_speed_kph": 42.0,
      "avg_speed_kph": 23.21,
      "start_latitude": -6.1751,
      "start_longitude": 106.865,
      "end_latitude": -6.1751,
      "end_longitude": 106.88075,
      "point_count": 9
    }
  ]
}
```

Trip terurut naik berdasarkan `start_time`.

**Kode status:**

| Situasi | Status |
|---|---|
| Perangkat ada di armada | `200` (walau `trips` kosong) |
| `device_id` tidak ada di `vehicles.csv` | `404` |
| `from` atau `to` bukan ISO-8601 yang valid | `400` |
| `from` lebih besar dari `to` | `400` |

Badan respons error bebas bentuknya, asalkan JSON dan memuat pesan yang bisa dibaca manusia.

---

### `GET /summary`

Menerima `from` dan `to` yang sama persis dengan endpoint trips.

```json
{
  "from": "2026-08-03T00:00:00Z",
  "to": "2026-08-10T00:00:00Z",
  "total_trips": 123,
  "total_distance_km": 2345.67,
  "total_duration_seconds": 234567,
  "active_vehicles": 8,
  "top_vehicles_by_distance": [
    { "device_id": "864636051234505", "plate_number": "D 8891 UCK", "total_distance_km": 456.789, "trip_count": 21 }
  ]
}
```

| Field | Arti |
|---|---|
| `from` / `to` | Kembalikan nilai yang dipakai. Kalau parameter tidak diberikan, gunakan `null`. |
| `total_trips` | Jumlah trip dalam rentang |
| `total_distance_km` | Total jarak, dibulatkan 2 desimal |
| `total_duration_seconds` | Total durasi, bilangan bulat |
| `active_vehicles` | Jumlah kendaraan dengan **minimal satu** trip dalam rentang |
| `top_vehicles_by_distance` | Maksimal **5** kendaraan, terurut turun berdasarkan `total_distance_km` |

> Sekali lagi: angka pada contoh di atas ilustratif. Satu-satunya angka dataset
> penuh yang kami publikasikan adalah **432 record terbuang / 8.644 lolos** di Bagian 2.

---

## 5. Cara memuat data

Silakan pilih pendekatan Anda sendiri: muat sekali saat layanan menyala, sediakan
perintah impor terpisah, atau simpan ke database. Jelaskan pilihan Anda di `SUBMISSION.md`.

Yang penting: **`verify/verify.py` harus bisa jalan tanpa langkah manual tambahan
selain yang tertulis di README Anda.**

---

## 6. Contoh terverifikasi

[`examples/sample-input.ndjson`](examples/sample-input.ndjson) berisi 36 baris yang
memuat **setiap** jenis data kotor dari Bagian 2, ditambah kasus-kasus batas deteksi trip:
berhenti di lampu merah **di dalam** trip, berhenti 5 menit yang **memotong** trip,
perjalanan pendek yang **dibuang** karena kurang dari 200 m, dan jeda 30 menit lebih.

[`examples/expected-output.json`](examples/expected-output.json) adalah jawaban yang benar:
**3 trip**.

Cocokkan dengan file itu dulu. Kalau sudah sama persis, barulah lanjut ke dataset penuh.
