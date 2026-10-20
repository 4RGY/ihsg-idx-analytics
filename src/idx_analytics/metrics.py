"""Metrik risiko dan imbal hasil. Semua fungsi murni, tidak menyentuh jaringan."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

HARI_BURSA = 252


def imbal_hasil_harian(harga: pd.Series) -> pd.Series:
    return harga.pct_change().dropna()


def imbal_hasil_tahunan(returns: pd.Series) -> float:
    """CAGR dari rata-rata geometrik harian."""
    bersih = returns.dropna()
    if bersih.empty:
        return float("nan")
    faktor = (1.0 + bersih).prod()
    if faktor <= 0:
        return float("nan")
    return float(faktor ** (HARI_BURSA / len(bersih)) - 1.0)


def volatilitas_tahunan(returns: pd.Series) -> float:
    bersih = returns.dropna()
    if len(bersih) < 2:
        return float("nan")
    return float(bersih.std(ddof=1) * math.sqrt(HARI_BURSA))


def sharpe(returns: pd.Series, rf_tahunan: float = 0.0) -> float:
    vol = volatilitas_tahunan(returns)
    if not np.isfinite(vol) or vol == 0:
        return float("nan")
    return float((imbal_hasil_tahunan(returns) - rf_tahunan) / vol)


def downside_deviation(returns: pd.Series) -> float:
    bersih = returns.dropna()
    negatif = bersih[bersih < 0]
    if negatif.empty:
        return 0.0
    return float(math.sqrt((negatif ** 2).mean()) * math.sqrt(HARI_BURSA))


def sortino(returns: pd.Series, rf_tahunan: float = 0.0) -> float:
    dd = downside_deviation(returns)
    if dd == 0:
        return float("nan")
    return float((imbal_hasil_tahunan(returns) - rf_tahunan) / dd)


def kurva_ekuitas(returns: pd.Series) -> pd.Series:
    bersih = returns.dropna()
    return (1.0 + bersih).cumprod()


def max_drawdown(returns: pd.Series) -> float:
    """Drawdown terdalam, dikembalikan sebagai angka negatif (mis. -0.35)."""
    ekuitas = kurva_ekuitas(returns)
    if ekuitas.empty:
        return float("nan")
    puncak = ekuitas.cummax()
    return float((ekuitas / puncak - 1.0).min())


def kurva_drawdown(harga: pd.Series) -> pd.Series:
    return harga / harga.cummax() - 1.0


def beta(returns: pd.Series, benchmark: pd.Series) -> float:
    gabung = pd.concat([returns, benchmark], axis=1, keys=["aset", "bench"]).dropna()
    if len(gabung) < 3:
        return float("nan")
    varian = gabung["bench"].var(ddof=1)
    if varian == 0:
        return float("nan")
    return float(gabung["aset"].cov(gabung["bench"]) / varian)


def var_historis(returns: pd.Series, level: float = 0.95) -> float:
    """Value at Risk harian historis, dikembalikan sebagai kerugian positif."""
    bersih = returns.dropna()
    if bersih.empty:
        return float("nan")
    return float(-np.percentile(bersih, (1 - level) * 100))


def calmar(returns: pd.Series) -> float:
    dd = max_drawdown(returns)
    if not np.isfinite(dd) or dd == 0:
        return float("nan")
    return float(imbal_hasil_tahunan(returns) / abs(dd))


def hari_terbaik_terburuk(returns: pd.Series) -> tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]:
    bersih = returns.dropna()
    return (bersih.idxmax(), float(bersih.max())), (bersih.idxmin(), float(bersih.min()))


def musiman_bulanan(returns: pd.Series) -> pd.DataFrame:
    """Rata-rata imbal hasil per bulan kalender dan persentase bulan positif."""
    bersih = returns.dropna()
    if bersih.empty:
        return pd.DataFrame(columns=["bulan", "rata_rata", "positif", "jumlah_tahun"])
    bulanan = (1.0 + bersih).resample("ME").prod() - 1.0
    tabel = pd.DataFrame({"bulan": bulanan.index.month, "ret": bulanan.to_numpy()})
    hasil = tabel.groupby("bulan").agg(
        rata_rata=("ret", "mean"),
        positif=("ret", lambda s: float((s > 0).mean())),
        jumlah_tahun=("ret", "size"),
    )
    return hasil.reset_index()
