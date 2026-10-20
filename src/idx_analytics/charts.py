"""Grafik analitik IDX."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .fetch import BENCHMARK  # noqa: E402

TINTA = "#1c2430"
ABU = "#6b7a8f"
GARIS = "#dfe5ec"
BIRU = "#1d4ed8"
HIJAU = "#15803d"
MERAH = "#b3261e"
AMBER = "#d97706"


def _gaya() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GARIS,
        "axes.labelcolor": TINTA,
        "axes.titlecolor": TINTA,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.color": GARIS,
        "grid.linewidth": 0.7,
        "xtick.color": ABU,
        "ytick.color": ABU,
        "font.size": 9.5,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
    })
    for spine in ("top", "right"):
        plt.rcParams[f"axes.spines.{spine}"] = False


def _simpan(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def risiko_imbal_hasil(tabel: pd.DataFrame, path: Path) -> Path:
    _gaya()
    data = tabel[tabel["ticker"] != "JKSE"].dropna(subset=["volatilitas", "ret_tahunan"])
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    warna = [HIJAU if v > 0 else MERAH for v in data["ret_tahunan"]]
    ax.scatter(data["volatilitas"], data["ret_tahunan"], s=70, c=warna, alpha=0.85,
               edgecolor="white", linewidth=0.8, zorder=3)
    for _, row in data.iterrows():
        ax.annotate(row["ticker"], (row["volatilitas"], row["ret_tahunan"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5, color=ABU)
    ihsg = tabel[tabel["ticker"] == "JKSE"]
    if not ihsg.empty:
        ax.axhline(float(ihsg["ret_tahunan"].iloc[0]), color=ABU, linestyle="--", linewidth=1,
                   label="imbal hasil IHSG")
        ax.axvline(float(ihsg["volatilitas"].iloc[0]), color=GARIS, linestyle=":", linewidth=1)
    ax.axhline(0, color=GARIS, linewidth=1)
    ax.set_xlabel("Volatilitas tahunan")
    ax.set_ylabel("Imbal hasil tahunan")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title("Risiko vs imbal hasil, 5 tahun terakhir")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    return _simpan(fig, path)


def pertumbuhan(harga: pd.DataFrame, tabel: pd.DataFrame, path: Path, n: int = 8) -> Path:
    _gaya()
    pilihan = [t for t in tabel["ticker"] if t != "JKSE"][:n]
    kolom = [f"{t}.JK" for t in pilihan if f"{t}.JK" in harga.columns]
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    for kol in kolom:
        seri = harga[kol].dropna()
        ax.plot(seri.index, seri / seri.iloc[0] * 100, linewidth=1.5,
                label=kol.replace(".JK", ""), alpha=0.9)
    bench = harga[BENCHMARK].dropna()
    ax.plot(bench.index, bench / bench.iloc[0] * 100, color=TINTA, linewidth=2.4, label="IHSG")
    ax.set_title("Pertumbuhan 100 rupiah, saham Sharpe tertinggi")
    ax.set_ylabel("Nilai (mulai 100)")
    ax.legend(frameon=False, fontsize=8, ncol=3)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
    return _simpan(fig, path)


def drawdown(harga: pd.DataFrame, tabel: pd.DataFrame, path: Path) -> Path:
    _gaya()
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    bench = harga[BENCHMARK].dropna()
    dd_bench = bench / bench.cummax() - 1.0
    ax.fill_between(dd_bench.index, dd_bench.to_numpy(), 0, color=TINTA, alpha=0.16)
    ax.plot(dd_bench.index, dd_bench.to_numpy(), color=TINTA, linewidth=1.6, label="IHSG")

    terburuk = tabel.dropna(subset=["max_drawdown"]).sort_values("max_drawdown").head(2)
    for _, row in terburuk.iterrows():
        kol = f"{row['ticker']}.JK"
        if kol not in harga.columns:
            continue
        seri = harga[kol].dropna()
        kurva = seri / seri.cummax() - 1.0
        ax.plot(kurva.index, kurva.to_numpy(), linewidth=1.2, alpha=0.85,
                label=f"{row['ticker']} ({row['max_drawdown']:.0%})")
    ax.set_title("Drawdown: seberapa jauh dari puncak")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    return _simpan(fig, path)


def musiman(tabel_musiman: pd.DataFrame, path: Path) -> Path:
    _gaya()
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    warna = [HIJAU if v > 0 else MERAH for v in tabel_musiman["rata_rata"]]
    ax.bar(tabel_musiman["bulan_nama"], tabel_musiman["rata_rata"], color=warna, width=0.66)
    for i, row in tabel_musiman.reset_index().iterrows():
        offset = 0.002 if row["rata_rata"] > 0 else -0.002
        ax.text(i, row["rata_rata"] + offset, f"{row['positif']:.0%}", ha="center",
                va="bottom" if row["rata_rata"] > 0 else "top", fontsize=7.5, color=ABU)
    ax.axhline(0, color=GARIS, linewidth=1)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1%}")
    ax.set_title("Rata-rata imbal hasil IHSG per bulan")
    ax.set_ylabel("Imbal hasil bulanan")
    ax.set_xlabel("Angka kecil di atas batang = porsi bulan yang ditutup positif")
    return _simpan(fig, path)


def buat_semua(harga: pd.DataFrame, tabel: pd.DataFrame, tabel_musiman: pd.DataFrame,
               outdir: Path) -> list[Path]:
    return [
        risiko_imbal_hasil(tabel, outdir / "01_risiko_imbal_hasil.png"),
        pertumbuhan(harga, tabel, outdir / "02_pertumbuhan_100.png"),
        drawdown(harga, tabel, outdir / "03_drawdown.png"),
        musiman(tabel_musiman, outdir / "04_musiman_bulanan.png"),
    ]
