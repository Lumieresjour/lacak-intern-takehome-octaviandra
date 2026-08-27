# verify.py

Pemeriksa kontrak API. Python 3.9+, tanpa dependensi.

```bash
# jalankan layanan Anda dulu, lalu:
python3 verify/verify.py http://localhost:8080
```

Argumen bersifat opsional — default-nya `http://localhost:8080`.

## Yang diperiksa

- Keempat endpoint ada dan mengembalikan JSON dengan skema benar
- Kedelapan kendaraan muncul di `/vehicles`
- Trip terurut naik berdasarkan `start_time` dan punya semua field wajib
- `from` inklusif, `to` eksklusif
- `404` untuk perangkat tak dikenal, `400` untuk tanggal tak valid dan rentang terbalik
- `/summary` konsisten dengan penjumlahan `/vehicles`
- Konsistensi internal tiap trip: `duration == end − start`,
  `avg_speed == distance / (duration/3600)`, tidak ada trip di bawah ambang minimum

## Yang TIDAK diperiksa

Skrip ini tidak tahu jawaban yang benar. Skrip ini **tidak bisa** memberitahu Anda
apakah pembersihan data dan deteksi trip Anda sudah benar — untuk itu, gunakan
[`../examples/`](../examples/).

**Lulus `verify.py` adalah syarat minimum, bukan nilai bagus.**

## Kode keluar

| Kode | Arti |
|---|---|
| `0` | Semua cek lulus |
| `1` | Ada cek yang gagal |
| `2` | Layanan tidak bisa dihubungi |

Cocok dipakai di CI. Kalau Anda menambahkan GitHub Actions, jalankan skrip ini
terhadap layanan Anda sendiri — itu nilai tambah.
