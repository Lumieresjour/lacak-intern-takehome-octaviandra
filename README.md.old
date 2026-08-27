# Take-Home Test — Software Engineer Intern @ Lacak

Halo! 👋 Terima kasih sudah tertarik magang di **Lacak**.

Kami bikin platform *fleet tracking* — ribuan GPS tracker di truk, van, dan alat berat
mengirim posisi ke sistem kami setiap beberapa detik. Data mentahnya berantakan:
sinyal hilang di terowongan, perangkat mengirim ulang paket yang sama, koordinat
kadang jatuh di tengah Samudra Atlantik. Tugas kami mengubah semua itu jadi angka
yang bisa dipercaya pelanggan.

**Take-home ini adalah versi mini dari pekerjaan itu.** Bukan puzzle algoritma,
bukan pertanyaan jebakan — ini benar-benar hal yang kami kerjakan tiap hari.

---

## TL;DR

| | |
|---|---|
| **Waktu yang kami harapkan** | 4–6 jam. Serius — jangan habiskan seminggu. |
| **Deadline** | 5 hari kalender sejak email undangan |
| **Bahasa pemrograman** | **Bebas.** Python, Go, Java, TypeScript, Rust, PHP, C#, apa pun. |
| **Yang dikumpulkan** | Link repo Git publik + `SUBMISSION.md` yang sudah diisi |
| **Yang dinilai** | Lihat [`RUBRIC.md`](RUBRIC.md) — kami buka rubriknya, tidak ada penilaian rahasia |

---

## Tugas

Bangun sebuah layanan kecil yang membaca *feed* posisi GPS mentah, membersihkannya,
memotongnya menjadi **perjalanan (trip)**, lalu menyajikannya lewat **HTTP API**.

Tiga bagian:

### 1. Ingest & bersihkan
Baca [`data/positions.ndjson`](data/positions.ndjson) (9.076 baris) dan
[`data/vehicles.csv`](data/vehicles.csv) (8 kendaraan).

Data ini **sengaja kotor** — ada duplikat, koordinat null, koordinat `0,0`,
lompatan posisi yang mustahil secara fisika, perangkat yang tidak terdaftar,
dan urutan waktu yang acak. Semua aturan pembersihannya ada di [`SPEC.md`](SPEC.md).

### 2. Deteksi trip
Potong posisi yang sudah bersih menjadi trip, lalu hitung untuk tiap trip:
jarak tempuh, durasi, kecepatan maksimum dan rata-rata, titik awal dan akhir.
Aturan lengkap + angka ambangnya ada di [`SPEC.md`](SPEC.md).

### 3. Sajikan lewat HTTP API
Empat endpoint: `/health`, `/vehicles`, `/vehicles/{device_id}/trips`, `/summary`.
Kontrak persisnya (skema respons, kode error, parameter) ada di [`SPEC.md`](SPEC.md).

---

## Yang kami harapkan ada

- [ ] **Kode sumber** di repo Git publik (GitHub/GitLab/Bitbucket), riwayat commit rapi
- [ ] **README** dengan cara menjalankan — idealnya **satu perintah**
- [ ] **Test otomatis** untuk logika inti (pembersihan data & deteksi trip)
- [ ] **[`SUBMISSION.md`](SUBMISSION.md)** yang sudah diisi — ceritakan keputusan dan trade-off Anda

## Bonus (opsional, kerjakan hanya kalau tugas inti sudah beres)

Pilih yang menurut Anda paling menarik — **tidak perlu semuanya**, dan mengerjakan
nol bonus dengan tugas inti yang rapi **lebih baik** daripada empat bonus setengah jadi.

- `Dockerfile` / `docker-compose.yml` sehingga cukup `docker compose up`
- Simpan hasil ke database (SQLite/Postgres) alih-alih di memori
- Endpoint tambahan: rekap harian per kendaraan, atau deteksi waktu *idle*
- Penanganan file besar (streaming, tidak memuat semuanya ke memori)
- CI sederhana (GitHub Actions) yang menjalankan test Anda

---

## Cara mulai

```bash
git clone https://github.com/Lacak-Cipta-Actual/lacak-intern-takehome.git
cd lacak-intern-takehome

# 1. Baca spesifikasinya — ini sumber kebenaran, bukan README ini
$EDITOR SPEC.md

# 2. Lihat contoh kecil yang sudah ada jawabannya
cat examples/sample-input.ndjson      # 36 baris, memuat SEMUA jenis data kotor
cat examples/expected-output.json     # 3 trip yang seharusnya Anda hasilkan

# 3. Bangun di repo Anda sendiri, lalu cek kontrak API Anda
python3 verify/verify.py http://localhost:8080
```

`examples/` adalah teman terbaik Anda. Kalau program Anda menghasilkan tepat 3 trip
itu dari 36 baris tersebut, kemungkinan besar interpretasi Anda terhadap spesifikasi
sudah benar. **Mulai dari situ sebelum menyentuh dataset penuh.**

[`verify/verify.py`](verify/verify.py) adalah pemeriksa kontrak API — Python 3.9+,
tanpa dependensi. Skrip itu **tidak** menilai kebenaran perhitungan Anda,
hanya memastikan bentuk API-nya sesuai. Lulus `verify.py` itu syarat minimum, bukan nilai bagus.

---

## Aturan main

**Boleh:** cari di internet, baca dokumentasi, pakai library apa pun (HTTP framework,
parser, test runner), meminjam ide dari Stack Overflow.

**Soal AI (Copilot, Claude, ChatGPT, Cursor):** **boleh dipakai** — kami juga memakainya
di sini. Dua syarat, dan kami serius soal ini:

1. Tulis di `SUBMISSION.md` bagian mana yang dibantu AI. Jujur saja; ini tidak mengurangi nilai.
2. Anda harus bisa **menjelaskan setiap baris** kode Anda saat interview. Kami akan menunjuk
   satu fungsi acak dan bertanya kenapa ditulis begitu, apa yang terjadi kalau inputnya kosong,
   dan kenapa Anda pilih pendekatan itu. Di sinilah kejujuran itu terlihat.

**Tidak boleh:** menyerahkan pekerjaan orang lain sebagai milik Anda.

---

## Kalau ada yang tidak jelas

Spesifikasi yang ambigu itu bagian dari pekerjaan nyata. Kalau [`SPEC.md`](SPEC.md)
tidak menjawab pertanyaan Anda:

1. **Ambil keputusan yang masuk akal, lalu tulis alasannya di `SUBMISSION.md`.**
   Ini yang kami cari — engineer yang bisa jalan tanpa harus dituntun.
2. Kalau benar-benar buntu, buka [issue di repo ini](../../issues) atau email
   **produk.lacak@gmail.com**. Pertanyaan bagus tidak mengurangi nilai Anda.

Pertanyaan yang jelas akan kami jawab di issue publik supaya semua kandidat dapat
informasi yang sama.

---

## Cara mengumpulkan

Balas email undangan Anda dengan:

1. Link repo Git **publik** Anda
2. Perkiraan waktu yang benar-benar Anda habiskan (jujur — kami tidak menghukum angka besar atau kecil)

Jangan buat pull request ke repo ini.

---

## Kenapa soalnya seperti ini

Kami sengaja tidak memberi soal LeetCode. Yang ingin kami lihat:

- Apakah Anda **membaca spesifikasi dengan teliti** sebelum menulis kode
- Bagaimana Anda memperlakukan **data yang tidak bisa dipercaya** — ini 80% pekerjaan telematics
- Apakah Anda **menulis test**, dan test apa yang Anda pilih
- Apakah orang lain bisa **menjalankan dan membaca** kode Anda enam bulan dari sekarang
- Apakah Anda bisa **menjelaskan keputusan** Anda

Kami tidak mencari kode yang sempurna. Kami mencari orang yang berpikir jernih dan jujur
tentang apa yang belum selesai. Kalau Anda kehabisan waktu, tulis di `SUBMISSION.md`
apa yang akan Anda kerjakan berikutnya — itu bagian dari penilaian.

Semoga berhasil. Kami tunggu hasilnya. 🚚

---

<sub>Repositori ini dilisensikan MIT — silakan fork, pakai untuk latihan, atau jadikan
referensi take-home test di tempat lain.</sub>
