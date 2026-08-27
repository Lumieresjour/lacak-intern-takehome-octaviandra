# Dataset

Data sintetis, dihasilkan dengan seed tetap. Tidak ada data pelanggan Lacak
yang asli di sini — tapi pola kerusakannya diambil dari yang benar-benar kami
temui di produksi.

| File | Isi |
|---|---|
| `positions.ndjson` | 9.076 posisi GPS mentah, **urutan acak**, satu objek JSON per baris |
| `vehicles.csv` | 8 kendaraan — inilah definisi armada resmi |

Rentang waktu: **3–10 Agustus 2026** (satu minggu penuh), tiga kota
(Jakarta, Bandung, Surabaya). Interval transmisi ~30 detik saat bergerak,
~60 detik saat parkir.

## Data ini sengaja dirusak

Setiap jenis kerusakan di bawah benar-benar ada di file, dalam jumlah yang cukup
untuk mempengaruhi hasil akhir kalau Anda melewatkannya:

- **Kirim ulang duplikat** — perangkat mengirim frame yang sama dua kali saat sinyal buruk
- **Koordinat `null`** — GPS belum dapat *fix*, biasanya `satellites: 0`
- **Null Island** — koordinat `0, 0`, kegagalan klasik firmware tracker
- **Koordinat di luar jangkauan** — frame rusak, lintang `> 90` atau bujur `> 180`
- **Lompatan mustahil** — posisi meloncat ratusan kilometer dalam hitungan detik
- **Perangkat asing** — IMEI yang tidak ada di `vehicles.csv`
- **Kecepatan tidak masuk akal** — nilai negatif, atau ratusan km/jam
- **Zona waktu campur** — instant yang sama ditulis sebagai `Z`, `+00:00`, dan `+07:00`
- **Waktu tidak terurut** — baris diacak; jangan berasumsi terurut

Aturan penanganan lengkapnya ada di [`../SPEC.md`](../SPEC.md) Bagian 2.

Jumlah tiap jenis **tidak** kami publikasikan. Yang kami beri: dari 9.076 baris,
**432 terbuang** dan **8.644 lolos**.

## Cara mengintip isinya

```bash
head -3 data/positions.ndjson
wc -l data/positions.ndjson

# lihat contoh baris bermasalah
grep -m3 '"latitude":null' data/positions.ndjson
grep -m3 '+07:00'          data/positions.ndjson
```
