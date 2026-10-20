# IHSG & Saham IDX: Risiko vs Imbal Hasil

Analitik 22 saham likuid Bursa Efek Indonesia plus IHSG sebagai benchmark. Satu perintah
mengunduh harga 5 tahun, menghitung 10 metrik risiko, menggambar empat grafik, dan menulis
laporan markdown. Semua angka dihitung ulang saat pipeline jalan.

Data contoh di bawah: periode **21 Oktober 2021 - 19 Oktober 2026**, 1.198 hari bursa.

## Angka utama (periode contoh)

| Ukuran | IHSG |
|---|---|
| Level terakhir | 4.996,61 |
| CAGR 5 tahun | **-5,8%** |
| Imbal hasil tahun berjalan | **-42,9%** |
| Volatilitas tahunan | 17,8% |
| Drawdown terdalam | **-45,3%** |
| Posisi sekarang dari puncak | -45,3% (titik terendah periode) |
| Hari ditutup naik | 52,4% |
| Hari terburuk | 16 Okt 2026, -11,6% |

Periode ini berat: 17 dari 22 saham punya Sharpe negatif, artinya imbal hasilnya kalah dari
aset bebas risiko. Yang bertahan justru emiten batu bara dan alat berat: **ADRO** (CAGR 33,9%,
Sharpe 0,66), **PTBA** (20,3%, 0,43), **UNTR** (9,8%, 0,12).

Yang paling hancur: **SMGR** (-31,3% per tahun, Sharpe -0,89), **GOTO** (-47,6%, -0,87), dan
**ARTO** (-49,3%, -0,87 dengan drawdown -96,9%).

## Yang bisa dibaca dari data ini

- **Saham batu bara menang bukan karena pasar naik, tapi karena tidak ikut jatuh.** Korelasi
  ADRO ke IHSG hanya 0,36, terendah di antara 22 emiten. Volatilitasnya tinggi (42,9%), tapi
  arahnya lepas dari indeks.
- **Beta tidak selalu berarti risiko besar.** ARTO punya beta 1,60, tertinggi di sampel, dan
  memang jadi yang terburuk. Tapi INDF dengan beta 0,39 juga negatif Sharpe, karena
  volatilitas rendah tidak menolong kalau imbal hasilnya di bawah suku bunga.
- **Pola musiman Indonesia terlihat jelas di samping tren yang buruk.** Juli rata-rata +5,2%
  dan selalu positif dalam 5 tahun pengamatan; Agustus +3,7% juga selalu positif. Sebaliknya
  Mei (-2,9%, hanya 20% bulan positif) dan Oktober (-3,1%) paling sering merah.

## Gambar

![Risiko vs imbal hasil](outputs/figures/01_risiko_imbal_hasil.png)

![Pertumbuhan 100 rupiah, skala log](outputs/figures/02_pertumbuhan_100.png)

![Kurva drawdown](outputs/figures/03_drawdown.png)

![Musiman bulanan IHSG](outputs/figures/04_musiman_bulanan.png)

## Metrik yang dihitung

Per saham, di `outputs/metrik.csv`:

| Metrik | Definisi |
|---|---|
| CAGR 5 tahun | imbal hasil geometrik harian disetahunkan (252 hari bursa) |
| Imbal hasil 1 tahun | perubahan harga 252 hari bursa terakhir |
| Volatilitas tahunan | standar deviasi imbal hasil harian x akar 252 |
| Sharpe | (CAGR - rf) / volatilitas |
| Sortino | (CAGR - rf) / downside deviation |
| Beta | kovarians dengan IHSG / varians IHSG |
| Max drawdown | penurunan terdalam dari puncak |
| VaR 95% harian | persentil ke-5 imbal hasil harian, dilaporkan sebagai kerugian positif |
| Calmar | CAGR / absolut max drawdown |
| Korelasi IHSG | korelasi imbal hasil harian dengan indeks |

Aset bebas risiko default 5,75% per tahun, bisa diganti lewat `--rf`.

## Cara jalan

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

python -m idx_analytics.cli              # pakai cache kalau ada
python -m idx_analytics.cli --segarkan   # paksa unduh ulang dari Yahoo Finance
python -m pytest                         # 11 tes, tanpa jaringan
```

Opsi lain: `--periode 3y`, `--rf 0.06`, `--outdir outputs`.

Kalau Yahoo Finance sedang tidak bisa diakses, pipeline otomatis jatuh ke cache
`data/harga.csv` dan menandai sumbernya di laporan (`sumber: cache`).

## Struktur

```
ihsg-idx-analytics/
  src/idx_analytics/
    fetch.py     unduh Yahoo Finance, cache, fallback offline
    metrics.py   10 metrik murni (bisa diuji tanpa data pasar)
    analysis.py  tabel metrik, ringkasan pasar, korelasi, musiman, temuan
    charts.py    scatter risiko-imbal hasil, pertumbuhan, drawdown, musiman
    report.py    laporan markdown
    cli.py       orkestrator
  tests/test_metrics.py   11 tes dengan deret sintetis
  outputs/                laporan, csv, grafik
```

## Batasan yang perlu disebut

- Universe 22 saham dipilih manual dari emiten likuid, **bukan** seluruh bursa, dan mengandung
  survivorship bias karena hanya emiten yang masih tercatat hari ini yang masuk.
- Harga dari Yahoo Finance, bukan dari IDX langsung. Selisih pembulatan dan aksi korporasi bisa
  berbeda tipis dari data resmi BEI.
- Ini analisis statistik historis, **bukan** rekomendasi investasi.

## Lisensi

MIT.
