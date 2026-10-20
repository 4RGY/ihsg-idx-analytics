"""Perhitungan tabel metrik dan ringkasan pasar."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import metrics
from .fetch import BENCHMARK, UNIVERSE

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tabel_metrik(harga: pd.DataFrame, rf: float = 0.0575) -> pd.DataFrame:
    if BENCHMARK not in harga.columns:
        raise ValueError(f"benchmark {BENCHMARK} tidak ada di data")

    bench_ret = metrics.imbal_hasil_harian(harga[BENCHMARK])
    baris = []
    for ticker in harga.columns:
        seri = harga[ticker].dropna()
        if len(seri) < 60:
            continue
        ret = metrics.imbal_hasil_harian(seri)
        setahun = ret.tail(metrics.HARI_BURSA)
        baris.append({
            "ticker": ticker.replace(".JK", "").lstrip("^"),
            "nama": UNIVERSE.get(ticker, ticker),
            "harga_akhir": float(seri.iloc[-1]),
            "ret_tahunan": metrics.imbal_hasil_tahunan(ret),
            "ret_1y": float((1.0 + setahun).prod() - 1.0),
            "volatilitas": metrics.volatilitas_tahunan(ret),
            "sharpe": metrics.sharpe(ret, rf),
            "sortino": metrics.sortino(ret, rf),
            "beta": metrics.beta(ret, bench_ret),
            "max_drawdown": metrics.max_drawdown(ret),
            "var95_harian": metrics.var_historis(ret),
            "calmar": metrics.calmar(ret),
            "korelasi_ihsg": float(ret.corr(bench_ret)),
            "observasi": int(len(ret)),
        })
    tabel = pd.DataFrame(baris)
    return tabel.sort_values("sharpe", ascending=False).reset_index(drop=True)


def ringkasan_pasar(harga: pd.DataFrame) -> dict[str, Any]:
    seri = harga[BENCHMARK].dropna()
    ret = metrics.imbal_hasil_harian(seri)
    ekuitas = metrics.kurva_ekuitas(ret)
    (tgl_baik, nilai_baik), (tgl_buruk, nilai_buruk) = metrics.hari_terbaik_terburuk(ret)
    setahun = seri.tail(metrics.HARI_BURSA)
    awal_tahun = seri[seri.index.year == seri.index[-1].year]
    return {
        "level_terakhir": float(seri.iloc[-1]),
        "tanggal_terakhir": seri.index[-1],
        "tanggal_mulai": seri.index[0],
        "hari_observasi": int(len(seri)),
        "ret_tahunan": metrics.imbal_hasil_tahunan(ret),
        "volatilitas": metrics.volatilitas_tahunan(ret),
        "max_drawdown": metrics.max_drawdown(ret),
        "drawdown_sekarang": float(metrics.kurva_drawdown(seri).iloc[-1]),
        "hari_terbaik": (tgl_baik, nilai_baik),
        "hari_terburuk": (tgl_buruk, nilai_buruk),
        "tertinggi_52m": float(setahun.max()),
        "terendah_52m": float(setahun.min()),
        "ret_ytd": float(seri.iloc[-1] / awal_tahun.iloc[0] - 1.0) if len(awal_tahun) > 1 else float("nan"),
        "ekuitas_akhir": float(ekuitas.iloc[-1]),
        "var95_harian": metrics.var_historis(ret),
        "hari_naik": float((ret > 0).mean()),
    }


def korelasi(harga: pd.DataFrame, n: int = 12, berdasarkan: pd.DataFrame | None = None) -> pd.DataFrame:
    """Matriks korelasi harian untuk n saham teratas (default: Sharpe tertinggi)."""
    kolom = list(harga.columns)
    if berdasarkan is not None and not berdasarkan.empty:
        pilihan = [t for t in berdasarkan["ticker"].head(n)]
        kolom = [c for c in harga.columns if c.replace(".JK", "") in pilihan]
        if BENCHMARK not in kolom:
            kolom.append(BENCHMARK)
    ret = harga[kolom].pct_change().dropna()
    matriks = ret.corr()
    matriks.index = [i.replace(".JK", "").replace("^", "") for i in matriks.index]
    matriks.columns = [c.replace(".JK", "").replace("^", "") for c in matriks.columns]
    return matriks


def musiman(harga: pd.DataFrame) -> pd.DataFrame:
    ret = metrics.imbal_hasil_harian(harga[BENCHMARK].dropna())
    tabel = metrics.musiman_bulanan(ret)
    tabel["bulan_nama"] = tabel["bulan"].map(lambda m: BULAN[int(m) - 1])
    return tabel


def temuan(tabel: pd.DataFrame, pasar: dict[str, Any]) -> list[str]:
    """Kalimat insight yang seluruhnya dihitung dari data, bukan opini."""
    hasil: list[str] = []
    saham = tabel[tabel["ticker"] != "JKSE"]
    if saham.empty:
        return hasil

    teratas = saham.iloc[0]
    hasil.append(
        f"Sharpe tertinggi: **{teratas['ticker']}** ({teratas['nama']}), "
        f"{teratas['sharpe']:.2f} dengan imbal hasil tahunan {teratas['ret_tahunan']:.1%} "
        f"dan volatilitas {teratas['volatilitas']:.1%}."
    )

    beta_tertinggi = saham.loc[saham["beta"].idxmax()]
    hasil.append(
        f"Paling sensitif ke IHSG: **{beta_tertinggi['ticker']}** (beta {beta_tertinggi['beta']:.2f}). "
        f"Artinya pergerakan IHSG 1% cenderung diikuti {beta_tertinggi['beta']:.1f}%."
    )

    paling_aman = saham.loc[saham["max_drawdown"].idxmax()]
    hasil.append(
        f"Drawdown terdalam paling ringan: **{paling_aman['ticker']}** "
        f"({paling_aman['max_drawdown']:.1%})."
    )

    negatif = int((saham["sharpe"] < 0).sum())
    hasil.append(
        f"{negatif} dari {len(saham)} saham punya Sharpe negatif pada periode ini, "
        f"artinya imbal hasilnya masih di bawah aset bebas risiko."
    )

    hasil.append(
        f"IHSG sendiri: {pasar['ret_tahunan']:.1%} per tahun dengan volatilitas "
        f"{pasar['volatilitas']:.1%} dan drawdown terdalam {pasar['max_drawdown']:.1%}."
    )
    hasil.append(
        f"Dalam {pasar['hari_observasi']} hari bursa, {pasar['hari_naik']:.1%} hari ditutup naik. "
        f"Hari terburuk {pasar['hari_terburuk'][0]:%d %b %Y} ({pasar['hari_terburuk'][1]:.2%}), "
        f"hari terbaik {pasar['hari_terbaik'][0]:%d %b %Y} ({pasar['hari_terbaik'][1]:.2%})."
    )
    return hasil
