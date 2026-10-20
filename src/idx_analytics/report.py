"""Laporan markdown untuk analitik IDX."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import analysis

BULAN = analysis.BULAN


def _tgl(nilai) -> str:
    return f"{nilai.day} {BULAN[nilai.month - 1]} {nilai.year}"


def _persen(nilai: float, digit: int = 1) -> str:
    if nilai is None or pd.isna(nilai):
        return "-"
    return f"{nilai * 100:.{digit}f}%".replace(".", ",")


def _angka(nilai: float, digit: int = 2) -> str:
    if nilai is None or pd.isna(nilai):
        return "-"
    return f"{nilai:.{digit}f}".replace(".", ",")


def _tabel(data: pd.DataFrame, kolom: list[str], judul: list[str]) -> str:
    garis = "| " + " | ".join(judul) + " |"
    pisah = "|" + "|".join(["---"] * len(judul)) + "|"
    isi = ["| " + " | ".join(str(row[k]) for k in kolom) + " |" for _, row in data.iterrows()]
    return "\n".join([garis, pisah, *isi])


def tulis_laporan(
    tabel: pd.DataFrame,
    musiman: pd.DataFrame,
    pasar: dict,
    korelasi: pd.DataFrame,
    sumber: str,
    path: Path,
    rf: float,
) -> None:
    baris: list[str] = []
    tb = tabel.copy()

    baris.append("# IHSG dan Saham IDX: Risiko vs Imbal Hasil")
    baris.append("")
    baris.append(
        f"Periode {_tgl(pasar['tanggal_mulai'])} sampai {_tgl(pasar['tanggal_terakhir'])} "
        f"({pasar['hari_observasi']} hari bursa, {len(tb) - 1} saham). "
        f"Sumber harga: {sumber}. Dibuat "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}."
    )
    baris.append("")
    baris.append("## Posisi IHSG")
    baris.append("")
    baris.append("| Ukuran | Nilai |")
    baris.append("|---|---|")
    baris.append(f"| Level terakhir | {pasar['level_terakhir']:,.2f} |".replace(",", "."))
    baris.append(f"| Imbal hasil tahunan (CAGR) | {_persen(pasar['ret_tahunan'])} |")
    baris.append(f"| Imbal hasil tahun berjalan | {_persen(pasar['ret_ytd'])} |")
    baris.append(f"| Volatilitas tahunan | {_persen(pasar['volatilitas'])} |")
    baris.append(f"| Drawdown terdalam | {_persen(pasar['max_drawdown'])} |")
    baris.append(f"| Posisi sekarang dari puncak | {_persen(pasar['drawdown_sekarang'])} |")
    baris.append(f"| Rentang 52 minggu | {pasar['terendah_52m']:,.0f} - {pasar['tertinggi_52m']:,.0f} |".replace(",", "."))
    baris.append(f"| Hari ditutup naik | {_persen(pasar['hari_naik'])} |")
    baris.append(f"| VaR 95% harian | {_persen(pasar['var95_harian'], 2)} |")
    baris.append("")

    baris.append("## Yang paling menonjol")
    baris.append("")
    for kalimat in analysis.temuan(tabel, pasar):
        baris.append(f"- {kalimat}")
    baris.append("")

    baris.append("## Metrik per saham")
    baris.append("")
    baris.append(
        f"Diurutkan berdasarkan Sharpe. Aset bebas risiko yang dipakai {_persen(rf)} per tahun. "
        "`VaR 95%` adalah kerugian harian yang terlampaui pada 5% hari terburuk."
    )
    baris.append("")
    saji = pd.DataFrame({
        "ticker": tb["ticker"],
        "nama": tb["nama"],
        "ret": tb["ret_tahunan"].map(lambda v: _persen(v)),
        "ret1y": tb["ret_1y"].map(lambda v: _persen(v)),
        "vol": tb["volatilitas"].map(lambda v: _persen(v)),
        "sharpe": tb["sharpe"].map(lambda v: _angka(v)),
        "beta": tb["beta"].map(lambda v: _angka(v)),
        "dd": tb["max_drawdown"].map(lambda v: _persen(v)),
        "var": tb["var95_harian"].map(lambda v: _persen(v, 2)),
        "korelasi": tb["korelasi_ihsg"].map(lambda v: _angka(v)),
    })
    baris.append(_tabel(
        saji,
        ["ticker", "nama", "ret", "ret1y", "vol", "sharpe", "beta", "dd", "var", "korelasi"],
        ["Ticker", "Emiten", "CAGR 5 th", "1 tahun", "Volatilitas", "Sharpe", "Beta",
         "Max drawdown", "VaR 95%", "Korelasi IHSG"],
    ))
    baris.append("")

    baris.append("## Musiman IHSG per bulan")
    baris.append("")
    saji_musim = pd.DataFrame({
        "bulan": musiman["bulan_nama"],
        "rata": musiman["rata_rata"].map(lambda v: _persen(v, 2)),
        "positif": musiman["positif"].map(lambda v: _persen(v, 0)),
        "n": musiman["jumlah_tahun"],
    })
    baris.append(_tabel(saji_musim, ["bulan", "rata", "positif", "n"],
                        ["Bulan", "Rata-rata", "Bulan positif", "Jumlah tahun"]))
    baris.append("")

    baris.append("## Korelasi harian")
    baris.append("")
    baris.append("Korelasi imbal hasil harian antar saham teratas dan IHSG. Nilai 1 berarti bergerak persis sama.")
    baris.append("")
    kepala = "| | " + " | ".join(korelasi.columns) + " |"
    pisah = "|" + "|".join(["---"] * (len(korelasi.columns) + 1)) + "|"
    baris.append(kepala)
    baris.append(pisah)
    for idx, row in korelasi.iterrows():
        isi = " | ".join(_angka(v, 2) if not pd.isna(v) else "-" for v in row)
        baris.append(f"| **{idx}** | {isi} |")
    baris.append("")

    baris.append("## Gambar")
    baris.append("")
    for nama, ket in [
        ("01_risiko_imbal_hasil.png", "sebaran risiko vs imbal hasil"),
        ("02_pertumbuhan_100.png", "pertumbuhan 100 rupiah (skala log)"),
        ("03_drawdown.png", "kurva drawdown IHSG dan dua saham terburuk"),
        ("04_musiman_bulanan.png", "pola musiman bulanan IHSG"),
    ]:
        baris.append(f"![{ket}](figures/{nama})")
        baris.append("")

    baris.append("## Catatan metode")
    baris.append("")
    baris.append(
        "- Harga memakai penutupan yang sudah disesuaikan terhadap aksi korporasi "
        "(`auto_adjust=True` di Yahoo Finance)."
    )
    baris.append(
        "- Imbal hasil tahunan dihitung secara geometrik (CAGR), volatilitas memakai "
        "standar deviasi harian dikali akar 252."
    )
    baris.append(
        f"- Sharpe dan Sortino memakai aset bebas risiko {_persen(rf)} per tahun. Angka ini "
        "adalah asumsi, bukan data yang diunduh, dan bisa diubah lewat opsi `--rf`."
    )
    baris.append(
        "- Universe saham dipilih manual dari emiten likuid, jadi **bukan** seluruh bursa dan "
        "mengandung survivorship bias. Jangan dibaca sebagai rekomendasi investasi."
    )
    baris.append("- Musiman dihitung dari rata-rata imbal hasil bulanan IHSG sepanjang periode data.")
    baris.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(baris), encoding="utf-8")
