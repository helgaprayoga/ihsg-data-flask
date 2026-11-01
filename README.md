# Dashboard Visualisasi Data Harian IHSG (Flask + Chart.js)

Studi kasus visualisasi data untuk mata kuliah Aplikasi Web. Dashboard membaca
data harian IHSG dari `data/ihsg_daily.csv`, mengolahnya di backend Flask, lalu
menampilkannya sebagai kartu statistik dan grafik interaktif dengan Chart.js.

## Data

| Kolom CSV | Arti |
|---|---|
| `Tanggal` | Tanggal perdagangan (DD/MM/YYYY) |
| `Terakhir` | Harga penutupan (close) |
| `Pembukaan` | Harga pembukaan (open) |
| `Tertinggi` | Harga tertinggi (high) |
| `Terendah` | Harga terendah (low) |
| `Vol.` | Volume transaksi (sufiks `B`/`M`) |
| `Perubahan%` | Perubahan harga harian |

Periode data: 4 Januari 2010 – 25 September 2026 (4.073 hari bursa).
Semua angka memakai format Indonesia (`6.241,89`), sehingga di-parse secara
khusus di `app.py`; volume dengan sufiks `M` dikonversi ke miliar dan volume
kosong diabaikan saat menghitung rata-rata.

## Struktur Project

```
.
├── app.py                  # Backend Flask: parsing data, filter, dan API JSON
├── templates/
│   └── dashboard.html      # Frontend: kartu statistik + grafik Chart.js
├── data/
│   ├── ihsg_daily.csv      # Data harian IHSG (sumber utama)
│   └── nilai.csv           # Data contoh lama (tidak dipakai)
├── requirements.txt
├── .gitignore
└── README.md
```

## Menjalankan

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000 di browser. Chart.js dimuat dari CDN, jadi perlu
koneksi internet.

## Fitur Dashboard

- **Kartu statistik**: jumlah hari bursa, close terakhir beserta perubahan
  harian, return periode, dan volume rata-rata (miliar).
- **Return per tahun**: grafik batang return penutupan tiap tahun (hijau untuk
  positif, merah untuk negatif).
- **Distribusi hari naik/turun**: grafik donat jumlah hari naik, turun, dan
  stagnan.
- **Tren harga**: grafik garis close beserta MA20 dan MA50.
- **Filter periode**: 1 Tahun, 3 Tahun, 5 Tahun (default), dan Semua.

## Endpoint

| URL | Isi |
|---|---|
| `/` | Halaman dashboard |
| `/api/ringkasan` | Hari bursa, close terakhir, perubahan harian, return periode, volume rata-rata |
| `/api/tren-harga` | Label tanggal, close, MA20, MA50 |
| `/api/distribusi-arah` | Jumlah hari naik, turun, dan stagnan |
| `/api/return-tahunan` | Return per tahun |

Semua endpoint `/api/...` menerima parameter `?periode=1y|3y|5y|all`
(default `5y`). Contoh:

```text
http://127.0.0.1:5000/api/ringkasan?periode=5y
http://127.0.0.1:5000/api/tren-harga?periode=1y
http://127.0.0.1:5000/api/return-tahunan?periode=all
```

## Catatan Implementasi

- MA20 dan MA50 dihitung dari seluruh data **sebelum** filter periode, agar
  nilainya tetap benar di awal grafik.
- Nilai `NaN` pada awal MA diubah menjadi `null` sebelum dikirim sebagai JSON,
  lalu disambung di Chart.js dengan `spanGaps: true`.
