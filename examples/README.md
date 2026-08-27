# Contoh terverifikasi

**Mulai dari sini.** Jangan sentuh `../data/positions.ndjson` sebelum program Anda
menghasilkan output yang persis sama dengan `expected-output.json`.

| File | Isi |
|---|---|
| `sample-input.ndjson` | 36 baris, format identik dengan dataset penuh |
| `expected-output.json` | Jawaban yang benar: **3 trip** |

## Apa yang diuji contoh ini

`sample-input.ndjson` memuat **setiap** jenis data kotor dari SPEC Bagian 2 —
duplikat, koordinat null, Null Island, lintang di luar jangkauan, kecepatan negatif,
perangkat asing, dan satu lompatan teleport — ditambah kasus batas deteksi trip:

- **Berhenti di lampu merah di dalam trip** — dua titik di bawah 3 km/jam selama 60 detik.
  Trip **tidak** boleh terpotong, dan kedua titik itu tetap dihitung jaraknya.
- **Berhenti yang memotong trip** — diam lebih dari 5 menit. Trip harus ditutup pada
  titik bergerak **terakhir**, bukan pada titik diam pertama.
- **Perjalanan yang harus dibuang** — bergerak ~50 m saja, di bawah ambang 200 m.
- **Jeda transmisi 30 menit lebih** — memutus trip meskipun kendaraan lanjut jalan.
- **Zona waktu campur** — satu baris ditulis sebagai `+07:00`. Kalau Anda memotong
  string alih-alih mem-parsing instant, trip pertama Anda akan salah.

## Cara memakainya

```bash
# arahkan pipeline Anda ke sample, lalu bandingkan
diff <(jq -S . hasil-anda.json) <(jq -S . examples/expected-output.json)
```

Kalau ketiga trip cocok — waktu, jarak, `point_count`, semuanya — interpretasi Anda
terhadap spesifikasi hampir pasti sudah benar.

Kalau **jumlah trip** Anda bukan 3, biasanya penyebabnya:

| Anda dapat | Kemungkinan sebabnya |
|---|---|
| 1 atau 2 trip | Trip tidak ditutup saat titik berikutnya sudah bergerak — periksa langkah 2 di SPEC 3.2 |
| 4 trip | Perjalanan pendek (< 200 m) tidak dibuang, atau berhenti di lampu merah ikut memotong trip |
| 3 trip tapi angkanya beda | Ekor diam tidak dipotong, atau baris `+07:00` salah di-parse |
