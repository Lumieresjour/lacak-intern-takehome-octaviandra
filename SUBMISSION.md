# Submission

Salin file ini ke repo Anda dan isi. Bahasa Indonesia atau Inggris, bebas.

Tidak perlu panjang — **satu halaman sudah cukup**. Kami menilai kejujuran dan
kejernihan berpikir, bukan jumlah kata.

---

## Identitas

- **Nama:*Octaviandra Adhitya Ariepratama*
- **Repo:**
- **Waktu yang benar-benar dihabiskan:** 5-6 jam
  <sub>(jujur saja — kami tidak menghukum angka besar maupun kecil)</sub>

---

## Cara menjalankan

```bash
git clone <https://github.com/Lumieresjour/lacak-intern-takehome-octaviandra>
cd <folder-ini>
python run.py
```

## verify API

```bash
python verify/verify.py http://localhost:8080
```

### Menjalankan dengan Docker Compose

```bash
docker compose up --build
```

API dapat diakses di `http://localhost:8080`. Verifier Compose menjalankan
`python verify/verify.py http://app:8080`. Untuk menghentikan container:

```bash
docker compose down
```

**Port:** 8080

---

## Stack yang dipilih


**Bahasa: Python**
Python dipilih karena sudah familiar dari matakuliah diperkuliahan, Selain itu, file pengujian (verify.py) berbasis Python, sehingga penyesuaian dapat dilakukan dengan lebih cepat.

**HTTP: `http.server.ThreadingHTTPServer`**
dari standard library python bukan FastAPI.

---

## Ambiguitas yang saya temukan

- Perbedaan representasi timezone ("Z" vs "+00:00") tapi sudah diselesaikan dengan normalisasi ke UTC.
- Jika ada record dengan `recorded_at` tidak bisa di-parse, record tersebut dibuang sebagai invalid.

---

## Keputusan teknis

- Parser timestamp: `datetime.fromisoformat(...replace('Z','+00:00'))` lalu `astimezone(timezone.utc)` — konsisten dengan verify script.
- Duplikat: key (device_id, instant_utc_str) dihasilkan dari instant UTC yang dinormalisasi (`YYYY-MM-DDTHH:MM:SSZ`). Hanya kemunculan pertama dalam file yang disimpan.
- Aturan teleport (aturan 7) dievaluasi *setelah* posisi diurutkan per device. Titik yang ditolak tidak mengubah titik pembanding berikutnya.
- Posisi mentah diproses sementara selama import; hasil trip di SQLite
  sehingga endpoint tidak bergantung pada hasil kalkulasi.

---

## Yang belum selesai

- Koneksi SQLite tunggal hanya cukup untuk beban rendah, tapi akan menjadi bottleneck kalau traffic baca jauh lebih tinggi jadi belum ada connection pool.
- Tidak ada rate limiting atau autentikasi di endpoint
- Integration test API di CI.
- Endpoint tambahan: rekap harian per kendaraan, atau deteksi waktu idle.
- Penanganan file besar (streaming, tidak memuat semuanya ke memori)

---

## Kalau punya 4 jam lagi

- Integration test API di CI.
- Endpoint tambahan: rekap harian per kendaraan, atau deteksi waktu idle.
- Penanganan file besar (streaming, tidak memuat semuanya ke memori)

---

## Penggunaan AI

- **Perkakas:** Claude  dan Copilot
- **Dipakai untuk:** Struktur tambahan di bagian `api.py`, `config.py`, `db.py`, `main.py`, dan `processing.py`, Review codebase untuk mencari edge case yang belum tertangani, dan menyusun rekomendasi perbaikan arsitektur (locking, readiness probe, transaksi database, konfigurasi Docker).
- **Bagian yang saya tulis sepenuhnya sendiri:** Logika inti pembersihan data dan deteksi trip awal di `processing.py`, struktur endpoint di `api.py`, serta keputusan stack dan struktur direktori.

---

## Catatan lain

Angka 432 terbuang / 8.644 lolos dari `data/positions.ndjson` sudah saya konfirmasi cocok persis dengan yang dipublikasikan di `SPEC.md`.