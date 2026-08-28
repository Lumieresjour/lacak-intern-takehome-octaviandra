## Cara Menjalankan

### Menjalankan tanpa Docker

```bash
python run.py
```

Gunakan `python run.py --port 9000` untuk port lain.

jika ingin test dataset sample-input.njson(default ke positions.ndjson)
```bash
python run.py --input examples/sample-input.ndjson
```

### Menjalankan dengan Docker

Prasyarat: Docker Desktop dengan Docker Compose.

```bash
docker compose up --build
```

Nantinya API tersedia di `http://localhost:8080`. Saat startup, aplikasi memproses
`data/positions.ndjson` dan `data/vehicles.csv`.

jika ingin test dataset sample-input.njson(default ke positions.ndjson)

```terminal
$env:INPUT_FILE = 'examples/sample-input.ndjson'
docker compose up --build
```

Untuk menghentikan:

```bash
docker compose down
```
## File database SQLite dengan nama "hasil_bonus.db" akan otomatis terbuat

## verifikasi

Ketika server localhost sedang berjalan di terminal lain, periksa dengan:

```bash
python verify/verify.py http://localhost:8080
```