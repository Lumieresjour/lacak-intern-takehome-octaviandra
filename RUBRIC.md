# Rubrik Penilaian

Kami membuka rubrik ini supaya Anda tahu persis ke mana harus mengalokasikan
4–6 jam Anda. Tidak ada kriteria tersembunyi.

**Total 100 poin.** Reviewer mengisi kartu ini per submission.

---

## Kebenaran — 35 poin

| Poin | Kriteria |
|---:|---|
| 12 | **Pembersihan data.** Keenam aturan Bagian 2 diterapkan dengan benar, termasuk urutannya. Jumlah record yang lolos sesuai. |
| 8 | **Deteksi teleport.** Aturan 7 dievaluasi setelah pengurutan waktu, dibandingkan terhadap titik terakhir yang *diterima* (bukan titik sebelumnya apa adanya). |
| 10 | **Segmentasi trip.** Batas trip benar: berhenti di tengah tetap masuk trip, ekor diam terpotong, jeda transmisi memutus trip, trip terlalu pendek dibuang. |
| 5 | **Perhitungan.** Jarak, durasi, kecepatan maksimum & rata-rata sesuai toleransi ±0,5%. Pembulatan sesuai spesifikasi. |

Cek cepat kami: apakah `examples/expected-output.json` direproduksi persis?
Kalau ya, biasanya sisanya ikut benar.

---

## Kelengkapan API — 15 poin

| Poin | Kriteria |
|---:|---|
| 6 | Keempat endpoint ada dan mengembalikan skema yang benar |
| 4 | Filter `from` / `to` benar — inklusif di bawah, eksklusif di atas, atas `start_time` |
| 5 | Kode error benar: `404` perangkat tak dikenal, `400` tanggal tak valid, `400` rentang terbalik |

`verify/verify.py` mengecek sebagian besar bagian ini secara otomatis.

---

## Kualitas kode — 20 poin

| Poin | Kriteria |
|---:|---|
| 6 | **Pemisahan tanggung jawab.** Parsing, pembersihan, segmentasi, dan lapisan HTTP tidak menyatu dalam satu fungsi raksasa. |
| 5 | **Penamaan & keterbacaan.** Reviewer bisa mengikuti alurnya tanpa bertanya. |
| 4 | **Konstanta bernama.** Angka `3.0`, `300`, `1800`, `200` tidak berserakan sebagai angka telanjang. |
| 5 | **Penanganan error.** Baris rusak tidak membuat proses mati; kegagalan ditangani secara eksplisit, bukan ditelan diam-diam. |

Kami **tidak** menilai gaya format, pilihan framework, atau selera arsitektur.
Idiomatik untuk bahasa Anda sudah cukup.

---

## Testing — 15 poin

| Poin | Kriteria |
|---:|---|
| 6 | Ada test otomatis yang benar-benar jalan lewat satu perintah |
| 5 | **Kasus batas diuji**, bukan cuma jalur bahagia. Contoh yang kami cari: koordinat null, trip yang harus dibuang, jeda 30 menit, dua zona waktu berbeda menghasilkan instant yang sama. |
| 4 | Test membaca sebagai spesifikasi — nama test menjelaskan perilaku yang diuji |

Tiga test kasus batas yang tajam lebih bernilai daripada tiga puluh test dangkal.
Kami tidak punya target angka coverage.

---

## Dokumentasi & pengalaman menjalankan — 10 poin

| Poin | Kriteria |
|---:|---|
| 5 | Reviewer bisa menjalankan proyek Anda dalam **< 5 menit** dari `git clone`, hanya dengan mengikuti README |
| 3 | README menjelaskan struktur proyek dan cara menjalankan test |
| 2 | Riwayat commit rapi — bukan satu commit `final` berisi semuanya |

---

## Komunikasi — 5 poin

| Poin | Kriteria |
|---:|---|
| 5 | `SUBMISSION.md` terisi jujur: ambiguitas apa yang Anda temukan, keputusan apa yang Anda ambil, apa yang belum selesai, dan penggunaan AI diungkap terbuka |

---

## Yang membuat kami terkesan

Bukan bagian dari 100 poin — tapi kami mencatatnya:

- Menemukan ambiguitas nyata di `SPEC.md` yang kami sendiri lewatkan, dan menuliskannya
- Membaca dataset dan menyadari sesuatu yang tidak kami sebutkan
- Test yang gagal saat spesifikasi diterjemahkan salah, bukan sekadar mengunci perilaku kode sendiri
- Mengatakan "saya kehabisan waktu di sini, ini rencana saya berikutnya" dengan spesifik

## Yang merugikan

- Angka dari dataset penuh yang ditulis langsung sebagai konstanta di kode
- Kode salin-tempel yang jelas tidak dipahami penulisnya (akan ketahuan di interview)
- Bonus dikerjakan sementara tugas inti masih rusak
- README yang tidak cocok dengan cara kode sebenarnya dijalankan
- Tidak ada test sama sekali

---

## Setelah take-home

Kalau lolos, langkah berikutnya adalah **interview teknis ±45 menit**. Formatnya:
kami buka kode Anda, menunjuk beberapa bagian, dan meminta Anda menjelaskan.
Lalu kami membahas bagaimana Anda akan menambahkan satu fitur kecil — cukup
diceritakan, tidak perlu ditulis.

**Tidak ada live coding.** Tidak ada whiteboard, tidak ada soal algoritma hafalan.
Kami tidak akan meminta Anda mengetik kode sambil ditonton. Kalau Anda benar-benar
menulis dan memahami submission Anda, sesi itu akan terasa seperti mengobrol.
